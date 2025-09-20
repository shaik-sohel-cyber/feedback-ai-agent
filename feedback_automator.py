import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def run_feedback_automation(username, password):
    """
    Runs the GRIET feedback automation and yields log messages for the web UI.
    """
    CONFIG = {
        "LOGIN_URL": "http://webprosindia.com/Gokaraju/",
        "TERM_VALUE_TO_SELECT": "1",
        "SUBMIT_FORM": False,
        "SELECTORS": {
            "username_field_id": "txtId2",
            "password_field_id": "txtPwd2",
            "login_button_id": "imgBtn2",
            "feedback_link_text": "FEEDBACK",
            "iframe_name": "capIframe",
            "term_dropdown_id": "ctl00_CapPlaceHolder_ddlExams",
            "question_rows_xpath": "//table[contains(@id, 'gvStudentFeedback')]//tr[.//input[@type='radio']]",
            "submit_button_id": "ContentPlaceHolder1_btnSubmit"
        },
        "RATINGS": { "default": 4 }
    }

    # Headless mode can be enabled for faster, non-visual execution.
    # To run without seeing the browser, uncomment the next line.
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") 
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    
    try:
        # Automatically downloads and manages the correct chromedriver for your installed Chrome version.
        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            wait = WebDriverWait(driver, 20)
            
            yield "Navigating to login page...\n"
            driver.get(CONFIG['LOGIN_URL'])
            
            wait.until(EC.presence_of_element_located((By.ID, CONFIG['SELECTORS']['username_field_id']))).send_keys(username)
            driver.find_element(By.ID, CONFIG['SELECTORS']['password_field_id']).send_keys(password)
            driver.find_element(By.ID, CONFIG['SELECTORS']['login_button_id']).click()
            yield "Login submitted. Waiting for dashboard...\n"

            feedback_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, CONFIG['SELECTORS']['feedback_link_text'])))
            yield "On dashboard. Clicking 'FEEDBACK' link...\n"
            feedback_link.click()

            yield "Switching to the feedback iframe...\n"
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, CONFIG['SELECTORS']['iframe_name'])))

            yield "Checking for active feedback sessions...\n"
            term_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, CONFIG['SELECTORS']['term_dropdown_id']))))
            
            # Check for any selectable terms other than the default "--Select Term--"
            valid_options = [opt for opt in term_dropdown.options if opt.get_attribute('value') and opt.get_attribute('value') != '0']
            if not valid_options:
                yield "🟡 No active feedback sessions found. Exiting.\n"
                return

            available_values = [opt.get_attribute('value') for opt in valid_options]
            yield f"✅ Active session(s) found. Available terms: {available_values}\n"

            term_to_select = CONFIG['TERM_VALUE_TO_SELECT']
            if term_to_select in available_values:
                yield f"Selecting configured term: '{term_to_select}'\n"
                term_dropdown.select_by_value(term_to_select)
            else:
                yield f"❌ Error: Your configured term '{term_to_select}' is not available.\n"
                return

            yield "Waiting for questions to appear...\n"
            wait.until(EC.presence_of_element_located((By.XPATH, CONFIG['SELECTORS']['question_rows_xpath'])))
            question_rows = driver.find_elements(By.XPATH, CONFIG['SELECTORS']['question_rows_xpath'])
            yield f"Found {len(question_rows)} questions. Filling feedback...\n"

            for i, row in enumerate(question_rows, 1):
                rating_value = CONFIG['RATINGS']['default']
                radio_button = row.find_element(By.XPATH, f".//input[@type='radio' and @value='{rating_value}']")
                driver.execute_script("arguments[0].click();", radio_button)
                yield f"  - Question {i}: Answered with rating '{rating_value}'\n"
                time.sleep(0.05) # Small delay to mimic human behavior

            yield "\nAll questions have been filled.\n"
            if CONFIG.get("SUBMIT_FORM", False):
                yield "Attempting to submit form...\n"
                driver.find_element(By.ID, CONFIG['SELECTORS']['submit_button_id']).click()
                yield "✅ FORM SUBMITTED SUCCESSFULLY!\n"
            else:
                yield "👍 Feedback filled. Submission is disabled in config.\n"
            
            time.sleep(3) # Keep browser open for final review

    except TimeoutException:
        yield "\n❌ A timeout occurred. The login may have failed or an element took too long to appear.\n"
    except Exception as e:
        yield f"\n❌ An unexpected error occurred: {e}\n"


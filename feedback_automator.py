import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def run_feedback_automation(username, password):
    """
    Runs the GRIET feedback automation in a Docker environment where Chrome is pre-installed.
    """
    
    # --- Configure Chrome for Headless Operation on a Server ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    
    # --- NEW ARGUMENTS TO FIX THE CRASH ---
    # Tells Chrome not to try using a GPU, which doesn't exist on the server.
    chrome_options.add_argument("--disable-gpu")
    # Tells Chrome to use a temporary folder for its user data, fixing the "directory in use" error.
    chrome_options.add_argument("--user-data-dir=/tmp/user-data")
    chrome_options.add_argument("--remote-debugging-port=9222")


    # --- Configuration ---
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

    with webdriver.Chrome(options=chrome_options) as driver:
        wait = WebDriverWait(driver, 25)
        
        try:
            yield "Initializing automation...\n"
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
            
            valid_options = [opt for opt in term_dropdown.options if opt.get_attribute('value') and opt.get_attribute('value') != '0']

            if not valid_options:
                yield "🟡 No active feedback sessions found. Exiting."
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
                time.sleep(0.05)

            yield "\nAll questions have been filled.\n"
            if CONFIG.get("SUBMIT_FORM", False):
                yield "Attempting to submit form...\n"
                driver.find_element(By.ID, CONFIG['SELECTORS']['submit_button_id']).click()
                yield "✅ FORM SUBMITTED SUCCESSFULLY!\n"
            else:
                yield "👍 Feedback filled. Submission is disabled in config.\n"
            
            yield "Automation finished successfully."
            time.sleep(2)

        except TimeoutException as e:
            yield f"\n❌ A timeout occurred. The page took too long to load an element.\nError details: {e}"
        except Exception as e:
            yield f"\n❌ An unexpected error occurred: {e}"


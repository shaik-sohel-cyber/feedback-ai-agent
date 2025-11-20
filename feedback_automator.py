import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

def run_feedback_automation(username, password):
    CONFIG = {
        "LOGIN_URL": "http://webprosindia.com/Gokaraju/",
        "TERM_VALUE_TO_SELECT": "1",
        "SUBMIT_FORM": True,
        "SELECTORS": {
            "username_field_id": "txtId2",
            "password_field_id": "txtPwd2",
            "login_button_id": "imgBtn2",
            "feedback_link_text": "FEEDBACK",
            "iframe_name": "capIframe",
            "term_dropdown_id": "ctl00_CapPlaceHolder_ddlExams",
        },
        "FILL_VALUE": "4",
        "WAIT_LONG": 20,
        "WAIT_SHORT": 1,
    }

    options = webdriver.ChromeOptions()
    # --- CRITICAL FOR DEPLOYMENT & UX ---
    options.add_argument("--headless=new") # Run invisible (no popup window)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # ------------------------------------

    driver = None
    try:
        # Auto-install matching chrome version
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, CONFIG["WAIT_LONG"])

        yield "PROGRESS:10:Navigating to login page..."
        driver.get(CONFIG["LOGIN_URL"])

        # --- Login ---
        wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["username_field_id"]))).send_keys(username)
        driver.find_element(By.ID, CONFIG["SELECTORS"]["password_field_id"]).send_keys(password)
        driver.find_element(By.ID, CONFIG["SELECTORS"]["login_button_id"]).click()
        yield "PROGRESS:20:Login submitted. Accessing dashboard..."

        # --- Click FEEDBACK link ---
        feedback_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, CONFIG["SELECTORS"]["feedback_link_text"])))
        feedback_link.click()

        # --- Switch to iframe ---
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, CONFIG["SELECTORS"]["iframe_name"])))
        yield "PROGRESS:30:Found Feedback Frame..."

        # --- Term selection ---
        dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["term_dropdown_id"])))
        try:
            driver.execute_script("arguments[0].click();", dropdown_elem)
        except Exception:
            pass
        time.sleep(0.6)

        term_dropdown = Select(driver.find_element(By.ID, CONFIG["SELECTORS"]["term_dropdown_id"]))
        valid_options = [opt for opt in term_dropdown.options if opt.get_attribute('value') and opt.get_attribute('value') != '0']
        
        if not valid_options:
            yield "ERROR:No active feedback sessions found."
            return

        # Select term
        term_to_select = CONFIG["TERM_VALUE_TO_SELECT"]
        available_values = [opt.get_attribute('value') for opt in valid_options]
        
        if term_to_select in available_values:
            term_dropdown.select_by_value(term_to_select)
        else:
            term_dropdown.select_by_value(valid_options[0].get_attribute('value'))
        
        yield "PROGRESS:40:Term selected. Loading grid..."
        time.sleep(CONFIG["WAIT_SHORT"])

        # --- Filling ---
        fill_val = str(CONFIG["FILL_VALUE"])
        candidates = driver.find_elements(By.XPATH, "//input[@type='text' and (@maxlength='1' or contains(@style,'width') or contains(@style,'px'))]")
        
        if not candidates:
            candidates = driver.find_elements(By.XPATH, "//input[@type='text']")

        total_boxes = len(candidates)
        yield f"PROGRESS:50:Found {total_boxes} rating boxes. Filling now..."

        filled = 0
        for idx, el in enumerate(candidates, start=1):
            try:
                if not el.is_displayed() or not el.is_enabled():
                    continue
                driver.execute_script(
                    "const el = arguments[0]; const val = arguments[1]; el.focus(); el.value = val; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); el.blur();",
                    el, fill_val
                )
                filled += 1
                # Calculate progress between 50% and 90%
                current_progress = 50 + int((filled / total_boxes) * 40)
                yield f"PROGRESS:{current_progress}:Filled box {filled}/{total_boxes}"
            except:
                pass

        yield "PROGRESS:90:Submitting form..."
        time.sleep(0.1)

        # --- Submit ---
        if CONFIG["SUBMIT_FORM"]:
            try:
                submit_btn = driver.find_element(By.ID, "btnfbsave")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", submit_btn)
                
                # Handle Alert
                try:
                    WebDriverWait(driver, 5).until(EC.alert_is_present()).accept()
                except:
                    pass
            except:
                # Fallback
                driver.execute_script("if(typeof _onSaveClick === 'function'){ _onSaveClick(); }")
                try:
                    WebDriverWait(driver, 5).until(EC.alert_is_present()).accept()
                except:
                    pass

        yield "PROGRESS:100:Automation Complete!"
        time.sleep(2.0)

    except Exception as e:
        yield f"ERROR:{str(e)}"
    finally:
        if driver:
            driver.quit()
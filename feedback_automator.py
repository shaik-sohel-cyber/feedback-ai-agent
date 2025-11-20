import time
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
        "WAIT_LONG": 30,  # Increased for slow servers
        "WAIT_SHORT": 1,
    }

    # --- BROWSER CONFIGURATION ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    # Fake a real user agent to avoid detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        # --- SMART DRIVER & BINARY SELECTION ---
        # This block fixes the "Message:" error by finding the correct files on Linux
        
        system_chromium_path = "/usr/bin/chromium"
        system_driver_path = "/usr/bin/chromedriver"
        
        if os.path.exists(system_chromium_path) and os.path.exists(system_driver_path):
            # SERVER MODE (Render/Linux)
            yield "PROGRESS:5:Detected Linux Server Environment..."
            options.binary_location = system_chromium_path  # <--- CRITICAL FIX
            service = Service(executable_path=system_driver_path)
        else:
            # LOCAL MODE (Windows/Mac)
            yield "PROGRESS:5:Detected Local Environment..."
            # No binary_location needed, Selenium finds it automatically on Windows
            service = Service(ChromeDriverManager().install())
        
        # ---------------------------------------

        yield "PROGRESS:8:Starting Browser..."
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, CONFIG["WAIT_LONG"])

        yield "PROGRESS:10:Navigating to login page..."
        driver.get(CONFIG["LOGIN_URL"])

        # --- Login ---
        yield "PROGRESS:15:Entering credentials..."
        wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["username_field_id"]))).send_keys(username)
        driver.find_element(By.ID, CONFIG["SELECTORS"]["password_field_id"]).send_keys(password)
        driver.find_element(By.ID, CONFIG["SELECTORS"]["login_button_id"]).click()
        yield "PROGRESS:25:Login submitted..."

        # --- Click FEEDBACK link ---
        feedback_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, CONFIG["SELECTORS"]["feedback_link_text"])))
        feedback_link.click()

        # --- Switch to iframe ---
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, CONFIG["SELECTORS"]["iframe_name"])))
        yield "PROGRESS:35:Found Feedback Frame..."

        # --- Term selection ---
        dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["term_dropdown_id"])))
        try:
            driver.execute_script("arguments[0].click();", dropdown_elem)
        except:
            pass
        time.sleep(1.0)

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
        
        yield "PROGRESS:45:Term selected. Loading grid..."
        time.sleep(CONFIG["WAIT_SHORT"])

        # --- Filling ---
        fill_val = str(CONFIG["FILL_VALUE"])
        candidates = driver.find_elements(By.XPATH, "//input[@type='text' and (@maxlength='1' or contains(@style,'width') or contains(@style,'px'))]")
        
        if not candidates:
            candidates = driver.find_elements(By.XPATH, "//input[@type='text']")

        total_boxes = len(candidates)
        yield f"PROGRESS:50:Found {total_boxes} rating boxes. Filling..."

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
                current_progress = 50 + int((filled / total_boxes) * 40)
                if idx % 5 == 0: 
                    yield f"PROGRESS:{current_progress}:Filled box {filled}/{total_boxes}"
            except:
                pass

        yield "PROGRESS:90:Submitting form..."
        time.sleep(1.5)

        # --- AGGRESSIVE SUBMIT LOGIC ---
        if CONFIG["SUBMIT_FORM"]:
            submission_success = False
            yield "PROGRESS:92:Attempting JS Click..."
            try:
                driver.execute_script("document.getElementById('btnfbsave').click();")
                WebDriverWait(driver, 8).until(EC.alert_is_present()).accept()
                submission_success = True
                yield "PROGRESS:95:✅ Submitted via JS Force"
            except Exception as e:
                yield f"PROGRESS:93:JS Click failed. Trying standard click..."
                try:
                    submit_btn = driver.find_element(By.ID, "btnfbsave")
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
                    submit_btn.click()
                    WebDriverWait(driver, 8).until(EC.alert_is_present()).accept()
                    submission_success = True
                    yield "PROGRESS:95:✅ Submitted via Standard Click"
                except Exception as e2:
                    pass

            if not submission_success:
                 yield "ERROR:Could not submit. Popup never appeared."
                 return

        yield "PROGRESS:100:Automation Complete!"
        time.sleep(2.0)

    except Exception as e:
        # Expanded Error Logging to see the REAL issue
        full_error = traceback.format_exc()
        error_msg = str(e)
        if not error_msg: 
            error_msg = "Unknown Driver Error (Chrome likely crashed)"
        yield f"ERROR:Critical Error: {error_msg}"
        # Print to server logs for debugging
        print(f"--- FULL ERROR TRACEBACK ---\n{full_error}\n-----------------------------")
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
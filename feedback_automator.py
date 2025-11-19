import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException


def run_feedback_automation(username, password):
    """
    Full automation for the GRIET feedback form where rating cells are short text inputs.

    Behavior:
    - navigates to login page and logs in
    - clicks FEEDBACK and switches to the feedback iframe
    - selects a term (prefers CONFIG['TERM_VALUE_TO_SELECT'], else picks first available)
    - finds short text inputs (maxlength=1 or small width) and fills them with CONFIG['FILL_VALUE'] (dispatches input/change events)
    - clicks the submit button (prefers #btnfbsave), falls back to calling the page function `_onSaveClick()` if needed
    - accepts the JavaScript confirmation dialog that appears after submission

    Yields log strings to be streamed to the UI.
    """

    CONFIG = {
        "LOGIN_URL": "http://webprosindia.com/Gokaraju/",
        "TERM_VALUE_TO_SELECT": "1",
        "SUBMIT_FORM": True,           # Set to False to test without actually submitting
        "SELECTORS": {
            "username_field_id": "txtId2",
            "password_field_id": "txtPwd2",
            "login_button_id": "imgBtn2",
            "feedback_link_text": "FEEDBACK",
            "iframe_name": "capIframe",
            "term_dropdown_id": "ctl00_CapPlaceHolder_ddlExams",
        },
        "FILL_VALUE": "4",
        # Wait timeouts (seconds)
        "WAIT_LONG": 20,
        "WAIT_SHORT": 1,
    }

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # uncomment to run headless
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")

    try:
        service = Service(ChromeDriverManager().install())
        with webdriver.Chrome(service=service, options=options) as driver:
            wait = WebDriverWait(driver, CONFIG["WAIT_LONG"])

            yield "Navigating to login page...\n"
            driver.get(CONFIG["LOGIN_URL"])

            # --- Login ---
            wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["username_field_id"]))).send_keys(username)
            driver.find_element(By.ID, CONFIG["SELECTORS"]["password_field_id"]).send_keys(password)
            driver.find_element(By.ID, CONFIG["SELECTORS"]["login_button_id"]).click()
            yield "Login submitted. Waiting for dashboard...\n"

            # --- Click FEEDBACK link ---
            feedback_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, CONFIG["SELECTORS"]["feedback_link_text"])))
            yield "On dashboard. Clicking 'FEEDBACK' link...\n"
            feedback_link.click()

            # --- Switch to iframe ---
            yield "Switching to the feedback iframe...\n"
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, CONFIG["SELECTORS"]["iframe_name"])))

            # --- Term selection (robust) ---
            yield "Checking for active feedback sessions...\n"
            dropdown_elem = wait.until(EC.presence_of_element_located((By.ID, CONFIG["SELECTORS"]["term_dropdown_id"])))
            try:
                driver.execute_script("arguments[0].click();", dropdown_elem)
            except Exception:
                pass
            time.sleep(0.6)

            try:
                term_dropdown = Select(driver.find_element(By.ID, CONFIG["SELECTORS"]["term_dropdown_id"]))
            except Exception as e:
                yield f"❌ Could not locate term dropdown after clicking: {e}\n"
                return

            valid_options = [opt for opt in term_dropdown.options if opt.get_attribute('value') and opt.get_attribute('value') != '0']
            if not valid_options:
                yield "🟡 No active feedback sessions found. Exiting.\n"
                return

            available_values = [opt.get_attribute('value') for opt in valid_options]
            available_texts = [opt.text.strip() for opt in valid_options]
            yield f"✅ Active session(s) found. Available terms (values): {available_values} (labels: {available_texts})\n"

            term_to_select = CONFIG["TERM_VALUE_TO_SELECT"]
            if term_to_select in available_values:
                yield f"Selecting configured term: '{term_to_select}'\n"
                term_dropdown.select_by_value(term_to_select)
            else:
                chosen_option = valid_options[0]
                chosen_value = chosen_option.get_attribute('value')
                chosen_label = chosen_option.text.strip()
                yield f"⚠️ Configured term '{term_to_select}' not available. Auto-selecting first available term: value='{chosen_value}', label='{chosen_label}'\n"
                term_dropdown.select_by_value(chosen_value)

            # --- Wait for grid to render ---
            yield "Waiting for the feedback grid to render...\n"
            time.sleep(CONFIG["WAIT_SHORT"])  # allow dynamic content to load

            fill_val = str(CONFIG["FILL_VALUE"])

            # --- Find short text inputs (heuristic) ---
            # Prefer inputs with maxlength=1 or small inline width. Broad but effective.
            candidates = driver.find_elements(By.XPATH, "//input[@type='text' and (@maxlength='1' or contains(@style,'width') or contains(@style,'px'))]")

            if not candidates:
                yield "No short text inputs found with heuristic selector — falling back to all input[type='text'].\n"
                candidates = driver.find_elements(By.XPATH, "//input[@type='text']")

            yield f"Total feedback text boxes found: {len(candidates)}\n"

            filled = 0
            for idx, el in enumerate(candidates, start=1):
                try:
                    if not el.is_displayed() or not el.is_enabled():
                        continue

                    # Set value via JS and dispatch input/change events so front-end handlers run
                    driver.execute_script(
                        "const el = arguments[0]; const val = arguments[1]; el.focus(); el.value = val; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); el.blur();",
                        el, fill_val
                    )

                    filled += 1
                    yield f"  - Filled box #{idx} with '{fill_val}'.\n"
                    time.sleep(0.01)
                except StaleElementReferenceException:
                    yield f"  - Skipped stale element #{idx}.\n"
                except Exception as e:
                    yield f"  - Warning: could not fill box #{idx}: {e}\n"

            yield f"Completed filling. Total boxes filled: {filled}\n"

            # small wait for any front-end validation or enabling of submit
            time.sleep(0.1)

            # --- Submit handling ---
            if not CONFIG.get("SUBMIT_FORM", False):
                yield "SUBMIT_FORM is False — submission skipped by config.\n"
            else:
                yield "Attempting to click the Submit button (id='btnfbsave')...\n"
                try:
                    submit_btn = driver.find_element(By.ID, "btnfbsave")
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", submit_btn)
                    yield "✅ Submit button clicked successfully.\n"

                    # Handle confirmation popup (Yes/No confirm)
                    yield "Waiting for confirmation popup...\n"
                    try:
                        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                        alert_text = alert.text if hasattr(alert, 'text') else ''
                        alert.accept()
                        yield f"✅ Confirmation popup accepted (text: '{alert_text}').\n"
                    except Exception as e_alert:
                        yield f"⚠️ No confirmation popup appeared or failed to accept: {e_alert}\n"

                except Exception as e_btn:
                    yield f"❌ Could not click '#btnfbsave' directly: {e_btn}\nTrying fallback: call page function _onSaveClick() via JS...\n"
                    try:
                        # Call the page's JS save function if present
                        driver.execute_script("if(typeof _onSaveClick === 'function'){ _onSaveClick(); } else if (typeof onSaveClick === 'function') { onSaveClick(); }")
                        yield "✅ Fallback: attempted to call page save function (JS invocation).\n"

                        # Handle confirmation popup after fallback call
                        yield "Waiting for confirmation popup (fallback)...\n"
                        try:
                            alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                            alert_text = alert.text if hasattr(alert, 'text') else ''
                            alert.accept()
                            yield f"✅ Confirmation popup accepted after fallback (text: '{alert_text}').\n"
                        except Exception as e_alert2:
                            yield f"⚠️ No confirmation popup after fallback or failed to accept: {e_alert2}\n"

                    except Exception as e_fn:
                        yield f"❌ Fallback save call failed: {e_fn}\nPlease inspect the page to find the proper submit handler or selector.\n"

            # keep browser open briefly for review (short)
            time.sleep(3.0)

    except TimeoutException:
        yield "\n❌ A timeout occurred. The login may have failed or an element took too long to appear.\n"
    except Exception as e:
        yield f"\n❌ An unexpected error occurred: {e}\n"
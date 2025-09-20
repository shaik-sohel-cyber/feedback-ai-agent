import time
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ========================== 1. CONFIGURATION =================================
# VVVV --- UPDATE YOUR DETAILS HERE --- VVVV

# Optional: Load credentials from a .env file for better security
load_dotenv()

CONFIG = {
    # --- Login & Navigation ---
    "LOGIN_URL": "http://webprosindia.com/Gokaraju/",
    
    # --- User Credentials (Update here or in a .env file) ---
    "CREDENTIALS": {
        "username": os.getenv("GRIET_USER", "23241a12c0"),  # e.g., 23241a12c0
        "password": os.getenv("GRIET_PASS", "02082003")      # Your password
    },

    # --- Feedback Settings ---
    "TERM_VALUE_TO_SELECT": "1",  # The term you want to select (e.g., "1" or "2")
    "SUBMIT_FORM": False,         # Set to True to automatically submit the form

    # --- HTML Element Selectors (IDs, Names, etc.) ---
    "SELECTORS": {
        # Login Page
        "username_field_id": "txtId2",
        "password_field_id": "txtPwd2",
        "login_button_id": "imgBtn2",
        
        # Dashboard
        "feedback_link_text": "FEEDBACK",

        # Feedback Page (inside the iframe)
        "iframe_name": "capIframe",
        "term_dropdown_id": "ctl00_CapPlaceHolder_ddlExams",
        "question_rows_xpath": "//table[contains(@id, 'gvStudentFeedback')]//tr[.//input[@type='radio']]",
        "submit_button_id": "ContentPlaceHolder1_btnSubmit"
    },
    
    # --- Rating Logic ---
    "RATINGS": {
        "default": 4, # 4 = Excellent, 3 = Good, 2 = Average, 1 = Poor
    }
}

# ^^^^ --- UPDATE YOUR DETAILS HERE --- ^^^^
# ==============================================================================


# ========================== 2. LOGIC ENGINE ===================================

def decide_rating(question_text: str, config: dict) -> int:
    """
    Determines the rating for a given question.
    For now, it returns the default rating from the CONFIG.
    """
    return config['RATINGS']['default']

# ==============================================================================


# ======================== 3. WEB AUTOMATION SCRIPT ============================

def main():
    """
    Main function to run the GRIET feedback automation.
    """
    print("🚀 Starting GRIET Feedback Automation Agent...")
    
    with webdriver.Chrome(service=Service()) as driver:
        wait = WebDriverWait(driver, 20)

        try:
            # --- STEP 1: LOGIN ---
            print("Navigating to login page...")
            driver.get(CONFIG['LOGIN_URL'])
            
            wait.until(EC.presence_of_element_located((By.ID, CONFIG['SELECTORS']['username_field_id']))).send_keys(CONFIG['CREDENTIALS']['username'])
            driver.find_element(By.ID, CONFIG['SELECTORS']['password_field_id']).send_keys(CONFIG['CREDENTIALS']['password'])
            driver.find_element(By.ID, CONFIG['SELECTORS']['login_button_id']).click()

            # --- STEP 2: NAVIGATE TO FEEDBACK PAGE ---
            print("Login submitted. Waiting for dashboard to load...")
            feedback_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, CONFIG['SELECTORS']['feedback_link_text'])))
            
            print("On dashboard. Clicking the 'FEEDBACK' link...")
            feedback_link.click()

            # --- STEP 3: SWITCH TO THE IFRAME ---
            print("Switching to the feedback iframe...")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, CONFIG['SELECTORS']['iframe_name'])))

            # --- STEP 4: VALIDATE AND SELECT TERM ---
            print("Checking for active feedback sessions...")
            term_dropdown_element = wait.until(EC.presence_of_element_located((By.ID, CONFIG['SELECTORS']['term_dropdown_id'])))
            term_dropdown = Select(term_dropdown_element)

            # CORRECTED LOGIC: Get options with a value that is NOT the default "0"
            valid_options = [opt for opt in term_dropdown.options if opt.get_attribute('value') and opt.get_attribute('value') != '0']

            if not valid_options:
                print("🟡 No active feedback sessions found. The term dropdown is empty.")
                print("Script will now exit.")
                return # Exit the function gracefully

            available_values = [opt.get_attribute('value') for opt in valid_options]
            print(f"✅ Active session(s) found. Available terms: {available_values}")

            # Check if the term specified in CONFIG is available to select
            term_to_select = CONFIG['TERM_VALUE_TO_SELECT']
            if term_to_select in available_values:
                print(f"Selecting configured term: '{term_to_select}'")
                term_dropdown.select_by_value(term_to_select)
            else:
                print(f"❌ Error: Your configured term '{term_to_select}' is not in the list of available terms {available_values}.")
                print("Please update TERM_VALUE_TO_SELECT in the CONFIG and try again.")
                return # Exit the function

            # --- STEP 5: FILL FEEDBACK ---
            print("Waiting for feedback questions to appear...")
            # Wait for the first row of questions before proceeding
            wait.until(EC.presence_of_element_located((By.XPATH, CONFIG['SELECTORS']['question_rows_xpath'])))
            
            question_rows = driver.find_elements(By.XPATH, CONFIG['SELECTORS']['question_rows_xpath'])
            print(f"Found {len(question_rows)} questions. Filling feedback now...")

            for i, row in enumerate(question_rows, 1):
                try:
                    question_text = row.find_element(By.XPATH, "./td[2]").text
                    rating_value = decide_rating(question_text, CONFIG)
                    radio_button = row.find_element(By.XPATH, f".//input[@type='radio' and @value='{rating_value}']")
                    driver.execute_script("arguments[0].click();", radio_button)
                    print(f"  - Question {i}: Answered with rating '{rating_value}'")
                    time.sleep(0.05)
                except Exception as e:
                    print(f"  - Warning: Could not process question row {i}. Skipping. Error: {e}")

            # --- STEP 6: SUBMIT FORM ---
            print("\nAll questions have been filled.")
            if CONFIG.get("SUBMIT_FORM", False):
                print("Attempting to submit form...")
                submit_button = driver.find_element(By.ID, CONFIG['SELECTORS']['submit_button_id'])
                submit_button.click()
                print("✅ FORM SUBMITTED SUCCESSFULLY!")
            else:
                print("👍 Feedback filled. Submission is disabled in the configuration.")

            time.sleep(5)

        except TimeoutException:
            print("\n❌ A timeout occurred. An element took too long to appear.")
            print("Please check your internet connection and verify the 'SELECTORS' in the CONFIG.")
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            print("Please double-check your CONFIG settings and ensure the website structure has changed.")
    
    print("\nScript finished. Browser closed.")


if __name__ == "__main__":
    main()
GRIET Feedback Automation Web App:
This project turns the feedback_automator_griet.py script into a local web application using Flask. You can run the automation from your browser and see live log updates.

Setup Instructions

1. PrerequisitesPython 3.7+ installed.Google Chrome browser installed.
2. Create a Virtual Environment:
It's highly recommended to use a virtual environment to keep dependencies isolated.

# Create the environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

 
3. Install Dependencies:
Install all the required Python packages using the requirements.txt file.

pip install -r requirements.txt

4. Create a Credentials File:
Create a file named .env in the same project folder. This is where you'll securely store your login details. This file is ignored by Git and should never be shared.

Add your credentials to the .env file like this:
GRIET_USER="your_username"
GRIET_PASS="your_password"

5. Run the Web ApplicationStart the Flask web server.
flask run

You should see output indicating the server is running, usually on 
http://127.0.0.1:5000.

6. Use the App:
Open your web browser and navigate to http://127.0.0.1:5000.
You will see the user interface.
Click the "Run Automation" button to start the script.
Watch the live log output in the text area.

How to Update the Automation Logic:
1. This setup is designed to be easily updatable.
2. Open the feedback_automator_griet.py file.
Make any changes you want to the automation logic (e.g., change selectors, add new steps, modify the rating logic).
3. Save the file.
4. The Flask server should automatically restart with your changes. If not, stop it (Ctrl+C) and run flask run again.
5. Refresh the web page and run the automation to see your new code in action!
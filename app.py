import os
from flask import Flask, render_template, Response, request, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

# Make sure this filename matches your automation script.
from feedback_automator import run_feedback_automation

# Initialize the Flask app and tell it where to find HTML files.
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'a-very-secret-key-that-should-be-changed'
CORS(app)

# --- User Authentication Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to /login if not authenticated

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Simple user store. The only valid user is 'user' with password 'password123'
users = {'user': User('user')}
user_passwords = {'user': 'password123'}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the user login process."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and user_passwords.get(username) == password:
            user = users[username]
            login_user(user)
            # After a successful login, send the user to the main dashboard.
            return redirect(url_for('index'))
        flash('Invalid username or password')
    # Show the login page.
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required # This protects the dashboard page.
def index():
    """Serves the main automation dashboard page after login."""
    return render_template('index.html')

@app.route('/run-automation', methods=['POST'])
@login_required # This protects the API endpoint.
def run_automation_endpoint():
    """API endpoint that runs the Selenium script."""
    data = request.get_json()
    griet_username = data.get('username')
    griet_password = data.get('password')

    if not griet_username or not griet_password:
        return Response("Error: GRIET Username and Password are required.", status=400)

    def generate_logs():
        """A generator function that calls the automation script and yields its logs."""
        try:
            # Call the function from the other file and stream its output.
            for message in run_feedback_automation(griet_username, griet_password):
                yield message
        except Exception as e:
            yield f"\n--- A critical error occurred in the backend ---\nError details: {str(e)}"

    return Response(generate_logs(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(port=5000, debug=True)


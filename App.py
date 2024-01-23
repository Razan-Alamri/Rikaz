import os
import sqlite3
from flask import Flask, render_template, g, request, session, redirect

# The Flask application is created and configured.
# The database file, secret key.
app = Flask(__name__)
app.config['DATABASE'] = 'Rikaz.db'
app.config['SECRET_KEY'] = os.urandom(24)


# Database connection setup and teardown functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Signup/Login page
@app.route("/signup-login", methods=["GET", "POST"])
def signup_login():
    if request.method == "POST":
        # Get the form data
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        submit_button = request.form.get("submit_button")

        # Check if the user clicked the signup button
        if submit_button == "signup":
            # Validate the email and password
            if not is_valid_email(email):
                return render_template("signup-login.html", alert_message="Invalid email")
            if not is_valid_password(password):
                return render_template("signup-login.html", alert_message="Invalid password")

            # Check if the email is already in use
            if is_email_duplicate(email):
                return render_template("signup-login.html", alert_message="Email already in use")

            # Create a new user in the database
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO User (firstName, lastName, Email, Password) VALUES (?, ?, ?, ?)",
                (first_name, last_name, email, password)
            )
            db.commit()

            # Redirect the user to the dashboard
            return redirect("/dashboard")

        # Check if the user clicked the login button
        if submit_button == "login":
            print("11")
            # Retrieve the user from the database based on the email
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM User WHERE Email=?", (email,))
            user = cursor.fetchone()

            # Validate the email and password
            if not user or user[4] != password:
                return render_template("signup-login.html", alert_message="Invalid email or password")
            print("33")
            # Store the user ID in the session
            session["user_id"] = user[0]

            # Redirect to the dashboard
            return redirect("/dashboard")

    # Render the signup-login page for GET requests
    return render_template("signup-login.html")

def is_valid_email(email):
    # Perform email validation here
    # You can use regular expressions or a library like Flask-WTF to validate the email format
    return True # Replace with your email validation logic

def is_valid_password(password):
    # Perform password validation here
    # You can check the length, complexity, or other requirements for a valid password
    return True # Replace with your password validation logic

def is_email_duplicate(email):
    # Check if the email already exists in the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE Email=?", (email,))
    user = cursor.fetchone()
    return user is not None

# Dashboard page
@app.route("/dashboard")
def dashboard():
    # Check if the user is logged in
    if "user_id" in session:
        # Retrieve the user from the database based on the user ID
        user_id = session["user_id"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE userID=?", (user_id,))
        user = cursor.fetchone()

        # Pass the user's details to the template
        return render_template("dashboard.html", user=user)
    else:
        # User is not logged in, redirect to the signup-login page
        return redirect("/signup-login")



# Satellite Upload page
@app.route("/satellite-upload")
def satellite_upload():
    return render_template("satellite-upload.html")


# Analysis results page
@app.route("/analysis-results", methods=["GET", "POST"])
def analysis_results():
    # Process the uploaded file and perform analysis if needed
    # Retrieve any form data if necessary
    image_name = request.form.get("image-name")
    satellite_name = request.form.get("satellite-name")
    coordinates = request.form.get("coordinates")
    area_name = request.form.get("area-name")
    spatial_resolution = request.form.get("spatial-resolution")

    # Additional processing and analysis logic if needed

    return render_template("analysis-results.html")


# Export results page
@app.route("/export-results")
def export_results():
    return render_template("export-results.html")


# Previous Results page
@app.route("/previous-results")
def previous_results():
    return render_template("previous-results.html")


# Account Settings page
@app.route("/account-settings")
def account_settings():
    return render_template("account-settings.html")

# Logout route
@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect("/signup-login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
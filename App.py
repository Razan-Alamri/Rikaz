import base64
import os
import re
import sqlite3
from flask import Flask, flash, render_template, g, request, session, redirect, url_for
from datetime import datetime 

# The Flask application is created and configured.
# The database satellite_image, secret key.
app = Flask(__name__, static_url_path='/static', static_folder='static')
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
            
            password_error =  is_valid_password(password)
            if password_error:
                return render_template("signup-login.html", alert_message=password_error)

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
            # Retrieve the user from the database based on the email
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM User WHERE Email=?", (email,))
            user = cursor.fetchone()

            # Validate the email and password
            if not user or user[4] != password:
                return render_template("signup-login.html", alert_message="Invalid email or password")
            
            # Store the user ID in the session
            session["user_id"] = user[0]

            # Redirect to the dashboard
            return redirect("/dashboard")

    # Render the signup-login page for GET requests
    return render_template("signup-login.html")

# Check if the email is valid
def is_valid_email(email):
    # Regular expression pattern for email validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Check if the email matches the pattern
    if re.match(email_pattern, email):
        return True
    else:
        return False

# Check if the password is valid
def is_valid_password(password):
    # Check password length
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    # Check password complexity (e.g., at least one uppercase, one lowercase, and one digit)
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one digit."

    return None

# Check if the email is duplicate
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

# Upload Satellite Image page
@app.route("/satellite-upload", methods=["GET", "POST"])
def satellite_upload():
    if request.method == "POST":
        # Get the form data
        image_name = request.form.get("image-name")
        satellite_name = request.form.get("satellite-name")
        coordinates = request.form.get("coordinates")
        area_name = request.form.get("area-name")
        spatial_resolution = request.form.get("spatial-resolution")
        satellite_image = request.files["file-upload"]

        # Perform any necessary data processing or validation
        # For example, you can save the satellite_image to a specified directory
        # and store the relevant information in the database

        # Save the uploaded satellite_image
        if satellite_image:
            satellite_image_data = satellite_image.read()
        else:
            satellite_image_data = None

        # Store the satellite image data in the SatelliteImage table
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO SatelliteImage (imageName, satelliteImage, satelliteName, Coordinates, areaName, Resolution, Timestamp, userID) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (image_name, satellite_image_data, satellite_name, coordinates, area_name, spatial_resolution, datetime.now(), session["user_id"])
        )
        db.commit()

        # Get the imageID of the inserted satellite image
        image_id = cursor.lastrowid

        # Store the result data in the Result table
        
        # ***************************************************************************************
        # ***************** Change (satellite_image_data) After finsh Map model *****************
        # ***************************************************************************************
        cursor.execute(
            "INSERT INTO Result (Map, Timestamp, userID, imageID) VALUES (?, ?, ?, ?)",
            (satellite_image_data, datetime.now(), session["user_id"], image_id)
        )
        db.commit()
        cursor.close()

        # Pass the form data to the analysis results template
        analysis_results = {
            "image_name": image_name,
            "acquisition_date": datetime.now(),
            "satellite_name": satellite_name,
            "coordinates": coordinates,
            "area_name": area_name,
            "spatial_resolution": spatial_resolution,
            
            # ***************************************************************************************
            # **************************** Change After Finsh Map Model *****************************
            # ***************************************************************************************
            "map_data": base64.b64encode(satellite_image_data).decode("utf-8")
        }

        # Redirect the user to the analysis results page
        return render_template("analysis-results.html", analysis_results=analysis_results)

    # Render the upload satellite image page for GET requests
    return render_template("satellite-upload.html")

# Previous Results page
@app.route("/previous-results")
def previous_results():
    # Fetch the previous results for the logged-in user
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT Result.resultID, SatelliteImage.imageName FROM Result "
        "JOIN SatelliteImage ON Result.imageID = SatelliteImage.imageID "
        "WHERE Result.userID = ?",
        (session["user_id"],)
    )
    previous_results = cursor.fetchall()
    cursor.close()

    # Render the previous results template and pass the results to it
    return render_template("previous-results.html", previous_results=previous_results)

# Analysis Results page
@app.route("/analysis-results-<int:result_id>")
def analysis_results(result_id):
    # Check if the user is logged in
    if "user_id" in session:
        # Fetch the previous results for the logged-in user
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT Result.resultID, SatelliteImage.imageName, SatelliteImage.Coordinates, SatelliteImage.areaName, SatelliteImage.Resolution, SatelliteImage.Timestamp, Result.Map "
            "FROM Result "
            "JOIN SatelliteImage ON Result.imageID = SatelliteImage.imageID "
            "WHERE Result.resultID = ? AND Result.userID = ?",
            (result_id, session["user_id"])
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result is None:
            return "Analysis result not found"

        # Create a dictionary from the result object
        analysis_results = {
            "result_id": result[0],
            "image_name": result[1],
            "coordinates": result[2],
            "area_name": result[3],
            "spatial_resolution": result[4],
            "acquisition_date":  result[5],
            "map_data": base64.b64encode(result[6]).decode("utf-8")
        }

        # Redirect the user to the analysis results page
        return render_template("analysis-results.html", analysis_results=analysis_results)
    
    else:
        # User is not logged in, redirect to the signup-login page
        return redirect("/signup-login")
  
# Export results page
@app.route("/export-results")
def export_results():
    return render_template("export-results.html")
      
# Account Settings page
@app.route('/account-settings')
def account_settings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/signup-login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT Email, firstName, lastName FROM User WHERE userID = ?', (user_id,))
    user_info = cursor.fetchone()
    cursor.close()

    if user_info:
        user = {
            'email': user_info[0],
            'first_name': user_info[1],
            'last_name': user_info[2],
        }
        return render_template('account-settings.html', user=user, alert_message=None)

    return redirect("/signup-login")


# Update Information page
@app.route('/update-information', methods=['GET', 'POST'])
def update_information():
    if request.method == 'GET':
        # Handle GET request (display form)
        user_id = session.get('user_id')
        if not user_id:
            return redirect("/signup-login")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT Email, firstName, lastName FROM User WHERE userID = ?', (user_id,))
        user_info = cursor.fetchone()
        cursor.close()

        if user_info:
            user = {
                'email': user_info[0],
                'first_name': user_info[1],
                'last_name': user_info[2],
            }
            return render_template('update-information.html', user=user, alert_message=None)

        return redirect("/signup-login")

    elif request.method == 'POST':
        # Handle POST request (form submission)
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user_id = session.get('user_id')

        # Validate the form data
        if not is_valid_email(email):
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT Email, firstName, lastName FROM User WHERE userID = ?', (user_id,))
            user_info = cursor.fetchone()
            cursor.close()

            if user_info:
                user = {
                    'email': user_info[0],
                    'first_name': user_info[1],
                    'last_name': user_info[2],
                }
                return render_template('update-information.html', user=user, alert_message='Invalid email address!')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Update the user information in the database
            cursor.execute(
                'UPDATE User SET Email = ?, firstName = ?, lastName = ? WHERE userID = ?',
                (email, first_name, last_name, user_id)
            )
            conn.commit()

            return render_template('account-settings.html', alert_message='User information updated successfully!')

        except sqlite3.Error as e:
            return render_template('account-settings.html', alert_message='An error occurred while updating user information: ' + str(e))

        finally:
            cursor.close()
            
# Change Password page
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        # Handle GET request (display form)
        return render_template('change-password.html', alert_message=None)

    elif request.method == 'POST':
        # Handle POST request (form submission)
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user_id = session.get('user_id')

        # Retrieve the user from the database based on the user ID
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE userID=?", (user_id,))
        user = cursor.fetchone()

        # Validate the old password
        if not user or user[4] != old_password:
            return render_template('change-password.html', alert_message='Invalid old password')

        # Validate the new password and confirm password
        password_error = is_valid_password(new_password)
        if password_error:
            return render_template('change-password.html', alert_message=password_error)

        if new_password != confirm_password:
            return render_template('change-password.html', alert_message='New password and confirm password do not match')

        try:
            # Update the user's password in the database
            cursor.execute("UPDATE User SET Password=? WHERE userID=?", (new_password, user_id))
            db.commit()

            return render_template('account-settings.html', alert_message='Password changed successfully')

        except sqlite3.Error as e:
            return render_template('account-settings.html', alert_message='An error occurred while changing the password: ' + str(e))

        finally:
            cursor.close()
            
# Delete Account page
@app.route('/delete-account', methods=['GET', 'POST'])
def delete_account():
    if request.method == 'POST':
        user_id = session.get('user_id')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Delete the user account and associated data from the database
            cursor.execute('DELETE FROM User WHERE userID = ?', (user_id,))
            cursor.execute('DELETE FROM SatelliteImage WHERE userID = ?', (user_id,))
            cursor.execute('DELETE FROM Result WHERE userID = ?', (user_id,))
            conn.commit()

            # Clear the session data
            session.clear()

            alert_message = 'Account deleted successfully!'
            return render_template('signup-login.html', alert_message=alert_message)

        except sqlite3.Error as e:
            return render_template('account-settings.html', alert_message='An error occurred while deleting the account: ' + str(e))

        finally:
            cursor.close()

    return render_template('delete-account.html')
        
        
# Logout route
@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect("/signup-login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
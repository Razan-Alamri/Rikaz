# Import the necessary modules and functions
import base64
import bcrypt
import os
import re
import sqlite3
from flask import Flask, render_template, g, request, session, redirect, url_for
from datetime import datetime
import requests
from flask_mail import Mail, Message
from pyrsgis import raster
from pyrsgis.ml import imageChipsFromArray
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from tensorflow import keras
import tempfile
from werkzeug.utils import secure_filename

# The Flask application is created and configured.
# The database satellite_image, secret key.
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static'
app.config['DATABASE'] = 'Rikaz.db'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rikazprojeect@gmail.com'
app.config['MAIL_PASSWORD'] = 'emvu vqns yvkc amaw'

mail = Mail(app)

# Load the models
model_files = {
    'ASTER': 'Aster_Model.h5',
    'Landsat': 'Landsat_Model.h5',
    'Sentinel': 'Sentinel_Model.h5',
}

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
        conformPassword = request.form.get("conformPassword")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        submit_button = request.form.get("submit_button")
        
        # Check if the user clicked the signup button
        if submit_button == "signup":
            # Validate the email
            if not is_valid_email(email):
                return render_template("signup-login.html", alert_message="Invalid email")
            
            # Validate the password and confirm password
            password_error =  is_valid_password(password)
            if password_error:
                return render_template("signup-login.html", alert_message=password_error)  

            if password != conformPassword:
                return render_template("signup-login.html", alert_message=' Password and confirm password do not match')

            # Check if the email is already in use
            if is_email_duplicate(email):
                return render_template("signup-login.html", alert_message="Email already in use")

            # Check if the email is deliverable
            if not is_email_deliverable(email):
                return render_template("signup-login.html", alert_message="Email is not deliverable")
            
            # Create a new user in the database
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO User (firstName, lastName, Email, Password) VALUES (?, ?, ?, ?)",
                (first_name, last_name, email, hash_password(password))
            )
            cursor.execute("SELECT * FROM User WHERE Email=?", (email,))
            user = cursor.fetchone()

            # Store the user ID in the session
            session["user_id"] = user[0]
            
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
            if not user or not verify_password(password, user[4]):
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


# Check if the email is deliverable
def is_email_deliverable(email):
    api_key = 'ema_live_NjAym4abmLbAglSpxUXVjaQ3qclLDXWJnqQiGw9c'
    url = f'https://api.emailvalidation.io/v1/info?apikey={api_key}&email={str(email)}'
    response = requests.get(url)
    if response.status_code == 200:
         json_res = response.json()
         format_valid = json_res['format_valid']
         mx_found = json_res['mx_found']
         smtp_check = json_res['smtp_check']
         state = json_res['state']
         check = format_valid and mx_found and smtp_check and state == 'deliverable'
         print(str(format_valid) + str(mx_found) + str(smtp_check) + state)
         print(check)
         return check
    return False


# Check if the email is duplicate
def is_email_duplicate(email):
    # Check if the email already exists in the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE Email=?", (email,))
    user = cursor.fetchone()
    return user is not None


# Hash the password
def hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')


# Verify the password
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

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

        if satellite_image:
            # Save the file to a temporary location
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, secure_filename(satellite_image.filename))
            # Save the file
            satellite_image.save(temp_file_path)

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

        db.commit()
        cursor.close()

        # Redirect the user to the analysis results page
        # return render_template("analysis-results.html", analysis_results=analysis_results)
        return redirect(url_for('predict', file_path=temp_file_path, image_id=image_id, satellite_name=satellite_name))
    # Render the upload satellite image page for GET requests
    return render_template("satellite-upload.html")



# Define the prediction route
@app.route('/predict', methods=['GET'])
def predict():
    file_path = request.args.get('file_path')
    image_id = request.args.get('image_id')  # This retrieves the image_id passed in the URL
    satellite_name=request.args.get('satellite_name')
    
    # Ensure that image_id is not None and is an integer (as expected by the database)
    if image_id is not None:
        try:
            image_id = int(image_id)
        except ValueError:
            # Handle the error if image_id is not an integer
            return "Invalid image ID", 400
    
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404
        # Load the corresponding model based on the selected satellite
    if satellite_name in model_files:
        model_file = model_files[satellite_name]
        model = keras.models.load_model(model_file)
    else:
        # Handle the case where the satellite name is not recognized
        # You could return an error message or a default model
        return "Satellite name not recognized", 400

    # Loading and normalizing the uploaded multispectral image
    dsPre, featuresPre = raster.read(file_path)
    
    # Loading and normalizing the uploaded multispectral image
    # dsPre, featuresPre = raster.read(file_stream)
    
    featuresPre = featuresPre.astype(float)

    for i in range(featuresPre.shape[0]):
        bandMinPre = featuresPre[i, :, :].min()
        bandMaxPre = featuresPre[i, :, :].max()
        bandRangePre = bandMaxPre - bandMinPre
        featuresPre[i, :, :] = (featuresPre[i, :, :] - bandMinPre) / bandRangePre

    # Generating image chips from the array
    image = imageChipsFromArray(featuresPre, x_size=7, y_size=7)

    # Pass the data through the model and get the predictions
    newPredicted = model.predict(image)

    prediction = np.reshape(newPredicted.argmax(axis=1), (dsPre.RasterYSize, dsPre.RasterXSize))

    # These should be updated to reflect the actual classes and colors from the model's predictions.
    class_labels = {
        1: 'Quartz monzonite',
        2: 'Dacite',
        3: 'Colluvium',
        4: 'Andesite',
        5: 'Sandstone and shale',
        6: 'Younger composite fans and terraces',
        7: 'River bed and recent alluvium',
        8: 'Older composite fans and terraces',
        9: 'Light red to gray sandstone'
                    }
    # The following colors are placeholders. They need to be replaced with the correct color values from the output map.
    class_colors = {
        1: '#000078',
        2: '#0000FF',
        3: '#3981EF',
        4: '#77FBE2',
        5: '#9FFC8C',
        6: '#EDF352',
        7: '#F0A000',
        8: '#EA3B25',
        9: '#76150D'
                    }
    # Create a colormap
    color_list = [class_colors[key] for key in sorted(class_colors.keys())]
    cmap = ListedColormap(color_list)
   
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(6, 6))
    cnn_map = prediction
    
    # Display the image
    cnn_map_img = ax.imshow(cnn_map, cmap=cmap)
    
    # Create legend handles manually
    handles = [mpatches.Patch(color=class_colors[key], label=class_labels[key]) 
               for key in sorted(class_labels.keys())]
    # Create a legend
    font_dict = {'family': 'serif', 'size': 12}
    legend = ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc=2, 
                       borderaxespad=0., title='Rock Types', labelspacing=1.8, 
                       prop=font_dict)
    # Set legend title properties
    legend.get_title().set_fontsize('14')
    legend.get_title().set_fontweight('bold')
    legend.get_title().set_fontfamily('serif')
    # Add north arrow
    ax.annotate('N', xy=(0.05, 0.95), xycoords='axes fraction', 
                color='white', fontsize=18, fontweight='bold', 
                fontfamily='serif', ha='center', va='center', 
                arrowprops=dict(arrowstyle='->'))

    # Save the plot as an image file
    plot_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Map.png')
    plt.savefig(plot_file_path, dpi=300, bbox_inches='tight')
    plt.close()
    plot_file = 'static/Map.png'

    # Convert the map image to a binary format for database storage (e.g., as a BLOB)
    with open(plot_file, "rb") as map_file:
        map_data_binary = map_file.read()

    # At the end of the `predict` method, before returning or redirecting
    db = get_db()
    cursor = db.cursor()
    # Store the result data in the Result table
    cursor.execute(
            "INSERT INTO Result (Map, Timestamp, userID, imageID) VALUES (?, ?, ?, ?)",
            (map_data_binary, datetime.now(), session["user_id"], image_id)
        )
    db.commit()
    cursor.close()
    # Return the predictions and temporary image path to the template
    return redirect(url_for('analysis_results', result_id=image_id))


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
        if not user or not verify_password(old_password, user[4]):
            return render_template('change-password.html', alert_message='Invalid old password')

        # Validate the new password and confirm password
        password_error = is_valid_password(new_password)
        if password_error:
            return render_template('change-password.html', alert_message=password_error)

        if new_password != confirm_password:
            return render_template('change-password.html', alert_message='New password and confirm password do not match')

        try:
            # Update the user's password in the database
            cursor.execute("UPDATE User SET Password=? WHERE userID=?", ( hash_password(new_password), user_id))
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
            # ***************************************************************************************
            # ************************** Check to delet all related data ****************************
            # ***************************************************************************************
            
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
     
        
# Contact Us route
@app.route('/contact-us', methods=['POST'])
def handle_contact_form():

    # Retrieve the form data
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    # Send an email
    msg = Message(subject, sender='rikazprojeect@gmail.com', recipients=['rikazprojeect@gmail.com'])
    msg.body = f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}"
    mail.send(msg)
    return 'Email sent successfully'

        
# Logout route
@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect("/signup-login")


# Recommended citation:
# Tripathy, P. pyrsgis: A Python package for remote sensing and GIS data processing. V0.4.
# Available at: https://github.com/PratyushTripathy/pyrsgis

from copy import deepcopy
import numpy as np
from pyrsgis.raster import read
from sklearn.feature_extraction import image

# define a function to create image chips from single band array
def array2d_to_chips(data_arr, y_size=5, x_size=5):
    """
    Image chips from 2D array

    This function generates images chips from single band arrays. The image chips can
    be used as a direct input to deep learning models (eg. Convolutional Neural Network).

    Parameters
    ----------
    data_arr        : array
                      A 2D array from which image chips will be created.

    y_size          : integer
                      The height of the image chips. Ideally an odd number.

    x_size          : integer
                      The width of the image chips. Ideally an odd number.

    Returns
    -------
    image_chips     : array
                      A 3D array containing stacked image chips. The first index
                      represents each image chip and the size is equal to total number
                      of cells in the input array. The 2nd and 3rd index represent the
                      height and the width of the image chips.

    Examples
    --------
    >>> from pyrsgis import raster, ml
    >>> infile = r'E:/path_to_your_file/your_file.tif'
    >>> ds, data_arr = raster.read(infile)
    >>> image_chips = ml.array2d_to_chips(data_arr, y_size=5, x_size=5)
    >>> print('Shape of input array:', data_arr.shape)
    >>> print('Shape of generated image chips:', image_chips.shape)
    Shape of input array: (2054, 2044)
    Shape of generated image chips: (4198376, 5, 5)

    """
    image_chips = deepcopy(data_arr)
    image_chips = np.pad(image_chips, (int(y_size/2),int(x_size/2)), 'reflect')
    image_chips = image.extract_patches_2d(image_chips, (y_size, x_size))

    return(image_chips)

def imageChipsFromSingleBandArray(data_arr, y_size=5, x_size=5):
    image_chips = deepcopy(data_arr)
    image_chips = np.pad(image_chips, (int(y_size/2),int(x_size/2)), 'reflect')
    image_chips = image.extract_patches_2d(image_chips, (y_size, x_size))

    return(image_chips)

# define a function to create image chips from array
def array_to_chips(data_arr, y_size=5, x_size=5):
    """
    Image chips from raster array

    This function generates images chips from single or multi band raster arrays. The image
    chips can be used as a direct input to deep learning models (eg. Convolutional Neural Network).

    Parameters
    ----------
    data_arr        : array
                      A 2D or 3D raster array from which image chips will be created. This
                      should be similar as the one generated by ``pyrsgis.raster.read`` function.

    y_size          : integer
                      The height of the image chips. Ideally an odd number.

    x_size          : integer
                      The width of the image chips. Ideally an odd number.

    Returns
    -------
    image_chips     : array
                      A 3D or 4D array containing stacked image chips. The first index
                      represents each image chip and the size is equal to total number
                      of cells in the input array. The 2nd and 3rd index represent the
                      height and the width of the image chips. If the input array is a
                      3D array, then image_clips will be 4D where the 4th index will
                      represent the number of bands.

    Examples
    --------
    >>> from pyrsgis import raster, ml
    >>> infile = r'E:/path_to_your_file/your_file.tif'
    >>> ds, data_arr = raster.read(infile)
    >>> image_chips = ml.array_to_chips(data_arr, y_size=7, x_size=7)
    >>> print('Shape of input array:', data_arr.shape)
    >>> print('Shape of generated image chips:', image_chips.shape)
    Shape of input array: (6, 2054, 2044)
    Shape of generated image chips: (4198376, 7, 7, 6)

    """

    # if array is a single band image
    if len(data_arr.shape) == 2:
        return(array2d_to_chips(data_arr, y_size=y_size, x_size=x_size))

    # if array is a multi band image
    elif len(data_arr.shape) > 2:
        data_arr = deepcopy(data_arr)

        for band in range(data_arr.shape[0]):
            temp_array = array2d_to_chips(data_arr[band, :, :], y_size=y_size, x_size=x_size)

            if band == 0:
                out_array = np.expand_dims(temp_array, axis=3)
            else:
                out_array = np.concatenate((out_array, np.expand_dims(temp_array, axis=3)), axis=3)

        return(out_array)

    # if shape of the image is less than two dimensions, raise error
    else:
        raise Exception("Sorry, only two or three dimensional arrays allowed.")


def imageChipsFromArray(data_array, x_size=5, y_size=5):

    # if array is a single band image
    if len(data_array.shape) == 2:
        return(imageChipsFromSingleBandArray(data_array, x_size=x_size, y_size=y_size))

    # if array is a multi band image
    elif len(data_array.shape) > 2:
        data_array = deepcopy(data_array)
        data_array = np.rollaxis(data_array, 0, 3)

        for band in range(data_array.shape[2]):
            temp_array = imageChipsFromSingleBandArray(data_array[:, :, band], x_size=x_size, y_size=y_size)

            if band == 0:
                out_array = np.expand_dims(temp_array, axis=3)
            else:
                out_array = np.concatenate((out_array, np.expand_dims(temp_array, axis=3)), axis=3)

        return(out_array)

    # if shape of the image is less than two dimensions, raise error
    else:
        raise Exception("Sorry, only two or three dimensional arrays allowed.")

# define a function to create image chips from TIF file
def raster_to_chips(file, y_size=5, x_size=5):
    """
    Image chips from raster file

    This function generates images chips from single or multi band GeoTIFF file. The image
    chips can be used as a direct input to deep learning models (eg. Convolutional Neural Network).

    This is built on the ``pyrsgis.ml.array_to_chips`` function.

    Parameters
    ----------
    file            : string
                      Name or path of the GeoTIFF file from which image chips will be created.

    y_size          : integer
                      The height of the image chips. Ideally an odd number.

    x_size          : integer
                      The width of the image chips. Ideally an odd number.

    Returns
    -------
    image_chips     : array
                      A 3D or 4D array containing stacked image chips. The first index
                      represents each image chip and the size is equal to total number
                      of cells in the input array. The 2nd and 3rd index represent the
                      height and the width of the image chips. If the input file is a
                      multiband raster, then image_clips will be 4D where the 4th index will
                      represent the number of bands.

    Examples
    --------
    >>> from pyrsgis import raster, ml
    >>> infile_2d = r'E:/path_to_your_file/your_2d_file.tif'
    >>> image_chips = ml.raster_to_chips(infile_2d, y_size=7, x_size=7)
    >>> print('Shape of single band generated image chips:', image_chips.shape)
    Shape of single bandgenerated image chips: (4198376, 7, 7)

    Not that here the shape of the input raster file is 2054 rows by 2044 columns.
    If the raster file is multiband:

    >>> infile_3d = r'E:/path_to_your_file/your_3d_file.tif'
    >>> image_chips = ml.raster_to_chips(infile_3d, y_size=7, x_size=7)
    >>> print('Shape of multiband generated image chips:', image_chips.shape)
    Shape of multiband generated image chips: (4198376, 7, 7, 6)

    """

    ds, data_arr = read(file)

    return(array_to_chips(data_arr, y_size=y_size, x_size=x_size))

def imageChipsFromFile(infile, y_size=5, x_size=5):
    ds, data_arr = read(infile)

    return(imageChipsFromArray(data_arr, y_size=y_size, x_size=x_size))

# End of citation:
# Tripathy, P. pyrsgis: A Python package for remote sensing and GIS data processing. V0.4.
# Available at: https://github.com/PratyushTripathy/pyrsgis

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
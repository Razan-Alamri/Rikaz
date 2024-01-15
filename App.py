from flask import Flask, render_template, g, request, session

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-secret-key'

#
database_file = "rikaz.db"

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Signup/Login page
@app.route("/signup-login.html")
def signup_login():
    return render_template("signup-login.html")

# Dashboard page
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

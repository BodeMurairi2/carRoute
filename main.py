#!/usr/bin/env python3

"""Main logic"""

import os
import re
import json
import ssl
import pdfkit
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, redirect, render_template
from flask import session, url_for, make_response, flash
from flask_session import Session
from store_userphoto import upload_user_image
from get_car_info import get_request
from werkzeug.utils import secure_filename

load_dotenv('config.env')

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("temp_session", exist_ok=True)

# Initialize Flask app
app = Flask(__name__)

# Set secret key for session management
secret_key = secrets.token_hex(32)
app.secret_key = secret_key

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.abspath("temp_session")
app.config['SESSION_PERMANENT'] = False

# set a session
Session(app)

@app.route("/", methods=["GET", "POST"])
def home():
    """Home page to upload car image."""
    if request.method == "POST":
        file = request.files["car_photo"]
        if file:
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_DIR, filename)
            file.save(temp_path)

            uploaded_image = upload_user_image(image_path=temp_path, file_name=filename)
            response_json = get_request(image_path=temp_path)

            session['response_json'] = response_json
            session['uploaded_image'] = uploaded_image

            os.remove(temp_path)

        return redirect(url_for('get_infos'))
    return render_template("index.html")


@app.route("/get-car-info/get-infos", methods=["GET"])
def get_infos():
    """Get car information based on uploaded image."""
    json_response = session.get('response_json', None)
    user_image = session.get('uploaded_image', None)

    data = json.loads(json_response) if json_response else {}
    is_car = data.get("is_car", False)

    if is_car:
        car_details = data.get("car_details", {})
        car_primary_info = {
            "car_name": car_details["brand"],
            "car_model": car_details["model"],
            "car_year": car_details["approximate_year"],
            "body_style": car_details["body_style"],
            "exterior_design": car_details["exterior_design"],
            "interior_design": car_details["interior_design"],
            "color": car_details["color"],
            "lights": car_details["lights"],
            "wheels": car_details["wheels"],
            "technology": car_details["technology"],
            "price": car_details["price_range"],
            "where_to_buy": re.findall(r'https?://[^\s,"]+|www\.[^\s,")]+', car_details["where_to_buy"]),
            "engine_type": car_details["engine_type"],
            "image_url": car_details["image_url_info"],
            "special_features_modifications": car_details["special_features_modifications"],
            "user_uploaded_image_url": user_image
        }
        car_features = car_details.get("car_features", [])
        car_safety_features = car_details.get("safety_features", [])
        car_performance_specs = car_details.get("performance_specifications", {})
    else:
        car_primary_info = {
            "image_url": data.get("image_url_info", ""),
            "message": "The uploaded image does not appear to be a car.",
            "user_uploaded_image_url": user_image
        }
        car_features = []
        car_safety_features = []
        car_performance_specs = {}

    return render_template(
        "carInfo.html",
        is_car=is_car,
        car_primary_info=car_primary_info,
        car_features=car_features,
        car_safety_features=car_safety_features,
        car_performance_specs=car_performance_specs
    )

@app.route("/download-report")
def download_report():
    """Download car information report as PDF."""
    json_response = session.get('response_json', None)
    user_image = session.get('uploaded_image', None)

    if not json_response:
        return redirect(url_for('home'))

    data = json.loads(json_response)
    is_car = data.get("is_car", False)

    if not is_car:
        return "Cannot generate report for non-car image."

    car_details = data.get("car_details", {})
    car_primary_info = {
        "car_name": car_details["brand"],
        "car_model": car_details["model"],
        "car_year": car_details["approximate_year"],
        "body_style": car_details["body_style"],
        "exterior_design": car_details["exterior_design"],
        "interior_design": car_details["interior_design"],
        "color": car_details["color"],
        "lights": car_details["lights"],
        "wheels": car_details["wheels"],
        "technology": car_details["technology"],
        "price": car_details["price_range"],
        "engine_type": car_details["engine_type"],
        "image_url": car_details["image_url_info"],
        "special_features_modifications": car_details["special_features_modifications"],
        "user_uploaded_image_url": user_image
    }

    car_features = car_details.get("car_features", [])
    car_safety_features = car_details.get("safety_features", [])
    car_performance_specs = car_details.get("performance_specifications", {})

    html = render_template(
        "pdf_report.html",
        car_primary_info=car_primary_info,
        car_features=car_features,
        car_safety_features=car_safety_features,
        car_performance_specs=car_performance_specs
    )

    # Render PDF
    config = pdfkit.configuration()
    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=car_report.pdf'
    return response

@app.route("/send", methods=["GET", "POST"])
def send_report():
    """Send car information report via email."""
    if request.method == "POST":
        email_address = request.form.get("email")
        json_response = session.get('response_json', None)
        user_image = session.get('uploaded_image', None)

        if not json_response:
            return "No report data found. Please upload a car image first."

        data = json.loads(json_response)
        is_car = data.get("is_car", False)

        if not is_car:
            return "Cannot send report for non-car image."

        car_details = data.get("car_details", {})
        car_primary_info = {
            "car_name": car_details["brand"],
            "car_model": car_details["model"],
            "car_year": car_details["approximate_year"],
            "body_style": car_details["body_style"],
            "exterior_design": car_details["exterior_design"],
            "interior_design": car_details["interior_design"],
            "color": car_details["color"],
            "lights": car_details["lights"],
            "wheels": car_details["wheels"],
            "technology": car_details["technology"],
            "price": car_details["price_range"],
            "engine_type": car_details["engine_type"],
            "image_url": car_details["image_url_info"],
            "special_features_modifications": car_details["special_features_modifications"],
            "user_uploaded_image_url": user_image
        }

        car_features = car_details.get("car_features", [])
        car_safety_features = car_details.get("safety_features", [])
        car_performance_specs = car_details.get("performance_specifications", {})

        # Render HTML for PDF
        html = render_template(
            "pdf_report.html",
            car_primary_info=car_primary_info,
            car_features=car_features,
            car_safety_features=car_safety_features,
            car_performance_specs=car_performance_specs
        )

        # Generate PDF from HTML string
        pdf = pdfkit.from_string(html, False)

        my_email = os.getenv("SENDER_EMAIL")
        my_password = os.getenv("SENDER_APP_PASSWORD")

        if not my_email or not my_password:
            raise ValueError("Missing EMAIL or APP_PASSWORD environment variables.")

        report_content = f"Dear valuable user,\n\nFind attached your car report.\nThank you for using {os.getenv('SENDER_NAME')}!"

        msg = EmailMessage()
        msg["Subject"] = f"Car Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {car_primary_info['car_name']} {car_primary_info['car_model']}"
        msg["From"] = my_email
        msg["To"] = email_address
        msg.set_content(report_content)

        # Attach the PDF
        msg.add_attachment(pdf, maintype='application', subtype='pdf', filename='car_report.pdf')

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(user=my_email, password=my_password)
            smtp.send_message(msg)
            flash(f"Report sent successfully to {email_address}!", "success")

        return redirect(url_for('home'))

    return render_template("email.html")

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)
#!/usr/bin/env python3
import os
from pathlib import Path
import re
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

# Load environment variables
load_dotenv('config.env')

# Base directory (where this script lives)
BASE_DIR = Path(__file__).resolve().parent

# Absolute paths for upload and session folders using pathlib
UPLOAD_DIR = BASE_DIR / "temp_uploads"
SESSION_DIR = BASE_DIR / "temp_session"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = str(SESSION_DIR)  # Flask expects string paths here
app.config['SESSION_PERMANENT'] = False

Session(app)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("car_photo")
        if file:
            filename = secure_filename(file.filename)
            local_path = UPLOAD_DIR / filename
            file.save(str(local_path))

            response_dict = get_request(image_path=str(local_path))
            uploaded_image_url = upload_user_image(image_path=str(local_path), file_name=filename)

            session['response_json'] = response_dict
            session['uploaded_image_url'] = uploaded_image_url

            return redirect(url_for('get_infos'))

    return render_template("index.html")


@app.route("/get-car-info/get-infos", methods=["GET"])
def get_infos():
    data = session.get('response_json', {})
    uploaded_image_url = session.get('uploaded_image_url', None)

    is_car = data.get("is_car", False)

    if is_car:
        car_details = data.get("car_details", {})
        car_primary_info = {
            "car_name": car_details.get("brand", ""),
            "car_model": car_details.get("model", ""),
            "car_year": car_details.get("approximate_year", ""),
            "body_style": car_details.get("body_style", ""),
            "exterior_design": car_details.get("exterior_design", ""),
            "interior_design": car_details.get("interior_design", ""),
            "color": car_details.get("color", ""),
            "lights": car_details.get("lights", ""),
            "wheels": car_details.get("wheels", ""),
            "technology": car_details.get("technology", ""),
            "price": car_details.get("price_range", ""),
            "where_to_buy": re.findall(r'https?://[^\s,"]+|www\.[^\s,")]+', car_details.get("where_to_buy", "")),
            "engine_type": car_details.get("engine_type", ""),
            "image_url": car_details.get("image_url_info", ""),
            "special_features_modifications": car_details.get("special_features_modifications", ""),
            "user_uploaded_image_url": uploaded_image_url
        }
        car_features = car_details.get("car_features", [])
        car_safety_features = car_details.get("safety_features", [])
        car_performance_specs = car_details.get("performance_specifications", {})
    else:
        car_primary_info = {
            "image_url": data.get("image_url_info", ""),
            "message": "The uploaded image does not appear to be a car.",
            "user_uploaded_image_url": uploaded_image_url
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
    data = session.get('response_json', None)
    uploaded_image_url = session.get('uploaded_image_url', None)

    if not data or not data.get("is_car", False):
        return "Cannot generate report for non-car image."

    car_details = data.get("car_details", {})
    car_primary_info = {
        "car_name": car_details.get("brand", ""),
        "car_model": car_details.get("model", ""),
        "car_year": car_details.get("approximate_year", ""),
        "body_style": car_details.get("body_style", ""),
        "exterior_design": car_details.get("exterior_design", ""),
        "interior_design": car_details.get("interior_design", ""),
        "color": car_details.get("color", ""),
        "lights": car_details.get("lights", ""),
        "wheels": car_details.get("wheels", ""),
        "technology": car_details.get("technology", ""),
        "price": car_details.get("price_range", ""),
        "engine_type": car_details.get("engine_type", ""),
        "image_url": car_details.get("image_url_info", ""),
        "special_features_modifications": car_details.get("special_features_modifications", ""),
        "user_uploaded_image_url": uploaded_image_url
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

    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=car_report.pdf'
    return response


@app.route("/send", methods=["GET", "POST"])
def send_report():
    if request.method == "POST":
        email_address = request.form.get("email")
        data = session.get('response_json', None)
        uploaded_image_url = session.get('uploaded_image_url', None)

        if not data or not data.get("is_car", False):
            return "No valid car data to send."

        car_details = data.get("car_details", {})
        car_primary_info = {
            "car_name": car_details.get("brand", ""),
            "car_model": car_details.get("model", ""),
            "car_year": car_details.get("approximate_year", ""),
            "body_style": car_details.get("body_style", ""),
            "exterior_design": car_details.get("exterior_design", ""),
            "interior_design": car_details.get("interior_design", ""),
            "color": car_details.get("color", ""),
            "lights": car_details.get("lights", ""),
            "wheels": car_details.get("wheels", ""),
            "technology": car_details.get("technology", ""),
            "price": car_details.get("price_range", ""),
            "engine_type": car_details.get("engine_type", ""),
            "image_url": car_details.get("image_url_info", ""),
            "special_features_modifications": car_details.get("special_features_modifications", ""),
            "user_uploaded_image_url": uploaded_image_url
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
        
        config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
        pdf = pdfkit.from_string(html, False, configuration=config)

        my_email = os.getenv("SENDER_EMAIL")
        my_password = os.getenv("SENDER_APP_PASSWORD")

        if not my_email or not my_password:
            raise ValueError("Missing email or app password in environment variables.")

        msg = EmailMessage()
        msg["Subject"] = f"Car Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {car_primary_info['car_name']} {car_primary_info['car_model']}"
        msg["From"] = my_email
        msg["To"] = email_address
        msg.set_content(f"Dear user,\n\nAttached is your car report.\n\nThanks for using {os.getenv('SENDER_NAME', 'CarInfo')}!")

        msg.add_attachment(pdf, maintype='application', subtype='pdf', filename='car_report.pdf')

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(user=my_email, password=my_password)
            smtp.send_message(msg)

        flash(f"Report sent successfully to {email_address}!", "success")
        return redirect(url_for('home'))

    return render_template("email.html")


@app.route("/run")
def test():
    return "Hello from Web-02"

from flask import Flask, render_template, request, redirect, session, url_for
from replit import db
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Please enter both email and password."

        if f"user:{email}" in db:
            return "User already exists. Try logging in."

        db[f"user:{email}"] = {
            "email": email,
            "password": password
        }

        return redirect(url_for("login"))
    return render_template("register_new.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Please enter both email and password."

        user_key = f"user:{email}"
        user = db.get(user_key)

        if user and user["password"] == password:
            session["user"] = email
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password."

    return render_template("login.html")

@app.route('/vendor-login', methods=["GET", "POST"])
def vendor_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Please enter both email and password."

        vendor_key = f"vendor:{email}"
        vendor = db.get(vendor_key)

        if vendor and vendor["password"] == password:
            session["vendor"] = email
            return redirect("https://erp.furrbutler.com")
        else:
            return "Invalid vendor login."

    return render_template("vendor_login.html")

@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    return render_template("dashboard.html", email=email)

@app.route('/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    vendors = [
        {
            "id": "fluffy-paws",
            "name": "Fluffy Paws Grooming",
            "description": "Expert grooming services for dogs and cats.",
            "image": "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
            "rating": 5,
            "level": 15,
            "xp": 2850,
            "city": "Bangalore",
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        {
            "id": "paws-spa",
            "name": "Paws & Relax Spa",
            "description": "Luxury pet spa offering full-service grooming.",
            "image": "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400",
            "rating": 4,
            "level": 12,
            "xp": 2100,
            "city": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        {
            "id": "happy-tails",
            "name": "Happy Tails Grooming",
            "description": "Professional pet grooming services.",
            "image": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400",
            "rating": 5,
            "level": 18,
            "xp": 3200,
            "city": "Hyderabad",
            "latitude": 17.3850,
            "longitude": 78.4867
        }
    ]
    return render_template("groomers.html", vendors=vendors)

@app.route('/vendor/<vendor_id>')
def vendor_profile(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if vendor_id == "fluffy-paws":
        vendor = {
            "name": "Fluffy Paws Grooming",
            "description": "Fluffy Paws offers expert grooming services for dogs and cats.",
            "image": "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=600&h=400&fit=crop",
            "services": ["Full Grooming", "Nail Clipping", "Ear Cleaning"],
            "market_url": "#",
            "booking_url": "/vendor/fluffy-paws/book",
            "rating": 5,
            "level": 15,
            "xp": 2850
        }
        return render_template("vendor_profile.html", vendor=vendor)
    else:
        return render_template("vendor_placeholder.html", vendor_name=vendor_id.replace("-", " ").title())

@app.route('/vendor/<vendor_id>/book', methods=["GET", "POST"])
def book_vendor(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if vendor_id != "fluffy-paws":
        return "Booking only available for Fluffy Paws demo vendor."

    services = ["Full Grooming", "Nail Clipping", "Ear Cleaning"]

    if request.method == "POST":
        selected_service = request.form.get("service")
        selected_date = request.form.get("date")
        print(f"Booking: {selected_service} on {selected_date}")
        return redirect(url_for("dashboard"))

    return render_template("booking.html", vendor_name="Fluffy Paws Grooming", services=services)

@app.route('/boarding')
def boarding():
    if "user" not in session:
        return redirect(url_for("login"))

    

    boardings = [
        {
            "id": "cozy-paws",
            "name": "Cozy Paws Boarding",
            "description": "Safe and cozy stay for your pets.",
            "image": "https://images.unsplash.com/photo-1558788353-f76d92427f16?w=400",
            "city": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777
        },
        {
            "id": "purrfect-inn",
            "name": "Purrfect Inn",
            "description": "Pet-friendly hotel and daycare.",
            "image": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400",
            "city": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    ]

    restaurants = [
        {
            "name": "The Barking Café",
            "description": "Pet‑friendly café with outdoor seating and water bowls.",
            "booking_url": "https://www.booking.com/searchresults.html?ss=pet-friendly+cafe"
        },
        {
            "name": "Fur & Fest",
            "description": "Co‑lodging hotel allowing dogs; book via affiliate.",
            "booking_url": "https://www.booking.com/searchresults.html?ss=pet-friendly+hotel"
        }
    ]

    return render_template("boarding.html", boardings=boardings, restaurants=restaurants)

@app.route('/boarding/<vendor_id>/book', methods=["GET", "POST"])
def book_boarding_vendor(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if vendor_id != "cozy-paws":
        return "Booking only available for Cozy Paws demo vendor."

    durations = [
        "1 Hour", "2 Hours", "6 Hours", "12 Hours", 
        "1 Day", "2 Days", "3 Days", "1 Week"
    ]

    if request.method == "POST":
        selected_duration = request.form.get("duration")
        checkin_date = request.form.get("checkin_date")
        notes = request.form.get("notes")

        # Future: Save booking to DB or send notification
        print(f"Boarding Booking: {selected_duration} from {checkin_date} - Notes: {notes}")
        return redirect(url_for("dashboard"))  # You can add a success screen or message later

    return render_template("boarding_booking.html", 
                           vendor_name="Cozy Paws Boarding", 
                           durations=durations)


@app.route('/vets')
def vets():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("vets.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)

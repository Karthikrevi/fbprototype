from flask import Flask, render_template, request, redirect, session, url_for
from replit import db
import os
import json
from werkzeug.utils import secure_filename

import sqlite3

# Initialize ERP database if not exists
def init_erp_db():
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            category TEXT,
            city TEXT,
            phone TEXT,
            bio TEXT,
            image_url TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            stock INTEGER DEFAULT 0,
            image_url TEXT,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            user_email TEXT,
            service TEXT,
            date TEXT,
            time TEXT,
            duration INTEGER,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            amount REAL,
            paid_on TEXT,
            payment_mode TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')

    conn.commit()
    conn.close()

# Run the DB setup on startup
init_erp_db()


app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'

# Setup for photo uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utility to check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home
@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# Register
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

# Vendor Register
@app.route('/vendor-register', methods=["GET", "POST"])
def vendor_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        category = request.form.get("category")  # grooming, boarding, etc.
        city = request.form.get("city")
        phone = request.form.get("phone")
        bio = request.form.get("bio")
        image_url = request.form.get("image_url")

        conn = sqlite3.connect("erp.db")
        c = conn.cursor()

        try:
            c.execute('''
                INSERT INTO vendors (name, email, password, category, city, phone, bio, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password, category, city, phone, bio, image_url))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Vendor with this email already exists."

        conn.close()
        return redirect(url_for("vendor_login"))

    return render_template("vendor_register.html")


# Login
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

# Vendor Login
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
            return redirect("https://erp.furrbutler.com")  # placeholder
        else:
            return "Invalid vendor login."

    return render_template("vendor_login.html")






# Dashboard
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    return render_template("dashboard.html", email=email)

# Groomers & Vendors
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

@app.route('/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    user_location = session.get("location")

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
    
    # Apply location filtering if user location is available
    if user_location:
        vendors = [
            v for v in vendors if haversine(
                user_location["lat"], user_location["lon"], v["latitude"], v["longitude"]
            ) <= 50  # Filter vendors within 50 km
        ]
    
    return render_template("groomers.html", vendors=vendors)

# Vendor Profile
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

# Booking (Fluffy Paws only)
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

# Boarding
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

# Vets & Pharma
@app.route('/vets')
def vets():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("vets.html")

# Pet Profile Routes
@app.route('/pet-profile', methods=["GET", "POST"])
def pet_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    user = session["user"]
    pets = db.get(f"pets:{user}", [])

    if request.method == "POST":
        name = request.form.get("name")
        birthday = request.form.get("birthday")
        breed = request.form.get("breed")
        blood = request.form.get("blood")
        photo_url = ""

        file = request.files.get("photo")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            photo_url = "/" + filepath

        pet = {
            "name": name,
            "birthday": birthday,
            "breed": breed,
            "blood": blood,
            "photo": photo_url
        }

        pets.append(pet)
        db[f"pets:{user}"] = pets

        return redirect(url_for("pet_profile"))

    return render_template("pet_profile.html", breeds=breeds, pets=pets)

@app.route('/pet-profile/add', methods=['GET', 'POST'])
def add_pet():
    if "user" not in session:
        return redirect(url_for("login"))

    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        birthday = request.form.get("birthday")
        breed = request.form.get("breed")
        blood = request.form.get("blood")
        photo = request.files.get("photo")

        if not name:
            return "Pet name is required."

        filename = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            try:
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print("Image save failed:", e)

        user = session["user"]
        pets = db.get(f"pets:{user}", [])

        pet = {
            "name": name,
            "birthday": birthday,
            "breed": breed,
            "blood": blood,
            "photo": filename
        }

        pets.append(pet)
        db[f"pets:{user}"] = pets

        return redirect(url_for("pet_profile"))

    return render_template("add_pet.html", breeds=breeds)

@app.route('/pet-profile/edit/<int:index>', methods=["GET", "POST"])
def edit_pet(index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])

    if index >= len(pets):
        return "Pet not found"

    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    if request.method == "POST":
        pets[index]["name"] = request.form.get("name")
        pets[index]["birthday"] = request.form.get("birthday")
        pets[index]["breed"] = request.form.get("breed")
        pets[index]["blood"] = request.form.get("blood")

        db[f"pets:{user}"] = pets
        return redirect(url_for("pet_profile"))

    return render_template("edit_pet.html", pet=pets[index], index=index, breeds=breeds)
    
#location
@app.route('/set-location')
def set_location():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat and lon:
        session["location"] = {"lat": lat, "lon": lon}
    return '', 204
    
# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)

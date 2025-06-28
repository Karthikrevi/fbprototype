from flask import Flask, render_template, request, redirect, session, url_for
from replit import db
import os
import json
from werkzeug.utils import secure_filename
from math import radians, cos, sin, asin, sqrt
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
            image_url TEXT,
            latitude REAL,
            longitude REAL
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
            return redirect(url_for("erp_dashboard"))
        else:
            return "Invalid vendor login."

    return render_template("vendor_login.html")



#Vendor Register
@app.route('/vendor-register', methods=["GET", "POST"])
def vendor_register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        category = request.form.get("category")
        city = request.form.get("city")
        phone = request.form.get("phone")
        bio = request.form.get("bio")
        image_url = request.form.get("image_url")

        if not email or not password or not name or not category:
            return "Missing required fields."

        vendor_key = f"vendor:{email}"
        if db.get(vendor_key):
            return "Vendor already exists."

        db[vendor_key] = {
            "email": email,
            "password": password,
            "name": name,
            "category": category,
            "city": city,
            "phone": phone,
            "bio": bio,
            "image_url": image_url
        }

        return redirect(url_for("vendor_login"))

    return render_template("vendor_register.html")


# Dashboard
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    return render_template("dashboard.html", email=email)

# Groomers & Vendors
def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in kilometers
    R = 6371.0
    
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')  # Or some default/fallback
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    
    return R * 2 * asin(sqrt(a))

@app.route('/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    user_location = session.get("location")

    # Get vendors from ERP database with grooming category
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors WHERE category IN ('grooming', 'groomer', 'pet grooming')")
    db_vendors = c.fetchall()
    conn.close()

    vendors = []
    for vendor in db_vendors:
        vendor_data = {
            "id": vendor[0],  # vendor id
            "name": vendor[2],  # vendor name
            "description": vendor[7] or "Professional pet grooming services.",  # bio
            "image": vendor[8] or "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
            "rating": 5,  # Default rating
            "level": 10,  # Default level
            "xp": 1500,  # Default XP
            "city": vendor[5] or "Unknown",
            "latitude": None,  # Will be set from location data if available
            "longitude": None
        }
        vendors.append(vendor_data)

    # Always show demo vendor for testing
    demo_vendor = {
        "id": "fluffy-paws",
        "name": "Fluffy Paws Grooming",
        "description": "Expert grooming services for dogs and cats. [DEMO]",
        "image": "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
        "rating": 5,
        "level": 15,
        "xp": 2850,
        "city": "Bangalore",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    vendors.append(demo_vendor)
    
    # Apply location filtering if user location is available
    if user_location:
        filtered_vendors = []
        for v in vendors:
            if v["latitude"] and v["longitude"]:
                distance = haversine(
                    user_location["lat"], user_location["lon"], v["latitude"], v["longitude"]
                )
                if distance <= 50:  # Filter vendors within 50 km
                    filtered_vendors.append(v)
            else:
                # Include vendors without location data for now
                filtered_vendors.append(v)
        vendors = filtered_vendors
    
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

    user_location = session.get("location")

    # Get vendors from ERP database with boarding/hotel category
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors WHERE category IN ('boarding', 'hotel', 'pet boarding', 'daycare')")
    db_vendors = c.fetchall()
    conn.close()

    boardings = []
    for vendor in db_vendors:
        vendor_data = {
            "id": vendor[0],  # vendor id
            "name": vendor[2],  # vendor name
            "description": vendor[7] or "Safe and comfortable stay for your pets.",  # bio
            "image": vendor[8] or "https://images.unsplash.com/photo-1558788353-f76d92427f16?w=400",
            "city": vendor[5] or "Unknown",
            "latitude": None,  # Will be set from location data if available
            "longitude": None
        }
        boardings.append(vendor_data)

    # Always show demo boarding for testing
    demo_boarding = {
        "id": "cozy-paws",
        "name": "Cozy Paws Boarding",
        "description": "Safe and cozy stay for your pets. [DEMO]",
        "image": "https://images.unsplash.com/photo-1558788353-f76d92427f16?w=400",
        "city": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    }
    boardings.append(demo_boarding)

    # Apply location filtering if user location is available
    if user_location:
        filtered_boardings = []
        for b in boardings:
            if b["latitude"] and b["longitude"]:
                distance = haversine(
                    user_location["lat"], user_location["lon"], b["latitude"], b["longitude"]
                )
                if distance <= 50:  # Filter vendors within 50 km
                    filtered_boardings.append(b)
            else:
                # Include vendors without location data for now
                filtered_boardings.append(b)
        boardings = filtered_boardings

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

        if file is not None and file.filename and allowed_file(file.filename):
            filename: str = secure_filename(file.filename)
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

# ---- ERP ROUTES ----

@app.route('/erp')
def erp_home():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    return redirect(url_for("erp_dashboard"))

@app.route('/erp/login', methods=["GET", "POST"])
def erp_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vendors WHERE email=? AND password=?", (email, password))
        vendor = c.fetchone()
        conn.close()

        if vendor:
            session["vendor"] = email
            return redirect(url_for("erp_dashboard"))
        else:
            return "Invalid credentials"

    return render_template("erp_login.html")

@app.route('/erp/register', methods=["GET", "POST"])
def erp_register():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        password = request.form["password"]
        category = request.form.get("category", "")
        city = request.form.get("city", "")
        phone = request.form.get("phone", "")
        bio = request.form.get("bio", "")
        image_url = request.form.get("image_url", "")

        try:
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("INSERT INTO vendors (email, name, password, category, city, phone, bio, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                     (email, name, password, category, city, phone, bio, image_url))
            conn.commit()
            conn.close()
            return redirect(url_for("erp_login"))
        except sqlite3.IntegrityError:
            return "Vendor already exists with that email."

    return render_template("vendor_register.html")

@app.route('/erp/dashboard')
def erp_dashboard():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    return render_template("erp_dashboard.html", vendor=session["vendor"])

@app.route('/erp/profile', methods=["GET", "POST"])
def erp_profile():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form.get("phone", "")
        bio = request.form.get("bio", "")
        image_url = request.form.get("image_url", "")
        city = request.form.get("city", "")
        latitude = request.form.get("latitude", "")
        longitude = request.form.get("longitude", "")

        # Convert coordinates to float if provided
        lat_val = float(latitude) if latitude else None
        lon_val = float(longitude) if longitude else None

        c.execute('''
            UPDATE vendors 
            SET name=?, phone=?, bio=?, image_url=?, city=?, latitude=?, longitude=? 
            WHERE email=?
        ''', (name, phone, bio, image_url, city, lat_val, lon_val, email))
        conn.commit()

    c.execute("SELECT name, email, phone, bio, image_url, city, latitude, longitude FROM vendors WHERE email=?", (email,))
    vendor = c.fetchone()
    conn.close()

    return render_template("erp_profiles.html", vendor=vendor)

@app.route('/erp/products')
def erp_products():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT p.* FROM products p JOIN vendors v ON p.vendor_id = v.id WHERE v.email=?", (email,))
    products = c.fetchall()
    conn.close()

    return render_template("erp_products.html", products=products)

@app.route('/erp/bookings')
def erp_bookings():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT b.* FROM bookings b JOIN vendors v ON b.vendor_id = v.id WHERE v.email=?", (email,))
    bookings = c.fetchall()
    conn.close()

    return render_template("erp_booking.html", bookings=bookings)

@app.route('/erp/logout')
def erp_logout():
    session.pop("vendor", None)
    return redirect(url_for("erp_login"))

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)

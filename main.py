from flask import Flask, render_template, request, redirect, session, url_for, flash
from replit import db
import os
import json
from werkzeug.utils import secure_filename
from math import radians, cos, sin, asin, sqrt
import sqlite3
from datetime import datetime

# Initialize ERP database if not exists
def init_erp_db():
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Check if products table exists and get its structure
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    products_table_exists = c.fetchone() is not None

    if products_table_exists:
        # Get current column structure
        c.execute("PRAGMA table_info(products)")
        existing_columns = [column[1] for column in c.fetchall()]

        # If the table exists but doesn't have the right columns, recreate it
        required_columns = ['id', 'vendor_id', 'name', 'description', 'category', 'buy_price', 'sale_price', 'quantity', 'image_url', 'barcode']
        missing_columns = [col for col in required_columns if col not in existing_columns]

        if missing_columns:
            # Backup existing data
            c.execute("SELECT * FROM products")
            existing_products = c.fetchall()

            # Drop and recreate table
            c.execute("DROP TABLE products")
            products_table_exists = False

    # Create all tables with correct schema
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
            longitude REAL,
            is_online BOOLEAN DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            buy_price REAL,
            sale_price REAL,
            quantity INTEGER DEFAULT 0,
            image_url TEXT,
            barcode TEXT UNIQUE,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS product_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            batch_name TEXT,
            quantity INTEGER,
            buy_price REAL,
            arrival_date TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
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

    # Accounting Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            entry_type TEXT NOT NULL,
            account TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sales_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL,
            customer_email TEXT,
            sale_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            unit_cost REAL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            remaining_quantity INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            amount REAL,
            payment_method TEXT,
            razorpay_id TEXT,
            status TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS platform_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            sale_id INTEGER,
            fee_percentage REAL DEFAULT 10.0,
            fee_amount REAL,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS settings_vendor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER UNIQUE,
            gst_rate REAL DEFAULT 18.0,
            platform_fee REAL DEFAULT 10.0,
            razorpay_enabled BOOLEAN DEFAULT 1,
            cod_enabled BOOLEAN DEFAULT 1,
            auto_reports BOOLEAN DEFAULT 0,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Insert demo vendor
    c.execute('''
        INSERT OR IGNORE INTO vendors (name, email, password, category, city, latitude, longitude, is_online)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Demo Groomer", "demo@furrbutler.com", "demo123", "Groomer", "Trivandrum", 8.5241, 76.9366, 1))

    # Get demo vendor ID
    c.execute("SELECT id FROM vendors WHERE email = 'demo@furrbutler.com'")
    demo_vendor_id = c.fetchone()

    if demo_vendor_id:
        demo_vendor_id = demo_vendor_id[0]

        # Insert demo products
        demo_products = [
            ("Premium Dog Shampoo", "Professional grade dog shampoo for all coat types", "Grooming", 15.00, 25.00, 50, "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400", "DOG001"),
            ("Cat Nail Clippers", "Professional stainless steel nail clippers for cats", "Grooming", 8.00, 15.00, 30, "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400", "CAT001"),
            ("Pet Brush Set", "Complete grooming brush set for dogs and cats", "Grooming", 12.00, 22.00, 25, "https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=400", "BRUSH001")
        ]

        for product in demo_products:
            c.execute('''
                INSERT OR IGNORE INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, image_url, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (demo_vendor_id,) + product)

            # Get product ID and add batch
            c.execute("SELECT id FROM products WHERE barcode = ?", (product[7],))
            product_id = c.fetchone()
            if product_id:
                c.execute('''
                    INSERT OR IGNORE INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (product_id[0], f"BATCH-{product[7]}-001", product[5], product[3], datetime.now().strftime("%Y-%m-%d")))

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
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    R = 6371.0
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

@app.route('/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    user_city = "Trivandrum"  # Hardcoded for now
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all groomers in the same city
    c.execute("""
        SELECT * FROM vendors 
        WHERE (LOWER(category) LIKE '%groom%' OR LOWER(category) LIKE '%salon%' OR LOWER(category) LIKE '%spa%')
        AND LOWER(city) = LOWER(?)
    """, (user_city,))
    db_vendors = c.fetchall()
    conn.close()

    vendors = []
    for vendor in db_vendors:
        vendor_data = {
            "id": vendor[0],
            "name": vendor[1],
            "description": vendor[7] or "Professional pet grooming services.",
            "image": vendor[8] or "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
            "rating": 5,
            "level": 10,
            "xp": 1500,
            "city": vendor[5] or "Unknown",
            "latitude": vendor[9],
            "longitude": vendor[10],
            "is_online": vendor[11]  # Add online status
        }
        vendors.append(vendor_data)

    return render_template("groomers.html", vendors=vendors)

# Vendor Profile
@app.route('/vendor/<vendor_id>')
def vendor_profile(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = sqlite3.connect("erp.db")
        c = conn.cursor()
        c.execute("SELECT id, name, bio, image_url, city, is_online FROM vendors WHERE id = ?", (vendor_id,))
        data = c.fetchone()
        conn.close()

        if data:
            vendor = {
                "id": data[0],
                "name": data[1],
                "description": data[2] or "Trusted pet care provider.",
                "image": data[3] or "https://images.unsplash.com/photo-1558788353-f76d92427f16?w=600&h=400&fit=crop",
                "city": data[4] or "Unknown",
                "is_online": data[5],
                "rating": 4,
                "level": 8,
                "xp": 1200,
                "booking_url": f"/vendor/{data[0]}/book",
                "market_url": "#"
            }
            return render_template("vendor_profile.html", vendor=vendor)
        else:
            return render_template("vendor_placeholder.html", vendor_name="Unknown Vendor")
    except Exception as e:
        print("Error loading vendor:", e)
        return "Error loading vendor profile"

# Boarding
@app.route('/boarding')
def boarding():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("boarding.html", boardings=[], restaurants=[])

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

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT name, is_online FROM vendors WHERE email=?", (email,))
    vendor_data = c.fetchone()
    conn.close()

    vendor_info = {
        "email": email,
        "name": vendor_data[0] if vendor_data else email,
        "is_online": vendor_data[1] if vendor_data else 0
    }

    return render_template("erp_dashboard.html", vendor=vendor_info)

@app.route('/erp/profile', methods=["GET"])
def erp_profile():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT name, email, phone, bio, image_url, city, latitude, longitude, category FROM vendors WHERE email=?", (email,))
    vendor = c.fetchone()
    conn.close()

    return render_template("erp_profile_view.html", vendor=vendor or ("", email, "", "", "", "", "", "", ""))

@app.route('/erp/profile/edit', methods=["GET", "POST"])
def edit_vendor_profile():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "")
        phone = request.form.get("phone", "")
        bio = request.form.get("bio", "")
        city = request.form.get("city", "")
        category = request.form.get("category", "")

        image_url = ""
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = "/" + filepath
        else:
            c.execute("SELECT image_url FROM vendors WHERE email=?", (email,))
            existing = c.fetchone()
            image_url = existing[0] if existing and existing[0] else ""

        c.execute('''
            UPDATE vendors 
            SET name=?, phone=?, bio=?, image_url=?, city=?, category=?
            WHERE email=?
        ''', (name, phone, bio, image_url, city, category, email))

        conn.commit()
        conn.close()
        return redirect(url_for("erp_profile"))

    c.execute("SELECT name, email, phone, bio, image_url, city, latitude, longitude, category FROM vendors WHERE email=?", (email,))
    vendor = c.fetchone()
    conn.close()

    return render_template("erp_profiles.html", vendor=vendor or ("", email, "", "", "", "", "", "", ""))

# ERP Products Management
@app.route('/erp/products')
def erp_products():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.name, p.description, p.sale_price, p.quantity, p.image_url, p.barcode, p.buy_price
        FROM products p 
        JOIN vendors v ON p.vendor_id = v.id 
        WHERE v.email=?
    """, (email,))
    products = c.fetchall()
    conn.close()

    return render_template("erp_products.html", products=products)

@app.route('/erp/products/add', methods=["GET", "POST"])
def add_product():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    if request.method == "POST":
        email = session["vendor"]
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        
        if vendor_result is None:
            conn.close()
            flash("Vendor not found. Please contact support.")
            return redirect(url_for("add_product"))
        
        vendor_id = vendor_result[0]

        name = request.form.get("name")
        description = request.form.get("description")
        category = request.form.get("category")
        buy_price = float(request.form.get("buy_price", 0))
        sale_price = float(request.form.get("sale_price", 0))
        quantity = int(request.form.get("quantity", 0))
        barcode = request.form.get("barcode")
        batch_name = request.form.get("batch_name")

        # Handle image upload
        image_url = ""
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = "/" + filepath

        # Insert product
        c.execute("""
            INSERT INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, image_url, barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, name, description, category, buy_price, sale_price, quantity, image_url, barcode))

        product_id = c.lastrowid

        # Insert batch
        c.execute("""
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, batch_name or f"BATCH-{barcode}-001", quantity, buy_price, datetime.now().strftime("%Y-%m-%d")))

        conn.commit()
        conn.close()
        return redirect(url_for("erp_products"))

    return render_template("add_product.html")

@app.route('/erp/products/<int:product_id>/edit', methods=["GET", "POST"])
def edit_product(product_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        category = request.form.get("category")
        sale_price = float(request.form.get("sale_price", 0))
        barcode = request.form.get("barcode")

        # Handle image upload
        image_url = request.form.get("existing_image", "")
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = "/" + filepath

        c.execute("""
            UPDATE products 
            SET name=?, description=?, category=?, sale_price=?, image_url=?, barcode=?
            WHERE id=? AND vendor_id=(SELECT id FROM vendors WHERE email=?)
        """, (name, description, category, sale_price, image_url, barcode, product_id, email))

        conn.commit()
        conn.close()
        return redirect(url_for("erp_products"))

    # Get product details
    c.execute("""
        SELECT p.* FROM products p 
        JOIN vendors v ON p.vendor_id = v.id 
        WHERE p.id=? AND v.email=?
    """, (product_id, email))
    product = c.fetchone()

    # Get batches
    c.execute("SELECT * FROM product_batches WHERE product_id=? ORDER BY arrival_date", (product_id,))
    batches = c.fetchall()

    conn.close()

    return render_template("edit_product.html", product=product, batches=batches)

@app.route('/erp/products/<int:product_id>/view')
def view_product(product_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get product details
    c.execute("""
        SELECT p.* FROM products p 
        JOIN vendors v ON p.vendor_id = v.id 
        WHERE p.id=? AND v.email=?
    """, (product_id, email))
    product = c.fetchone()

    # Get batches ordered by arrival date (FIFO)
    c.execute("SELECT * FROM product_batches WHERE product_id=? ORDER BY arrival_date", (product_id,))
    batches = c.fetchall()

    conn.close()

    return render_template("view_product.html", product=product, batches=batches)

# ERP Bookings
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

@app.route('/erp/toggle-online', methods=["POST"])
def toggle_vendor_online():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT is_online FROM vendors WHERE email=?", (email,))
    current_status = c.fetchone()
    if current_status is None:
        conn.close()
        return "Vendor not found", 404

    current_status = current_status[0]

    new_status = 1 if current_status == 0 else 0
    c.execute("UPDATE vendors SET is_online=? WHERE email=?", (new_status, email))
    conn.commit()
    conn.close()

    return redirect(url_for("erp_dashboard"))

@app.route('/erp/logout')
def erp_logout():
    session.pop("vendor", None)
    return redirect(url_for("erp_login"))

# ---- ACCOUNTING & REPORTING ROUTES ----

@app.route('/erp/reports')
def accounting_dashboard():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_id = c.fetchone()

    if vendor_id is None:
        conn.close()
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_id[0]

    # Quick stats
    c.execute("SELECT SUM(amount) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_sales = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE vendor_id=?", (vendor_id,))
    total_expenses = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM products WHERE vendor_id=?", (vendor_id,))
    total_products = c.fetchone()[0] or 0

    c.execute("SELECT SUM(quantity) FROM products WHERE vendor_id=?", (vendor_id,))
    total_inventory = c.fetchone()[0] or 0

    conn.close()

    stats = {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'net_profit': total_sales - total_expenses,
        'total_products': total_products,
        'total_inventory': total_inventory
    }

    return render_template("accounting_dashboard.html", stats=stats)

@app.route('/erp/reports/ledger')
def general_ledger():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn= sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("""
        SELECT le.*, v.id as vendor_id FROM ledger_entries le 
        JOIN vendors v ON le.vendor_id = v.id 
        WHERE v.email=? 
        ORDER BY le.timestamp DESC
    """, (email,))
    entries = c.fetchall()

    conn.close()
    return render_template("general_ledger.html", entries=entries)

@app.route('/erp/reports/pnl')
def profit_loss():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return redirect(url_for("erp_login"))

    vendor_id = result[0]

    # Sales (Revenue)
    c.execute("SELECT SUM(total_amount) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_revenue = c.fetchone()[0] or 0

    # Cost of Goods Sold (COGS) - calculated from inventory
    c.execute("""
        SELECT SUM(sl.quantity * ib.unit_cost) 
        FROM sales_log sl 
        JOIN inventory_batches ib ON sl.product_id = ib.product_id 
        WHERE sl.vendor_id=?
    """, (vendor_id,))
    cogs = c.fetchone()[0] or 0

    # Operating Expenses
    c.execute("SELECT SUM(amount) FROM expenses WHERE vendor_id=?", (vendor_id,))
    total_expenses = c.fetchone()[0] or 0

    # Platform Fees
    c.execute("SELECT SUM(fee_amount) FROM platform_fees WHERE vendor_id=?", (vendor_id,))
    platform_fees = c.fetchone()[0] or 0

    gross_profit = total_revenue - cogs
    net_profit = gross_profit - total_expenses - platform_fees

    pnl_data = {
        'revenue': total_revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'expenses': total_expenses,
        'platform_fees': platform_fees,
        'net_profit': net_profit
    }

    conn.close()
    return render_template("profit_loss.html", pnl=pnl_data)

@app.route('/erp/reports/inventory')
def inventory_report():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("""
        SELECT p.name, p.quantity, p.buy_price, p.sale_price,
               (p.quantity * p.buy_price) as total_cost,
               (p.quantity * p.sale_price) as total_value
        FROM products p 
        JOIN vendors v ON p.vendor_id = v.id 
        WHERE v.email=?
    """, (email,))
    inventory = c.fetchall()

    conn.close()
    return render_template("inventory_report.html", inventory=inventory)

@app.route('/erp/reports/expenses', methods=["GET", "POST"])
def manage_expenses():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return redirect(url_for("erp_login"))

    vendor_id = result[0]

    if request.method == "POST":
        category = request.form.get("category")
        amount = float(request.form.get("amount"))
        description = request.form.get("description")
        date = request.form.get("date")

        # Add expense
        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, category, amount, description, date))

        # Add to ledger
        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description)
            VALUES (?, 'debit', ?, ?, ?)
        """, (vendor_id, category, amount, description))

        conn.commit()
        return redirect(url_for("manage_expenses"))

    # Get all expenses
    c.execute("SELECT * FROM expenses WHERE vendor_id=? ORDER BY date DESC", (vendor_id,))
    expenses = c.fetchall()

    conn.close()
    return render_template("manage_expenses.html", expenses=expenses)

@app.route('/erp/reports/settings', methods=["GET", "POST"])
def accounting_settings():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return redirect(url_for("erp_login"))

    vendor_id = result[0]

    if request.method == "POST":
        gst_rate = float(request.form.get("gst_rate", 18.0))
        platform_fee = float(request.form.get("platform_fee", 10.0))
        razorpay_enabled = 1 if request.form.get("razorpay_enabled") else 0
        cod_enabled = 1 if request.form.get("cod_enabled") else 0
        auto_reports = 1 if request.form.get("auto_reports") else 0

        # Insert or update settings
        c.execute("""
            INSERT OR REPLACE INTO settings_vendor 
            (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports))

        conn.commit()
        flash("Settings updated successfully!")
        return redirect(url_for("accounting_settings"))

    # Get current settings
    c.execute("SELECT * FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    settings = c.fetchone()

    conn.close()
    return render_template("accounting_settings.html", settings=settings)

# Marketplace route
@app.route('/marketplace')
def marketplace():
    if "user" not in session:
        return redirect(url_for("login"))

    user_city = "Trivandrum"  # Hardcoded for now

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT v.*, 
               (SELECT COUNT(*) FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0) as product_count
        FROM vendors v 
        WHERE v.is_online = 1 
        AND LOWER(v.city) = LOWER(?)
        AND EXISTS (
            SELECT 1 FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0
        )
    """, (user_city,))
    online_vendors = c.fetchall()

    vendors = []
    for vendor in online_vendors:
        vendor_data = {
            "id": vendor[0],
            "name": vendor[1],
            "email": vendor[2],
            "category": vendor[4],
            "city": vendor[5],
            "bio": vendor[7],
            "image_url": vendor[8],
            "latitude": vendor[9],
            "longitude": vendor[10],
            "product_count": vendor[12],
            "is_online": vendor[11]  # This will be 1 since we're filtering for online vendors
        }
        vendors.append(vendor_data)

    conn.close()
    return render_template("marketplace.html", vendors=vendors)

@app.route('/marketplace/vendor/<int:vendor_id>')
def marketplace_vendor_products(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor info including online status
    c.execute("SELECT name, city, bio, is_online FROM vendors WHERE id=?", (vendor_id,))
    vendor_data = c.fetchone()

    if not vendor_data:
        return "Vendor not found", 404

    vendor = {
        "name": vendor_data[0],
        "city": vendor_data[1],
        "bio": vendor_data[2],
        "is_online": vendor_data[3]
    }

    # Get products with stock only if vendor is online
    if vendor["is_online"]:
        c.execute("""
            SELECT id, name, description, sale_price, quantity, image_url 
            FROM products 
            WHERE vendor_id=? AND quantity > 0
        """, (vendor_id,))
        products = c.fetchall()
    else:
        products = []

    conn.close()

    return render_template("marketplace_vendor_products.html", vendor=vendor, products=products, vendor_id=vendor_id)

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
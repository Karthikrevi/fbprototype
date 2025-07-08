from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
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
            is_online BOOLEAN DEFAULT 0,
            account_status TEXT DEFAULT 'active',
            break_start_date TEXT,
            break_end_date TEXT,
            break_reason TEXT
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
            status_details TEXT,
            estimated_completion TEXT,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            vendor_id INTEGER,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            delivery_address TEXT,
            delivery_type TEXT DEFAULT 'standard',
            delivery_fee REAL DEFAULT 0,
            estimated_delivery TEXT,
            tracking_notes TEXT,
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
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
            sub_category TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Add sub_category column if it doesn't exist
    try:
        c.execute("ALTER TABLE ledger_entries ADD COLUMN sub_category TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

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
            standard_delivery_price REAL DEFAULT 2.99,
            express_delivery_price REAL DEFAULT 5.99,
            same_day_delivery_price REAL DEFAULT 12.99,
            free_delivery_threshold REAL DEFAULT 50.00,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Create master settings table for platform-wide settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value REAL NOT NULL,
            description TEXT,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            previous_value REAL DEFAULT NULL
        )
    ''')

    # Check if previous_value column exists, if not add it
    c.execute("PRAGMA table_info(master_settings)")
    columns = [column[1] for column in c.fetchall()]
    if 'previous_value' not in columns:
        c.execute("ALTER TABLE master_settings ADD COLUMN previous_value REAL DEFAULT NULL")

    # Insert default master settings if they don't exist
    c.execute('''
        INSERT OR IGNORE INTO master_settings (setting_name, setting_value, description)
        VALUES 
        ('marketplace_commission_rate', 10.0, 'Commission percentage for marketplace sales'),
        ('grooming_commission_rate', 15.0, 'Commission percentage for grooming services'),
        ('payment_processing_fee', 2.9, 'Payment processing fee percentage'),
        ('marketplace_listing_fee', 0.0, 'Fee for listing products on marketplace')
    ''')

    # Create platform earnings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS platform_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            transaction_type TEXT NOT NULL,
            service_type TEXT NOT NULL,
            base_amount REAL NOT NULL,
            commission_rate REAL NOT NULL,
            commission_amount REAL NOT NULL,
            transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            user_email TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            service_type TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Add new columns if they don't exist
    try:
        c.execute("ALTER TABLE vendors ADD COLUMN account_status TEXT DEFAULT 'active'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN break_start_date TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN break_end_date TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN break_reason TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

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

# Utility function to recalculate inventory from batches
def recalculate_inventory(conn, product_id=None):
    c = conn.cursor()
    if product_id:
        # Recalculate for specific product
        c.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(remaining_quantity), 0) 
                FROM inventory_batches 
                WHERE product_id = products.id
            )
            WHERE id = ?
        """, (product_id,))
    else:
        # Recalculate for all products
        c.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(remaining_quantity), 0) 
                FROM inventory_batches 
                WHERE product_id = products.id
            )
        """)
    conn.commit()

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
            "image_url": image_url or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400&h=400&fit=crop&crop=face"
        }

        return redirect(url_for("vendor_login"))

    return render_template("vendor_register.html")


# Dashboard
@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    pets = db.get(f"pets:{email}", [])
    return render_template("dashboard.html", email=email, pets=pets)

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
@app.route('/services/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    user_city = "Trivandrum"  # Hardcoded for now
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all groomers/boarding services in the same city that are ONLINE and ACTIVE
    c.execute("""
        SELECT * FROM vendors 
        WHERE (LOWER(category) LIKE '%groom%' OR LOWER(category) LIKE '%salon%' OR LOWER(category) LIKE '%spa%' OR LOWER(category) LIKE '%boarding%')
        AND LOWER(city) = LOWER(?)
        AND is_online = 1
        AND (account_status IS NULL OR account_status = 'active')
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
@app.route('/vendor/<vendor_id>', methods=["GET", "POST"])
def vendor_profile(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # Handle static demo vendor "fluffy-paws"
    if vendor_id == "fluffy-paws":
        vendor = {
            "id": "fluffy-paws",
            "name": "Fluffy Paws Grooming",
            "description": "Expert grooming services for dogs and cats. Professional, caring, and experienced team.",
            "image": "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=600&h=400&fit=crop",
            "city": "Trivandrum",
            "is_online": True,
            "rating": 5.0,
            "level": 15,
            "xp": 2850,
            "total_reviews": 24,
            "success_rate": 95.8,
            "services": ["Full Grooming", "Nail Trimming", "Ear Cleaning", "Teeth Cleaning", "Flea Treatment"],
            "booking_url": f"/vendor/{vendor_id}/book",
            "market_url": f"/marketplace/vendor/{vendor_id}"
        }

        # Static demo reviews
        reviews = [
            ("1", "fluffy-paws", 5, "Amazing service! My dog looks fantastic.", "Grooming", "user@example.com", "2024-01-15"),
            ("2", "fluffy-paws", 4, "Great experience, very professional staff.", "Grooming", "another@example.com", "2024-01-10"),
            ("3", "fluffy-paws", 5, "Best grooming service in town!", "Grooming", "happy@example.com", "2024-01-05")
        ]

        return render_template("vendor_profile.html", vendor=vendor, reviews=reviews)

    if request.method == "POST":
        # Handle review submission for database vendors
        user_email = session["user"]
        rating = int(request.form.get("rating"))
        review_text = request.form.get("review_text", "")
        service_type = request.form.get("service_type", "Other")

        conn = sqlite3.connect("erp.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO reviews (vendor_id, user_email, rating, review_text, service_type)
            VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, user_email, rating, review_text, service_type))
        conn.commit()
        conn.close()

        return redirect(url_for("vendor_profile", vendor_id=vendor_id))

    try:
        conn = sqlite3.connect("erp.db")
        c = conn.cursor()
        c.execute("SELECT id, name, bio, image_url, city, is_online FROM vendors WHERE id = ?", (vendor_id,))
        data = c.fetchone()

        if data:
            vendor_id_db = data[0]

            # Calculate dynamic stats from reviews
            c.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE vendor_id = ?", (vendor_id_db,))
            review_stats = c.fetchone()
            avg_rating = round(review_stats[0], 1) if review_stats[0] else 0
            total_reviews = review_stats[1] or 0

            # Calculate success rate (reviews with 4+ stars)
            c.execute("SELECT COUNT(*) FROM reviews WHERE vendor_id = ? AND rating >= 4", (vendor_id_db,))
            good_reviews = c.fetchone()[0] or 0
            success_rate = round((good_reviews / total_reviews * 100), 1) if total_reviews > 0 else 100

            # Calculate level based on total reviews (every 10 reviews = 1 level)
            level = min(1 + (total_reviews // 10), 20)  # Cap at level 20
            xp = total_reviews * 100  # 100 XP per review

            vendor = {
                "id": data[0],
                "name": data[1],
                "description": data[2] or "Trusted pet care provider.",
                "image": data[3] or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=600&h=400&fit=crop&crop=face",
                "city": data[4] or "Unknown",
                "is_online": data[5],
                "rating": avg_rating,
                "level": level,
                "xp": xp,
                "total_reviews": total_reviews,
                "success_rate": success_rate,
                "services": ["Pet Grooming", "Pet Care", "Professional Services"],
                "booking_url": f"/vendor/{data[0]}/book",
                "market_url": f"/marketplace/vendor/{data[0]}"
            }

            # Get reviews for this vendor
            c.execute("""
                SELECT id, vendor_id, rating, review_text, service_type, user_email, timestamp 
                FROM reviews 
                WHERE vendor_id = ? 
                ORDER BY timestamp DESC
            """, (vendor_id_db,))
            reviews = c.fetchall()

            conn.close()
            return render_template("vendor_profile.html", vendor=vendor, reviews=reviews)
        else:
            conn.close()
            return render_template("vendor_placeholder.html", vendor_name="Unknown Vendor")
    except Exception as e:
        print("Error loading vendor:", e)
        return "Error loading vendor profile"

@app.route('/marketplace/vendor/fluffy-paws')
def fluffy_paws_marketplace():
    if "user" not in session:
        return redirect(url_for("login"))

    vendor = {
        "name": "Fluffy Paws Grooming",
        "city": "Trivandrum",
        "bio": "Expert grooming services for dogs and cats. Professional, caring, and experienced team.",
        "is_online": True
    }

    # Static demo products for fluffy-paws
    products = [
        (1, "Premium Dog Shampoo", "Professional grade dog shampoo for all coat types", 25.00, 15, "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400"),
        (2, "Cat Nail Clippers", "Professional stainless steel nail clippers for cats", 15.00, 12, "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"),
        (3, "Pet Brush Set", "Complete grooming brush set for dogs and cats", 22.00, 8, "https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=400"),
        (4, "Flea Treatment Spray", "Effective flea treatment for dogs and cats", 18.00, 20, "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400"),
        (5, "Pet Teeth Cleaning Kit", "Professional dental care kit for pets", 35.00, 6, "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400")
    ]

    return render_template("marketplace_vendor_products.html", vendor=vendor, products=products, vendor_id="fluffy-paws")

# Boarding
@app.route('/boarding')
@app.route('/services/boarding')
def boarding():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("boarding.html", boardings=[], restaurants=[])

# Vets & Pharma
@app.route('/vets')
@app.route('/services/vets')
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

    # Get pet-specific bookings and purchase history
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get bookings for this user
    c.execute("""
        SELECT service, date, time, status 
        FROM bookings 
        WHERE user_email = ? 
        ORDER BY date DESC
    """, (user,))
    pet_bookings = c.fetchall()

    # Get booking history (completed bookings)
    c.execute("""
        SELECT service, date, time, status 
        FROM bookings 
        WHERE user_email = ? AND status = 'completed'
        ORDER BY date DESC
    """, (user,))
    pet_booking_history = c.fetchall()

    conn.close()

    return render_template("pet_profile.html", breeds=breeds, pets=pets, pet_bookings=pet_bookings, pet_booking_history=pet_booking_history)

@app.route('/set-location')
def set_location():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat and lon:
        session["location"] = {"lat": lat, "lon": lon}
    return '', 204

# Booking route for vendor services
@app.route('/vendor/<vendor_id>/book', methods=["GET", "POST"])
def book_vendor_service(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    # Handle demo vendor
    if vendor_id == "fluffy-paws":
        vendor_name = "Fluffy Paws Grooming"
        services = ["Full Grooming", "Nail Trimming", "Ear Cleaning", "Teeth Cleaning", "Flea Treatment"]

        if request.method == "POST":
            service = request.form.get("service")
            date = request.form.get("date")
            time = request.form.get("time", "10:00")

            # Store booking in database (using vendor_id=0 for demo)
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO bookings (vendor_id, user_email, service, date, time, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (0, user_email, service, date, time, "pending"))
            conn.commit()
            conn.close()

            flash(f"Booking confirmed for {service} on {date}")
            return redirect(url_for("vendor_profile", vendor_id=vendor_id))

        return render_template("booking.html", vendor_name=vendor_name, services=services)

    # Handle database vendors
    try:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM vendors WHERE id = ?", (vendor_id,))
        vendor_data = c.fetchone()
        if vendor_data:
            vendor_name = vendor_data[1]
            services = ["Pet Grooming", "Pet Care", "Consultation", "Health Check"]

            if request.method == "POST":
                service = request.form.get("service")
                date = request.form.get("date")
                time = request.form.get("time", "10:00")

                c.execute("""
                    INSERT INTO bookings (vendor_id, user_email, service, date, time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendor_id, user_email, service, date, time, "pending"))
                conn.commit()
                conn.close()

                flash(f"Booking confirmed for {service} on {date}")
                return redirect(url_for("vendor_profile", vendor_id=vendor_id))

            conn.close()
            return render_template("booking.html", vendor_name=vendor_name, services=services)
        else:
            conn.close()
            return "Vendor not found", 404
    except Exception as e:
        return f"Error: {e}", 500

# Review submission route
@app.route('/vendor/<int:vendor_id>/review', methods=["POST"])
def submit_review(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    rating = int(request.form.get("rating"))
    review_text = request.form.get("review_text", "")
    service_type = request.form.get("service_type", "Other")

    conn = sqlite3.connect("erp.db")
    c = conn.cursor()

    # Check if user already reviewed this vendor
    c.execute("SELECT id FROM reviews WHERE vendor_id = ? AND user_email = ?", (vendor_id, user_email))
    existing_review = c.fetchone()

    if existing_review:
        # Update existing review
        c.execute("""
            UPDATE reviews 
            SET rating = ?, review_text = ?, service_type = ?, timestamp = CURRENT_TIMESTAMP
            WHERE vendor_id = ? AND user_email = ?
        """, (rating, review_text, service_type, vendor_id, user_email))
    else:
        # Insert new review
        c.execute("""
            INSERT INTO reviews (vendor_id, user_email, rating, review_text, service_type)
            VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, user_email, rating, review_text, service_type))

    conn.commit()
    conn.close()

    return redirect(url_for("vendor_profile", vendor_id=vendor_id))

# Booking status update route for vendors
@app.route('/erp/bookings/update/<int:booking_id>', methods=["POST"])
def update_booking_status(booking_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    new_status = request.form.get("status")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Verify the booking belongs to this vendor
    c.execute("""
        UPDATE bookings 
        SET status = ? 
        WHERE id = ? AND vendor_id = (SELECT id FROM vendors WHERE email = ?)
    """, (new_status, booking_id, email))

    conn.commit()
    conn.close()

    flash(f"Booking status updated to {new_status}")
    return redirect(url_for("erp_bookings"))

# User booking tracking route
@app.route('/my-bookings')
def my_bookings():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all bookings for this user with vendor info
    c.execute("""
        SELECT b.id, b.service, b.date, b.time, b.status, v.name as vendor_name, v.phone
        FROM bookings b
        JOIN vendors v ON b.vendor_id = v.id
        WHERE b.user_email = ?
        ORDER BY b.date DESC, b.time DESC
    """, (user_email,))
    bookings = c.fetchall()

    conn.close()
    return render_template("my_bookings.html", bookings=bookings)

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

        # Check for admin login
        if email == "admin@furrbutler.com" and password == "admin123":
            session["master_admin"] = True
            return redirect(url_for("master_admin_dashboard"))

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
            conn.close()
            return "Vendor already exists with that email."

    return render_template("vendor_register.html")

@app.route('/erp/reports/inventory-analytics')
def inventory_analytics():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return render_template("inventory_analytics.html", 
                             analytics={}, 
                             product_analytics=[], 
                             recommendations=[],
                             turnover_months=[],
                             turnover_data=[])

    vendor_id = result[0]

    # Calculate overall analytics
    analytics = calculate_inventory_analytics(c, vendor_id)

    # Calculate product-specific analytics
    product_analytics = calculate_product_analytics(c, vendor_id)

    # Generate recommendations
    recommendations = generate_inventory_recommendations(analytics, product_analytics)

    # Get turnover trend data for chart
    turnover_months, turnover_data = get_turnover_trends(c, vendor_id)

    conn.close()

    return render_template("inventory_analytics.html", 
                         analytics=analytics,
                         product_analytics=product_analytics,
                         recommendations=recommendations,
                         turnover_months=turnover_months,
                         turnover_data=turnover_data)

def calculate_inventory_analytics(c, vendor_id):
    """Calculate overall inventory analytics"""

    # Get all products with sales history
    c.execute("""
        SELECT p.id, p.name, p.quantity, p.buy_price, p.sale_price,
               COALESCE(SUM(sl.quantity), 0) as total_sold,
               COALESCE(SUM(sl.total_amount), 0) as total_revenue
        FROM products p
        LEFT JOIN sales_log sl ON p.id = sl.product_id AND sl.sale_date >= date('now', '-365 days')
        WHERE p.vendor_id = ?
        GROUP BY p.id, p.name, p.quantity, p.buy_price, p.sale_price
    """, (vendor_id,))
    products = c.fetchall()

    total_inventory_value = 0
    total_holding_cost = 0
    total_turnover = 0
    products_count = 0
    products_need_restock = 0

    for product in products:
        product_id, name, stock, buy_price, sale_price, total_sold, revenue = product

        # Inventory value
        inventory_value = stock * (buy_price or 0)
        total_inventory_value += inventory_value

        # Holding cost (25% of inventory value annually)
        holding_cost = inventory_value * 0.25
        total_holding_cost += holding_cost

        # Turnover rate (COGS / Average Inventory)
        if stock > 0 and buy_price:
            avg_inventory = inventory_value
            cogs = total_sold * (buy_price or 0)
            turnover = cogs / avg_inventory if avg_inventory > 0 else 0
            total_turnover += turnover
            products_count += 1

        # Safety stock calculation
        safety_stock = calculate_safety_stock(total_sold, 365)
        if stock < safety_stock:
            products_need_restock += 1

    avg_turnover = total_turnover / products_count if products_count > 0 else 0

    # Health score based on various factors
    health_score = calculate_health_score(avg_turnover, products_need_restock, products_count)

    return {
        'total_inventory_value': total_inventory_value,
        'total_holding_cost': total_holding_cost,
        'avg_turnover': avg_turnover,
        'products_need_restock': products_need_restock,
        'health_score': health_score
    }

def calculate_product_analytics(c, vendor_id):
    """Calculate analytics for each product"""

    c.execute("""
        SELECT p.id, p.name, p.quantity, p.buy_price, p.sale_price,
               COALESCE(SUM(sl.quantity), 0) as total_sold_year,
               COALESCE(SUM(CASE WHEN sl.sale_date >= date('now', '-30 days') THEN sl.quantity ELSE 0 END), 0) as sold_last_month,
               COALESCE(SUM(CASE WHEN sl.sale_date >= date('now', '-7 days') THEN sl.quantity ELSE 0 END), 0) as sold_last_week
        FROM products p
        LEFT JOIN sales_log sl ON p.id = sl.product_id AND sl.sale_date >= date('now', '-365 days')
        WHERE p.vendor_id = ?
        GROUP BY p.id, p.name, p.quantity, p.buy_price, p.sale_price
        ORDER BY p.name
    """, (vendor_id,))

    products = c.fetchall()
    product_analytics = []

    for product in products:
        product_id, name, stock, buy_price, sale_price, sold_year, sold_month, sold_week = product

        # Calculate key metrics
        daily_demand = sold_year / 365 if sold_year > 0 else 0

        # Safety stock (lead time demand + buffer)
        lead_time_days = 7  # Assume 7 days lead time
        demand_variance = max(sold_week - (daily_demand * 7), 0)
        safety_stock = int((lead_time_days * daily_demand) + (1.65 * demand_variance))  # 95% service level

        # Reorder point
        reorder_point = int((lead_time_days * daily_demand) + safety_stock)

        # Turnover rate
        if stock > 0 and buy_price:
            inventory_value = stock * buy_price
            cogs = sold_year * (buy_price or 0)
            turnover_rate = cogs / inventory_value if inventory_value > 0 else 0
        else:
            turnover_rate = 0

        # Holding cost (25% annually)
        holding_cost = (stock * (buy_price or 0)) * 0.25

        # Determine status
        if stock < safety_stock:
            status = "RESTOCK NEEDED"
            status_class = "critical"
            action = f"Order {reorder_point - stock} units"
        elif stock < reorder_point:
            status = "LOW STOCK"
            status_class = "warning"
            action = f"Consider ordering {reorder_point - stock} units"
        else:
            status = "OPTIMAL"
            status_class = "good"
            action = None

        product_analytics.append({
            'id': product_id,
            'name': name,
            'current_stock': stock,
            'safety_stock': max(safety_stock, 1),
            'reorder_point': max(reorder_point, 1),
            'turnover_rate': turnover_rate,
            'holding_cost': holding_cost,
            'status': status,
            'status_class': status_class,
            'action': action,
            'daily_demand': daily_demand
        })

    return product_analytics

def calculate_safety_stock(annual_demand, days_in_period):
    """Calculate safety stock based on demand variability"""
    if annual_demand == 0:
        return 1

    daily_demand = annual_demand / days_in_period
    # Simple safety stock calculation - can be enhanced with more sophisticated models
    return max(int(daily_demand * 7), 1)  # 7 days of average demand

def calculate_health_score(avg_turnover, restock_needed, total_products):
    """Calculate overall inventory health score"""
    if total_products == 0:
        return 100

    # Base score
    score = 100

    # Penalize low turnover
    if avg_turnover < 2:
        score -= 30
    elif avg_turnover < 4:
        score -= 15

    # Penalize products needing restock
    restock_penalty = (restock_needed / total_products) * 40
    score -= restock_penalty

    return max(score, 0)

def generate_inventory_recommendations(analytics, product_analytics):
    """Generate smart inventory recommendations"""
    recommendations = []

    # Low turnover recommendation
    if analytics['avg_turnover'] < 4:
        recommendations.append({
            'title': 'Improve Inventory Turnover',
            'description': 'Your average turnover is below optimal. Consider promotional pricing or adjusting purchase quantities.',
            'color': '#ffc107',
            'bg_color': '#fff3cd'
        })

    # High holding costs
    if analytics['total_holding_cost'] > 10000:
        recommendations.append({
            'title': 'Reduce Holding Costs',
            'description': 'High inventory carrying costs detected. Consider just-in-time ordering or clearance sales.',
            'color': '#dc3545',
            'bg_color': '#f8d7da'
        })

    # Restock alerts
    if analytics['products_need_restock'] > 0:
        recommendations.append({
            'title': 'Urgent Restocking Required',
            'description': f"{analytics['products_need_restock']} products are below safety stock levels. Review reorder recommendations.",
            'color': '#dc3545',
            'bg_color': '#f8d7da'
        })

    # Good performance
    if analytics['health_score'] > 80:
        recommendations.append({
            'title': 'Excellent Inventory Management',
            'description': 'Your inventory health is excellent! Continue monitoring turnover rates and stock levels.',
            'color': '#28a745',
            'bg_color': '#d4edda'
        })

    return recommendations

def get_turnover_trends(c, vendor_id):
    """Get monthly turnover trends for charting"""
    c.execute("""
        SELECT strftime('%Y-%m', sl.sale_date) as month,
               SUM(sl.quantity * p.buy_price) as cogs,
               AVG(p.quantity * p.buy_price) as avg_inventory
        FROM sales_log sl
        JOIN products p ON sl.product_id = p.id
        WHERE p.vendor_id = ? AND sl.sale_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', sl.sale_date)
        ORDER BY month
    """, (vendor_id,))

    data = c.fetchall()
    months = []
    turnover_rates = []

    for row in data:
        month, cogs, avg_inventory = row
        turnover = (cogs / avg_inventory) if avg_inventory > 0 else 0
        months.append(month)
        turnover_rates.append(round(turnover, 1))

    return months, turnover_rates

# The code fixes an incomplete try-except block in the erp_register function.
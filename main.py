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
@app.route('/services/groomers')
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
                "image": data[3] or "https://images.unsplash.com/photo-1558788353-f76d92427f16?w=600&h=400&fit=crop",
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

    # Get vendor details
    c.execute("SELECT id, name, email, phone, bio, image_url, city, latitude, longitude, category FROM vendors WHERE email=?", (email,))
    vendor_data = c.fetchone()

    if vendor_data:
        vendor_id = vendor_data[0]

        # Calculate dynamic stats from reviews
        c.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE vendor_id = ?", (vendor_id,))
        review_stats = c.fetchone()
        avg_rating = round(review_stats[0], 1) if review_stats[0] else 0
        total_reviews = review_stats[1] or 0

        # Calculate success rate (reviews with 4+ stars)
        c.execute("SELECT COUNT(*) FROM reviews WHERE vendor_id = ? AND rating >= 4", (vendor_id,))
        good_reviews = c.fetchone()[0] or 0
        success_rate = round((good_reviews / total_reviews * 100), 1) if total_reviews > 0 else 100

        # Get total orders from bookings and sales
        c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id = ?", (vendor_id,))
        total_bookings = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM sales_log WHERE vendor_id = ?", (vendor_id,))
        total_sales = c.fetchone()[0] or 0

        total_orders = total_bookings + total_sales

        vendor_stats = {
            "rating": avg_rating,
            "total_reviews": total_reviews,
            "total_orders": total_orders,
            "success_rate": success_rate
        }
    else:
        vendor_stats = {"rating": 0, "total_reviews": 0, "total_orders": 0, "success_rate": 100}

    conn.close()

    return render_template("erp_profile_view.html", 
                         vendor=vendor_data or (0, email, email, "", "", "", "", "", "", ""),
                         stats=vendor_stats)

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
    # First recalculate inventory to ensure accuracy
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if vendor_result:
        # Recalculate inventory for this vendor's products
        c.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(ib.remaining_quantity), 0) 
                FROM inventory_batches ib 
                WHERE ib.product_id = products.id
            )
            WHERE vendor_id = ?
        """, (vendor_result[0],))
        conn.commit()

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

        # Also insert into inventory_batches for tracking
        c.execute("""
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        """, (product_id, quantity, buy_price, quantity))

        # Update product quantity from all batches
        c.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(remaining_quantity), 0) 
                FROM inventory_batches 
                WHERE product_id = ?
            )
            WHERE id = ?
        """, (product_id, product_id))

        conn.commit()
        conn.close()
        flash("Product added successfully!")
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

    # Check if vendor exists in SQLite database
    c.execute("SELECT is_online FROM vendors WHERE email=?", (email,))
    current_status = c.fetchone()

    if current_status is None:
        # Vendor doesn't exist in SQLite, get their info from Replit db and create them
        vendor_key = f"vendor:{email}"
        vendor_data = db.get(vendor_key)

        if vendor_data:
            # Create vendor in SQLite database
            c.execute('''
                INSERT INTO vendors (name, email, password, category, city, phone, bio, image_url, is_online)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor_data.get("name", ""),
                vendor_data.get("email", email),
                vendor_data.get("password", ""),
                vendor_data.get("category", ""),
                vendor_data.get("city", ""),
                vendor_data.get("phone", ""),
                vendor_data.get("bio", ""),
                vendor_data.get("image_url", ""),
                1  # Set online when first created
            ))
            conn.commit()
            conn.close()
            return redirect(url_for("erp_dashboard"))
        else:
            # Neither system has the vendor, create basic entry
            c.execute('''
                INSERT INTO vendors (name, email, password, is_online)
                VALUES (?, ?, ?, ?)
            ''', (email.split('@')[0], email, "temp_password", 1))
            conn.commit()
            conn.close()
            return redirect(url_for("erp_dashboard"))

    # Vendor exists, toggle their online status
    current_status = current_status[0]
    new_status = 1 if current_status == 0 else 0
    c.execute('''
        UPDATE vendors SET is_online=? WHERE email=?
    ''', (new_status, email))
    conn.commit()
    conn.close()

    return redirect(url_for("erp_dashboard"))

@app.route('/erp/receipts')
def erp_receipts():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()

    if vendor_result is None:
        conn.close()
        return render_template("erp_receipts.html", receipts=[], bookings=[], sales=[])

    vendor_id = vendor_result[0]

    # Get all receipts for this vendor's bookings
    c.execute("""
        SELECT r.id, r.booking_id, r.amount, r.paid_on, r.payment_mode,
               b.user_email, b.service, b.date, b.time, b.status
        FROM receipts r
        JOIN bookings b ON r.booking_id = b.id
        WHERE b.vendor_id = ?
        ORDER BY r.paid_on DESC
    """, (vendor_id,))
    receipts = c.fetchall()

    # Get all bookings for this vendor
    c.execute("""
        SELECT id, user_email, service, date, time, duration, status
        FROM bookings
        WHERE vendor_id = ?
        ORDER BY date DESC
    """, (vendor_id,))
    bookings = c.fetchall()

    # Get all sales for this vendor
    c.execute("""
        SELECT sl.id, sl.quantity, sl.unit_price, sl.total_amount, 
               sl.customer_email, sl.sale_date, p.name as product_name
        FROM sales_log sl
        JOIN products p ON sl.product_id = p.id
        WHERE sl.vendor_id = ?
        ORDER BY sl.sale_date DESC
    """, (vendor_id,))
    sales = c.fetchall()

    conn.close()
    return render_template("erp_receipts.html", receipts=receipts, bookings=bookings, sales=sales)

@app.route('/erp/logout')
def erp_logout():
    session.pop("vendor", None)
    return redirect(url_for("erp_login"))

# ---- ACCOUNTING & REPORTING ROUTES ----

@app.route('/erp/reports')
def accounting_dashboard():
    # Check if user is logged in as vendor
    if "vendor" not in session:
        # If not logged in as vendor, redirect to vendor login
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()

    if vendor_result is None:
        # If vendor doesn't exist in database, still show dashboard with zero stats
        stats = {
            'total_sales': 0,
            'total_expenses': 0,
            'net_profit': 0,
            'total_products': 0,
            'total_inventory': 0
        }
        conn.close()
        return render_template("accounting_dashboard.html", stats=stats)

    vendor_id = vendor_result[0]

    # Quick stats - use COALESCE to handle null values
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_sales = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    total_expenses = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM products WHERE vendor_id=?", (vendor_id,))
    total_products = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(quantity), 0) FROM products WHERE vendor_id=?", (vendor_id,))
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
        return redirect(url_for("vendor_login"))

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
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        # Show P&L with zero values if vendor not found
        pnl_data = {
            'revenue': 0,
            'cogs': 0,
            'gross_profit': 0,
            'expenses': 0,
            'platform_fees': 0,
            'net_profit': 0
        }
        conn.close()
        return render_template("profit_loss.html", pnl=pnl_data)

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
        return redirect(url_for("vendor_login"))

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
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        # Show empty expenses page if vendor not found
        conn.close()
        return render_template("manage_expenses.html", expenses=[])

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
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        # Show settings page with default values if vendor not found
        conn.close()
        return render_template("accounting_settings.html", settings=None)

    vendor_id = result[0]

    if request.method == "POST":
        gst_rate = float(request.form.get("gst_rate", 18.0))
        razorpay_enabled = 1 if request.form.get("razorpay_enabled") else 0
        cod_enabled = 1 if request.form.get("cod_enabled") else 0
        auto_reports = 1 if request.form.get("auto_reports") else 0

        # Delivery pricing settings
        standard_delivery = float(request.form.get("standard_delivery_price", 2.99))
        express_delivery = float(request.form.get("express_delivery_price", 5.99))
        same_day_delivery = float(request.form.get("same_day_delivery_price", 12.99))
        free_delivery_threshold = float(request.form.get("free_delivery_threshold", 50.00))

        # Get current platform commission from master settings (not editable by vendor)
        c.execute("SELECT setting_value FROM master_settings WHERE setting_name = 'platform_commission_rate'")
        platform_fee_result = c.fetchone()
        platform_fee = platform_fee_result[0] if platform_fee_result else 10.0

        # Insert or update settings
        c.execute("""
            INSERT OR REPLACE INTO settings_vendor 
            (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports, 
             standard_delivery_price, express_delivery_price, same_day_delivery_price, free_delivery_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports,
              standard_delivery, express_delivery, same_day_delivery, free_delivery_threshold))

        conn.commit()
        flash("Settings updated successfully!")
        return redirect(url_for("accounting_settings"))

    # Get current settings
    c.execute("SELECT * FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    settings = c.fetchone()

    conn.close()
    return render_template("accounting_settings.html", settings=settings)

@app.route('/erp/reports/sales')
def sales_analytics():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        # Show empty sales analytics if vendor not found
        conn.close()
        return render_template("sales_analytics.html", 
                             sales=[], 
                             monthly_summary=[], 
                             top_products=[])

    vendor_id = result[0]

    # Get sales data
    c.execute("""
        SELECT sl.*, p.name as product_name 
        FROM sales_log sl 
        JOIN products p ON sl.product_id = p.id 
        WHERE sl.vendor_id=? 
        ORDER BY sl.sale_date DESC
    """, (vendor_id,))
    sales = c.fetchall()

    # Get monthly sales summary
    c.execute("""
        SELECT strftime('%Y-%m', sale_date) as month, 
               COUNT(*) as total_orders,
               SUM(total_amount) as total_revenue,
               SUM(quantity) as total_units
        FROM sales_log 
        WHERE vendor_id=? 
        GROUP BY strftime('%Y-%m', sale_date)
        ORDER BY month DESC
    """, (vendor_id,))
    monthly_summary = c.fetchall()

    # Top selling products
    c.execute("""
        SELECT p.name, SUM(sl.quantity) as total_sold, SUM(sl.total_amount) as total_revenue
        FROM sales_log sl 
        JOIN products p ON sl.product_id = p.id 
        WHERE sl.vendor_id=?
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 10
    """, (vendor_id,))
    top_products = c.fetchall()

    conn.close()

    return render_template("sales_analytics.html", 
                         sales=sales, 
                         monthly_summary=monthly_summary, 
                         top_products=top_products)

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

@app.route('/checkout')
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("checkout.html")

# Master Admin Routes (Platform Owner)
@app.route('/master/admin/login', methods=["GET", "POST"])
def master_admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Hardcoded admin credentials (in production, use proper authentication)
        if username == "furrbutler_admin" and password == "admin123":
            session["master_admin"] = True
            return redirect(url_for("master_admin_dashboard"))
        else:
            flash("Invalid admin credentials")

    return render_template("master_admin_login.html")

@app.route('/master/admin/dashboard')
def master_admin_dashboard():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get current master settings
    c.execute("SELECT * FROM master_settings ORDER BY setting_name")
    settings = c.fetchall()

    # Get platform statistics
    c.execute("SELECT COUNT(*) FROM vendors")
    total_vendors = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log")
    total_sales = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(fee_amount), 0) FROM platform_fees")
    total_commission = c.fetchone()[0]

    # Get platform earnings
    c.execute("SELECT COALESCE(SUM(commission_amount), 0) FROM platform_earnings")
    platform_earnings = c.fetchone()[0]

    # Get earnings breakdown by service type
    c.execute("""
        SELECT service_type, 
               COALESCE(SUM(commission_amount), 0) as earnings,
               COUNT(*) as transactions
        FROM platform_earnings 
        GROUP BY service_type
    """)
    earnings_breakdown = c.fetchall()

    # Get recent transactions for admin view
    c.execute("""
        SELECT pe.*, v.name as vendor_name
        FROM platform_earnings pe
        JOIN vendors v ON pe.vendor_id = v.id
        ORDER BY pe.transaction_date DESC
        LIMIT 10
    """)
    recent_transactions = c.fetchall()

    conn.close()

    stats = {
        'total_vendors': total_vendors,
        'total_products': total_products,
        'total_sales': total_sales,
        'total_commission': total_commission,
        'platform_earnings': platform_earnings,
        'earnings_breakdown': earnings_breakdown,
        'recent_transactions': recent_transactions
    }

    return render_template("master_admin_dashboard.html", settings=settings, stats=stats)

@app.route('/master/admin/update-commission', methods=["POST"])
def update_commission():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))

    marketplace_platform_fee = float(request.form.get("marketplace_platform_fee", 2.99))
    grooming_commission = float(request.form.get("grooming_commission_rate", 15.0))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Update master settings - marketplace uses fixed platform fee, grooming uses commission
    c.execute("""
        UPDATE master_settings 
        SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE setting_name = 'marketplace_listing_fee'
    """, (marketplace_platform_fee,))

    c.execute("""
        UPDATE master_settings 
        SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE setting_name = 'grooming_commission_rate'
    """, (grooming_commission,))

    conn.commit()
    conn.close()

    flash(f"Settings updated: Marketplace Platform Fee ${marketplace_platform_fee}, Grooming Commission {grooming_commission}%")
    return redirect(url_for("master_admin_dashboard"))

@app.route('/master/admin/update-settings', methods=["POST"])
def update_platform_settings():
    if not session.get("master_admin"):
        return {"success": False, "message": "Unauthorized"}, 403

    try:
        settings_data = request.get_json()

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        for setting_name, new_value in settings_data.items():
            # Update setting with previous value tracking
            c.execute("""
                UPDATE master_settings 
                SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE setting_name = ?
            """, (new_value, setting_name))

        conn.commit()
        conn.close()

        return {"success": True, "message": "Settings updated successfully"}

    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/master/admin/logout')
def master_admin_logout():
    session.pop("master_admin", None)
    flash("You have been logged out successfully")
    return redirect(url_for("home"))

# Add route to get vendor's delivery prices for checkout
@app.route('/api/vendor/<int:vendor_id>/delivery-prices')
def get_vendor_delivery_prices(vendor_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("""
        SELECT standard_delivery_price, express_delivery_price, same_day_delivery_price, free_delivery_threshold
        FROM settings_vendor 
        WHERE vendor_id = ?
    """, (vendor_id,))

    result = c.fetchone()
    conn.close()

    if result:
        return {
            'standard': result[0] or 2.99,
            'express': result[1] or 5.99,
            'same_day': result[2] or 12.99,
            'free_threshold': result[3] or 50.00
        }
    else:
        return {
            'standard': 2.99,
            'express': 5.99,
            'same_day': 12.99,
            'free_threshold': 50.00
        }

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)
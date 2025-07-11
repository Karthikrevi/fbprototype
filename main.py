from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from replit import db
import os
import json
from werkzeug.utils import secure_filename
from math import radians, cos, sin, asin, sqrt
import sqlite3
from datetime import datetime
import hashlib

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
            pet_name TEXT,
            pet_parent_name TEXT,
            pet_parent_phone TEXT,
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

    # Chatbot system tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            vendor_email TEXT,
            query TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            response TEXT,
            feedback INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            intent TEXT NOT NULL,
            response TEXT,
            is_validated INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            vendor_email TEXT NOT NULL,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
            query_count INTEGER DEFAULT 0
        )
    ''')

    # Chat system tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            user_email TEXT,
            last_message_time TEXT DEFAULT CURRENT_TIMESTAMP,
            vendor_unread_count INTEGER DEFAULT 0,
            user_unread_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            sender_type TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            message_type TEXT DEFAULT 'text',
            FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id)
        )
    ''')

    # Pet Passport System tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS passport_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL CHECK(doc_type IN ('microchip', 'vaccine', 'health_cert', 'dgft', 'aqcs', 'quarantine')),
            uploaded_by_role TEXT NOT NULL CHECK(uploaded_by_role IN ('parent', 'vet', 'handler', 'isolation')),
            uploaded_by_user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            upload_time TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            comments TEXT,
            is_signed BOOLEAN DEFAULT 0,
            doc_hash TEXT,
            signature_timestamp TEXT,
            vet_id INTEGER,
            dgft_reference TEXT
        )
    ''')

    # Add missing columns to passport_documents table if they don't exist
    try:
        c.execute("ALTER TABLE passport_documents ADD COLUMN is_signed BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE passport_documents ADD COLUMN doc_hash TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE passport_documents ADD COLUMN signature_timestamp TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE passport_documents ADD COLUMN vet_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE passport_documents ADD COLUMN dgft_reference TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # FurrWings role-specific tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS vets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            license_number TEXT NOT NULL,
            phone TEXT,
            clinic_name TEXT,
            city TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS handlers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            company_name TEXT NOT NULL,
            license_number TEXT,
            phone TEXT,
            city TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS isolation_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            center_name TEXT NOT NULL,
            license_number TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            uploaded_by_role TEXT NOT NULL,
            uploaded_by_user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            media_type TEXT NOT NULL CHECK(media_type IN ('photo', 'video')),
            upload_time TEXT DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            booking_type TEXT NOT NULL CHECK(booking_type IN ('isolation', 'quarantine')),
            center_id INTEGER,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'in_progress', 'completed', 'rejected')),
            check_in_date TEXT,
            check_out_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (center_id) REFERENCES isolation_centers(id)
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

    # Add pet parent information columns to bookings table
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN pet_name TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE bookings ADD COLUMN pet_parent_name TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE bookings ADD COLUMN pet_parent_phone TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Insert demo vendor
    c.execute('''
        INSERT OR IGNORE INTO vendors (name, email, password, category, city, latitude, longitude, is_online)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Demo Groomer", "demo@furrbutler.com", "demo123", "Groomer", "Trivandrum", 8.5241, 76.9366, 1))

    # Insert demo FurrWings users
    c.execute('''
        INSERT OR IGNORE INTO vets (name, email, password, license_number, phone, clinic_name, city)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("Dr. Kavya Sharma", "vet@furrwings.com", "vet123", "KL-1324", "+91-9876543210", "PetCare Clinic", "Trivandrum"))

    c.execute('''
        INSERT OR IGNORE INTO handlers (name, email, password, company_name, license_number, phone, city)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("Global Paws Handler", "handler@furrwings.com", "handler123", "Global Paws Pvt Ltd", "DGFT-2024-001", "+91-9876543211", "Trivandrum"))

    c.execute('''
        INSERT OR IGNORE INTO isolation_centers (name, email, password, center_name, license_number, phone, address, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Bark & Board Manager", "isolation@furrwings.com", "isolation123", "Bark & Board Isolation Center", "ISO-2024-001", "+91-9876543212", "123 Pet Street", "Trivandrum"))

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
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup for photo uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Utility to check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# F-DSC Digital Signature System
def generate_fdsc_signature(file_bytes, user_id, user_type, license_number):
    """Generate F-DSC (FurrButler Digital Signature Certificate) for documents"""
    timestamp = datetime.now().isoformat()
    signature_data = file_bytes + user_id.encode() + timestamp.encode() + license_number.encode()
    doc_hash = hashlib.sha256(signature_data).hexdigest()
    
    return {
        'doc_hash': doc_hash,
        'timestamp': timestamp,
        'user_id': user_id,
        'user_type': user_type,
        'license_number': license_number
    }

def create_signature_file(signature_info, filepath, user_name, user_type):
    """Create .sig.txt file with signature information"""
    sig_filepath = filepath + '.sig.txt'
    
    disclaimer = """
This digital signature is valid within the FurrButler ecosystem. It is not certified under the Indian IT Act, 2000. 
For export validation, documents are submitted via certified authorities or partner handlers. 
This system ensures document traceability, tamper protection, and identity verification within the FurrWings network.
"""
    
    signature_content = f"""FurrButler Digital Signature Certificate (F-DSC)
================================================================

Document Hash: {signature_info['doc_hash']}
Signed By: {user_name}
User Type: {user_type.upper()}
License/ID: {signature_info['license_number']}
F-DSC ID: FDSC-{signature_info['user_type'].upper()}-{signature_info['license_number'][-4:]}
Timestamp: {signature_info['timestamp']}
DSC Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DISCLAIMER:
{disclaimer}

Verification URL: /verify/document/{signature_info['doc_hash']}
"""
    
    with open(sig_filepath, 'w') as f:
        f.write(signature_content)
    
    return sig_filepath

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

        # Check SQLite database first
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vendors WHERE email=? AND password=?", (email, password))
        vendor = c.fetchone()
        conn.close()

        if vendor:
            session["vendor"] = email
            return redirect(url_for("erp_dashboard"))
        else:
            # Fallback to old Replit database for backward compatibility
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
                "image": data[3] or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=600&h=400&fit=crop=face",
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
@app.route('/pet-profile')
def pet_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])

    return render_template("pet_profile.html", pets=pets)

@app.route('/add-pet', methods=["GET", "POST"])
def add_pet():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        user = session["user"]
        pets = db.get(f"pets:{user}", [])
        
        name = request.form.get("name")
        parent_name = request.form.get("parent_name")
        parent_phone = request.form.get("parent_phone")
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
            "parent_name": parent_name,
            "parent_phone": parent_phone,
            "birthday": birthday,
            "breed": breed,
            "blood": blood,
            "photo": photo_url
        }

        pets.append(pet)
        db[f"pets:{user}"] = pets
        flash(f"Pet {name} added successfully!")
        return redirect(url_for("pet_profile"))

    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    return render_template("add_pet.html", breeds=breeds)

@app.route('/pet/<int:pet_index>')
def pet_detail(pet_index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])
    
    if pet_index < 0 or pet_index >= len(pets):
        flash("Pet not found!")
        return redirect(url_for("pet_profile"))

    pet = pets[pet_index]

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

    return render_template("pet_detail.html", pet=pet, pet_index=pet_index, pet_bookings=pet_bookings, pet_booking_history=pet_booking_history)

@app.route('/pet/<int:pet_index>/passport')
def pet_passport(pet_index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])
    
    if pet_index < 0 or pet_index >= len(pets):
        flash("Pet not found!")
        return redirect(url_for("pet_profile"))

    pet = pets[pet_index]
    pet_id = pet_index + 1  # Simple ID mapping for now

    # Get passport documents for this pet
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT doc_type, uploaded_by_role, uploaded_by_user_id, filename, upload_time, status, comments
        FROM passport_documents 
        WHERE pet_id = ?
        ORDER BY upload_time DESC
    """, (pet_id,))
    
    documents = c.fetchall()
    conn.close()

    # Organize documents by type
    doc_status = {}
    for doc in documents:
        doc_type = doc[0]
        if doc_type not in doc_status or doc[4] > doc_status[doc_type]['upload_time']:  # Keep latest
            doc_status[doc_type] = {
                'uploaded_by_role': doc[1],
                'uploaded_by_user_id': doc[2],
                'filename': doc[3],
                'upload_time': doc[4],
                'status': doc[5],
                'comments': doc[6]
            }

    # Define required documents and their allowed uploaders
    required_docs = {
        'microchip': {'name': 'Microchip Certificate', 'allowed_roles': ['parent']},
        'vaccine': {'name': 'Vaccination Records', 'allowed_roles': ['vet']},
        'health_cert': {'name': 'Health Certificate', 'allowed_roles': ['vet']},
        'dgft': {'name': 'DGFT Certificate', 'allowed_roles': ['handler']},
        'aqcs': {'name': 'AQCS Certificate', 'allowed_roles': ['handler']},
        'quarantine': {'name': 'Quarantine Clearance', 'allowed_roles': ['handler']}
    }

    # Calculate completion percentage
    completed_docs = sum(1 for doc_type in required_docs.keys() if doc_type in doc_status and doc_status[doc_type]['status'] == 'approved')
    completion_percentage = int((completed_docs / len(required_docs)) * 100)

    # Determine user role (simplified - with role switching for testing)
    user_role = request.args.get('role', 'parent')
    if user_role not in ['parent', 'vet', 'handler']:
        user_role = 'parent'

    return render_template("pet_passport.html", 
                         pet=pet, 
                         pet_index=pet_index,
                         pet_id=pet_id,
                         doc_status=doc_status,
                         required_docs=required_docs,
                         completion_percentage=completion_percentage,
                         user_role=user_role)

@app.route('/pet/<int:pet_index>/edit', methods=["GET", "POST"])
def edit_pet(pet_index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    pets = db.get(f"pets:{user}", [])
    
    if pet_index < 0 or pet_index >= len(pets):
        flash("Pet not found!")
        return redirect(url_for("pet_profile"))

    if request.method == "POST":
        # Update the pet information
        pets[pet_index]["name"] = request.form.get("name")
        pets[pet_index]["parent_name"] = request.form.get("parent_name")
        pets[pet_index]["parent_phone"] = request.form.get("parent_phone")
        pets[pet_index]["birthday"] = request.form.get("birthday")
        pets[pet_index]["breed"] = request.form.get("breed")
        pets[pet_index]["blood"] = request.form.get("blood")

        # Handle photo upload
        file = request.files.get("photo")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            pets[pet_index]["photo"] = "/" + filepath

        # Save updated pets list
        db[f"pets:{user}"] = pets
        flash(f"Pet {pets[pet_index]['name']} updated successfully!")
        return redirect(url_for("pet_detail", pet_index=pet_index))

    pet = pets[pet_index]
    
    # Load dog breeds for the dropdown
    with open("dog_breeds.json", "r") as f:
        breeds = json.load(f)

    return render_template("edit_pet.html", pet=pet, pet_index=pet_index, breeds=breeds)

@app.route('/vet/dashboard')
def vet_dashboard():
    if "vet" not in session:
        return redirect(url_for("vet_login"))

    vet_email = session["vet"]
    vet_id = session["vet_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all pets that need vet documents (simplified - showing all pets for demo)
    c.execute("""
        SELECT DISTINCT pd.pet_id, 
               (SELECT COUNT(*) FROM passport_documents WHERE pet_id = pd.pet_id AND doc_type IN ('vaccine', 'health_cert')) as vet_docs_count
        FROM passport_documents pd
        UNION
        SELECT 1 as pet_id, 0 as vet_docs_count  -- Demo pet Luna
    """)
    
    pets_data = c.fetchall()
    
    # Get vet documents status for each pet
    pets = []
    for pet_data in pets_data:
        pet_id = pet_data[0]
        
        # Get vaccine and health cert status
        c.execute("""
            SELECT doc_type, filename, status, upload_time, is_signed, doc_hash, signature_timestamp
            FROM passport_documents 
            WHERE pet_id = ? AND doc_type IN ('vaccine', 'health_cert') AND uploaded_by_role = 'vet'
            ORDER BY upload_time DESC
        """, (pet_id,))
        
        docs = c.fetchall()
        doc_status = {}
        for doc in docs:
            doc_status[doc[0]] = {
                'filename': doc[1],
                'status': doc[2],
                'upload_time': doc[3],
                'is_signed': doc[4],
                'doc_hash': doc[5],
                'signature_timestamp': doc[6]
            }
        
        pets.append({
            'id': pet_id,
            'name': f'Pet {pet_id}' if pet_id != 1 else 'Luna',
            'doc_status': doc_status
        })

    conn.close()
    return render_template("vet_dashboard.html", pets=pets, vet_name=session["vet_name"])

@app.route('/vet/upload', methods=["POST"])
def vet_upload_document():
    if "vet" not in session:
        return redirect(url_for("vet_login"))

    pet_id = request.form.get("pet_id")
    doc_type = request.form.get("doc_type")
    should_sign = request.form.get("sign_document") == "on"
    
    if doc_type not in ['vaccine', 'health_cert']:
        flash("Vets can only upload vaccine and health certificate documents")
        return redirect(url_for("vet_dashboard"))

    # Handle file upload
    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected")
        return redirect(url_for("vet_dashboard"))

    # Validate file type
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash("Invalid file type. Please upload PDF, JPG, or PNG files only.")
        return redirect(url_for("vet_dashboard"))

    # Create unique filename
    import time
    timestamp = str(int(time.time()))
    original_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"vet_{pet_id}_{doc_type}_{timestamp}.{original_extension}"
    
    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Generate F-DSC signature if requested
    doc_hash = None
    signature_timestamp = None
    is_signed = 0
    
    if should_sign:
        # Read file for signature
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
        
        signature_info = generate_fdsc_signature(
            file_bytes, 
            session["vet"], 
            "vet", 
            session["vet_license"]
        )
        
        doc_hash = signature_info['doc_hash']
        signature_timestamp = signature_info['timestamp']
        is_signed = 1
        
        # Create signature file
        create_signature_file(
            signature_info, 
            filepath, 
            session["vet_name"], 
            "vet"
        )

    # Save to database
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO passport_documents 
        (pet_id, doc_type, uploaded_by_role, uploaded_by_user_id, filename, is_signed, doc_hash, signature_timestamp, vet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, doc_type, "vet", session["vet"], filename, is_signed, doc_hash, signature_timestamp, session["vet_id"]))
    
    conn.commit()
    conn.close()

    if should_sign:
        flash(f"{doc_type.replace('_', ' ').title()} document uploaded and digitally signed with F-DSC!")
    else:
        flash(f"{doc_type.replace('_', ' ').title()} document uploaded successfully!")
    
    return redirect(url_for("vet_dashboard"))

@app.route('/handler/dashboard')
def handler_dashboard():
    if "handler" not in session:
        return redirect(url_for("handler_login"))

    handler_email = session["handler"]
    handler_id = session["handler_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all pets that need handler documents (simplified - showing all pets for demo)
    c.execute("""
        SELECT DISTINCT pd.pet_id, 
               (SELECT COUNT(*) FROM passport_documents WHERE pet_id = pd.pet_id AND doc_type IN ('dgft', 'aqcs', 'quarantine')) as handler_docs_count
        FROM passport_documents pd
        UNION
        SELECT 1 as pet_id, 0 as handler_docs_count  -- Demo pet Luna
    """)
    
    pets_data = c.fetchall()
    
    # Get handler documents status for each pet
    pets = []
    for pet_data in pets_data:
        pet_id = pet_data[0]
        
        # Get DGFT, AQCS, and quarantine docs status
        c.execute("""
            SELECT doc_type, filename, status, upload_time, dgft_reference
            FROM passport_documents 
            WHERE pet_id = ? AND doc_type IN ('dgft', 'aqcs', 'quarantine') AND uploaded_by_role = 'handler'
            ORDER BY upload_time DESC
        """, (pet_id,))
        
        docs = c.fetchall()
        doc_status = {}
        for doc in docs:
            doc_status[doc[0]] = {
                'filename': doc[1],
                'status': doc[2],
                'upload_time': doc[3],
                'dgft_reference': doc[4]
            }
        
        pets.append({
            'id': pet_id,
            'name': f'Pet {pet_id}' if pet_id != 1 else 'Luna',
            'doc_status': doc_status
        })

    conn.close()
    return render_template("handler_dashboard.html", pets=pets, handler_name=session["handler_name"])

@app.route('/handler/upload', methods=["POST"])
def handler_upload_document():
    if "handler" not in session:
        return redirect(url_for("handler_login"))

    pet_id = request.form.get("pet_id")
    doc_type = request.form.get("doc_type")
    dgft_reference = request.form.get("dgft_reference", "")
    
    if doc_type not in ['dgft', 'aqcs', 'quarantine']:
        flash("Handlers can only upload DGFT, AQCS, and quarantine documents")
        return redirect(url_for("handler_dashboard"))

    # Handle file upload
    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected")
        return redirect(url_for("handler_dashboard"))

    # Validate file type
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash("Invalid file type. Please upload PDF, JPG, or PNG files only.")
        return redirect(url_for("handler_dashboard"))

    # Create unique filename
    import time
    timestamp = str(int(time.time()))
    original_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"handler_{pet_id}_{doc_type}_{timestamp}.{original_extension}"
    
    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Mock DGFT API submission for DGFT documents
    if doc_type == 'dgft' and not dgft_reference:
        # Mock API call
        dgft_reference = f"DGFT-{timestamp[-6:]}"

    # Save to database
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO passport_documents 
        (pet_id, doc_type, uploaded_by_role, uploaded_by_user_id, filename, dgft_reference)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pet_id, doc_type, "handler", session["handler"], filename, dgft_reference))
    
    conn.commit()
    conn.close()

    flash(f"{doc_type.upper()} document uploaded successfully!" + (f" Reference: {dgft_reference}" if dgft_reference else ""))
    return redirect(url_for("handler_dashboard"))

@app.route('/isolation/dashboard')
def isolation_dashboard():
    if "isolation" not in session:
        return redirect(url_for("isolation_login"))

    isolation_email = session["isolation"]
    isolation_id = session["isolation_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all pet bookings for this isolation center
    c.execute("""
        SELECT pb.id, pb.pet_id, pb.status, pb.check_in_date, pb.check_out_date, pb.notes,
               COUNT(pm.id) as media_count
        FROM pet_bookings pb
        LEFT JOIN pet_media pm ON pb.pet_id = pm.pet_id
        WHERE pb.center_id = ? AND pb.booking_type = 'isolation'
        GROUP BY pb.id
        ORDER BY pb.created_at DESC
    """, (isolation_id,))
    
    bookings_data = c.fetchall()
    
    bookings = []
    for booking in bookings_data:
        # Get media files for this pet
        c.execute("""
            SELECT filename, media_type, upload_time, description
            FROM pet_media 
            WHERE pet_id = ? AND uploaded_by_role = 'isolation'
            ORDER BY upload_time DESC
        """, (booking[1],))
        
        media_files = c.fetchall()
        
        bookings.append({
            'id': booking[0],
            'pet_id': booking[1],
            'pet_name': f'Pet {booking[1]}' if booking[1] != 1 else 'Luna',
            'status': booking[2],
            'check_in_date': booking[3],
            'check_out_date': booking[4],
            'notes': booking[5],
            'media_count': booking[6],
            'media_files': media_files
        })

    conn.close()
    return render_template("isolation_dashboard.html", bookings=bookings, center_name=session["isolation_name"])

@app.route('/isolation/update-booking', methods=["POST"])
def isolation_update_booking():
    if "isolation" not in session:
        return redirect(url_for("isolation_login"))

    booking_id = request.form.get("booking_id")
    new_status = request.form.get("status")
    notes = request.form.get("notes", "")
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        UPDATE pet_bookings 
        SET status = ?, notes = ?
        WHERE id = ? AND center_id = ?
    """, (new_status, notes, booking_id, session["isolation_id"]))
    
    conn.commit()
    conn.close()
    
    flash(f"Booking status updated to {new_status}")
    return redirect(url_for("isolation_dashboard"))

@app.route('/isolation/upload-media', methods=["POST"])
def isolation_upload_media():
    if "isolation" not in session:
        return redirect(url_for("isolation_login"))

    pet_id = request.form.get("pet_id")
    media_type = request.form.get("media_type")
    description = request.form.get("description", "")
    
    # Handle file upload
    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected")
        return redirect(url_for("isolation_dashboard"))

    # Validate file type based on media type
    if media_type == 'photo':
        allowed_extensions = {'jpg', 'jpeg', 'png'}
    else:  # video
        allowed_extensions = {'mp4', 'mov', 'avi'}
    
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash(f"Invalid file type for {media_type}.")
        return redirect(url_for("isolation_dashboard"))

    # Create unique filename
    import time
    timestamp = str(int(time.time()))
    original_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"isolation_{pet_id}_{media_type}_{timestamp}.{original_extension}"
    
    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Save to database
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO pet_media 
        (pet_id, uploaded_by_role, uploaded_by_user_id, filename, media_type, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pet_id, "isolation", session["isolation"], filename, media_type, description))
    
    conn.commit()
    conn.close()

    flash(f"{media_type.title()} uploaded successfully!")
    return redirect(url_for("isolation_dashboard"))

@app.route('/verify/document/<doc_hash>')
def verify_document(doc_hash):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT pd.*, v.name as vet_name, v.license_number
        FROM passport_documents pd
        LEFT JOIN vets v ON pd.vet_id = v.id
        WHERE pd.doc_hash = ? AND pd.is_signed = 1
    """, (doc_hash,))
    
    document = c.fetchone()
    conn.close()
    
    if not document:
        return render_template("document_verification.html", 
                             verified=False, 
                             message="Document not found or not digitally signed")
    
    return render_template("document_verification.html", 
                         verified=True, 
                         document=document)

@app.route('/passport/upload', methods=["POST"])
def passport_upload():
    if "user" not in session:
        return redirect(url_for("login"))

    pet_id = request.form.get("pet_id")
    pet_index = request.form.get("pet_index")
    doc_type = request.form.get("doc_type")
    user_role = request.form.get("user_role", "parent")  # This would come from actual user role system
    
    if not pet_id or not doc_type:
        flash("Missing required information")
        return redirect(url_for("pet_passport", pet_index=pet_index))

    # Define role permissions
    role_permissions = {
        'microchip': ['parent'],
        'vaccine': ['vet'],
        'health_cert': ['vet'],
        'dgft': ['handler'],
        'aqcs': ['handler'],
        'quarantine': ['handler']
    }

    # Check if user role can upload this document type
    if user_role not in role_permissions.get(doc_type, []):
        flash(f"You don't have permission to upload {doc_type} documents")
        return redirect(url_for("pet_passport", pet_index=pet_index))

    # Handle file upload
    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected")
        return redirect(url_for("pet_passport", pet_index=pet_index))

    # Validate file type
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash("Invalid file type. Please upload PDF, JPG, or PNG files only.")
        return redirect(url_for("pet_passport", pet_index=pet_index))

    # Create unique filename
    import time
    timestamp = str(int(time.time()))
    original_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"pet_{pet_id}_{doc_type}_{timestamp}.{original_extension}"
    
    # Save file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Save to database
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO passport_documents (pet_id, doc_type, uploaded_by_role, uploaded_by_user_id, filename)
        VALUES (?, ?, ?, ?, ?)
    """, (pet_id, doc_type, user_role, session["user"], filename))
    
    conn.commit()
    conn.close()

    flash(f"{doc_type.replace('_', ' ').title()} document uploaded successfully!")
    return redirect(url_for("pet_passport", pet_index=pet_index))

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
            pet_name = request.form.get("pet_name")
            pet_parent_name = request.form.get("pet_parent_name")
            pet_parent_phone = request.form.get("pet_parent_phone")

            # Store booking in database (using vendor_id=0 for demo)
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO bookings (vendor_id, user_email, service, date, time, status, pet_name, pet_parent_name, pet_parent_phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (0, user_email, service, date, time, "pending", pet_name, pet_parent_name, pet_parent_phone))
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
                pet_name = request.form.get("pet_name")
                pet_parent_name = request.form.get("pet_parent_name")
                pet_parent_phone = request.form.get("pet_parent_phone")

                c.execute("""
                    INSERT INTO bookings (vendor_id, user_email, service, date, time, status, pet_name, pet_parent_name, pet_parent_phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (vendor_id, user_email, service, date, time, "pending", pet_name, pet_parent_name, pet_parent_phone))
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
        SELECT b.id, b.service, b.date, b.time, b.status, v.name as vendor_name, v.phone, 
               b.pet_name, b.pet_parent_name, b.pet_parent_phone
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

# ---- FURRWINGS ROLE-BASED LOGIN ROUTES ----

@app.route('/vet/login', methods=["GET", "POST"])
def vet_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vets WHERE email=? AND password=? AND is_active=1", (email, password))
        vet = c.fetchone()
        conn.close()

        if vet:
            session["vet"] = email
            session["vet_id"] = vet[0]
            session["vet_name"] = vet[1]
            session["vet_license"] = vet[3]
            return redirect(url_for("vet_dashboard"))
        else:
            flash("Invalid vet credentials")

    return render_template("vet_login.html")

@app.route('/handler/login', methods=["GET", "POST"])
def handler_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM handlers WHERE email=? AND password=? AND is_active=1", (email, password))
        handler = c.fetchone()
        conn.close()

        if handler:
            session["handler"] = email
            session["handler_id"] = handler[0]
            session["handler_name"] = handler[1]
            session["handler_license"] = handler[5]
            return redirect(url_for("handler_dashboard"))
        else:
            flash("Invalid handler credentials")

    return render_template("handler_login.html")

@app.route('/isolation/login', methods=["GET", "POST"])
def isolation_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM isolation_centers WHERE email=? AND password=? AND is_active=1", (email, password))
        center = c.fetchone()
        conn.close()

        if center:
            session["isolation"] = email
            session["isolation_id"] = center[0]
            session["isolation_name"] = center[1]
            session["isolation_license"] = center[5]
            return redirect(url_for("isolation_dashboard"))
        else:
            flash("Invalid isolation center credentials")

    return render_template("isolation_login.html")

# ---- ERP ROUTES ----

@app.route('/erp')
def erp_home():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    return redirect(url_for("erp_dashboard"))

@app.route('/erp-login')
def erp_login_redirect():
    """Redirect route for /erp-login to unified ERP login page"""
    return render_template("erp_login_unified.html")

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
    c.execute("SELECT id, name, email, phone, bio, image_url, city, latitude, longitude, category, account_status, break_start_date, break_reason FROM vendors WHERE email=?", (email,))
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

        # Get online status
        c.execute("SELECT is_online FROM vendors WHERE id = ?", (vendor_id,))
        online_status = c.fetchone()
        is_online = online_status[0] if online_status else 0

        vendor_stats = {
            "rating": avg_rating,
            "total_reviews": total_reviews,
            "total_orders": total_orders,
            "success_rate": success_rate,
            "is_online": is_online
        }
    else:
        vendor_stats = {"rating": 0, "total_reviews": 0, "total_orders": 0, "success_rate": 100, "is_online": 0}

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

        # Auto-generate barcode if not provided
        if not barcode:
            import time
            barcode = f"FB{vendor_id}{int(time.time())}"

        # Handle image upload
        image_url = ""
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = "/" + filepath

        # Check if barcode already exists (if provided)
        if barcode:
            c.execute("SELECT id FROM products WHERE barcode = ?", (barcode,))
            existing_product = c.fetchone()
            if existing_product:
                conn.close()
                flash(f"Error: Barcode '{barcode}' already exists. Please use a unique barcode.")
                return redirect(url_for("add_product"))

        # Calculate total cost
        total_cost = quantity * buy_price

        # Insert product
        try:
            c.execute("""
                INSERT INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, image_url, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vendor_id, name, description, category, buy_price, sale_price, quantity, image_url, barcode or None))

            product_id = c.lastrowid
        except sqlite3.IntegrityError as e:
            conn.close()
            flash(f"Error adding product: {str(e)}")
            return redirect(url_for("add_product"))

        # Insert batch
        batch_name_final = batch_name or f"BATCH-{barcode}-001"
        c.execute("""
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, batch_name_final, quantity, buy_price, datetime.now().strftime("%Y-%m-%d")))

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

        # Verify the update worked
        c.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
        final_quantity = c.fetchone()[0]

        # Record initial inventory expense in expenses table
        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date)
            VALUES (?, 'Inventory', ?, ?, ?)
        """, (vendor_id, total_cost, f"Initial inventory - {name} ({quantity} units @ ₹{buy_price} each)", 
              datetime.now().strftime("%Y-%m-%d")))

        # Add to ledger - Inventory Asset (Debit)
        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'debit', 'Inventory', ?, ?, 'Inventory')
        """, (vendor_id, total_cost, f"Initial Inventory - {name} ({quantity} units @ ₹{buy_price} each)"))

        # Add to ledger - Cash (Credit) - assuming cash payment for initial inventory
        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'credit', 'Cash', ?, ?, 'Inventory Purchase')
        """, (vendor_id, total_cost, f"Cash payment for initial inventory - {name}"))

        conn.commit()
        conn.close()
        flash(f"Product added successfully! Inventory cost of ${total_cost} recorded in ledger.")
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

@app.route('/erp/take-break', methods=["POST"])
def vendor_take_break():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Set vendor on break
    c.execute('''
        UPDATE vendors 
        SET account_status='on_break', 
            break_start_date=?, 
            is_online=0
        WHERE email=?
    ''', (datetime.now().strftime("%Y-%m-%d"), email))

    conn.commit()
    conn.close()

    flash("You are now on break. Your profile is hidden from customers.")
    return redirect(url_for("erp_profile"))

@app.route('/erp/deactivate', methods=["POST"])
def vendor_deactivate():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Deactivate vendor account
    c.execute('''
        UPDATE vendors 
        SET account_status='deactivated', 
            is_online=0
        WHERE email=?
    ''', (email,))

    conn.commit()
    conn.close()

    flash("Your account has been deactivated. Contact support to reactivate.")
    return redirect(url_for("erp_logout"))

@app.route('/erp/reactivate', methods=["POST"])
def vendor_reactivate():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Reactivate vendor account
    c.execute('''
        UPDATE vendors 
        SET account_status='active', 
            break_start_date=NULL,
            break_end_date=NULL,
            break_reason=NULL
        WHERE email=?
    ''', (email,))

    conn.commit()
    conn.close()

    flash("Welcome back! Your account has been reactivated.")
    return redirect(url_for("erp_profile"))

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
        SELECT le.id, le.vendor_id, le.entry_type, le.account, le.amount, le.description, le.timestamp, le.sub_category, v.id as vendor_id FROM ledger_entries le 
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
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'debit', 'Expenses', ?, ?, ?)
        """, (vendor_id, amount, description, category))

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

    # Get sales data with product names - including POS and online sales
    c.execute("""
        SELECT sl.id, sl.vendor_id, sl.quantity, sl.unit_price, sl.total_amount, 
               sl.customer_email, sl.sale_date, 
               CASE 
                 WHEN sl.customer_email = '' OR sl.customer_email IS NULL THEN 'POS Sale'
                 ELSE 'Online Sale'
               END as sale_type,
               p.name as product_name 
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

    conn.close()
    return render_template("sales_analytics.html", 
                         sales=sales,
                         monthly_summary=monthly_summary, 
                         top_products=top_products)

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
        return render_template("inventory_analytics.html", analytics=[], operational_insights={})

    vendor_id = result[0]

    # Enhanced query to get comprehensive product analytics
    c.execute("""
        SELECT p.id, p.name, p.category, p.quantity as current_stock, 
               p.buy_price, p.sale_price,
               COALESCE(SUM(sl.quantity), 0) as total_sold_30_days,
               COALESCE(AVG(sl.quantity), 0) as avg_sale_quantity,
               COUNT(DISTINCT DATE(sl.sale_date)) as active_sales_days,
               COALESCE(SUM(sl.total_amount), 0) as total_revenue_30_days
        FROM products p
        LEFT JOIN sales_log sl ON p.id = sl.product_id 
            AND sl.sale_date >= date('now', '-30 days')
        WHERE p.vendor_id = ?
        GROUP BY p.id, p.name, p.category, p.quantity, p.buy_price, p.sale_price
    """, (vendor_id,))
    products = c.fetchall()

    analytics = []
    static_holding_rate = 0.02  # 2% monthly holding cost rate

    for product in products:
        (product_id, name, category, current_stock, buy_price, sale_price, 
         total_sold_30_days, avg_sale_quantity, active_sales_days, total_revenue_30_days) = product

        # Ensure we have valid prices
        buy_price = buy_price or 0
        sale_price = sale_price or 0

        # Calculate daily sales rate
        daily_sales_rate = total_sold_30_days / 30 if total_sold_30_days > 0 else 0

        # Calculate Average Inventory (Starting + Ending) / 2
        # Assuming starting inventory was current_stock + sold items
        starting_inventory = current_stock + total_sold_30_days
        avg_inventory = (starting_inventory + current_stock) / 2 if starting_inventory > 0 else current_stock

        # Calculate Turnover Rate = Total Sales / Average Inventory
        turnover_rate = total_sold_30_days / avg_inventory if avg_inventory > 0 else 0

        # Calculate Stock-to-Sales Ratio = Average Inventory / Sales
        stock_to_sales_ratio = avg_inventory / total_sold_30_days if total_sold_30_days > 0 else float('inf')

        # Calculate Gross Margin % = (Sell Price - Buy Price) / Sell Price × 100
        gross_margin_percent = ((sale_price - buy_price) / sale_price * 100) if sale_price > 0 else 0

        # Calculate Holding Cost per Month = Buy Price × Current Stock × Holding Rate
        holding_cost_monthly = buy_price * current_stock * static_holding_rate

        # Classify velocity based on turnover rate
        if turnover_rate >= 2.0:
            velocity_class = "Fast-moving"
            velocity_color = "success"
        elif turnover_rate >= 0.5:
            velocity_class = "Slow-moving"
            velocity_color = "warning"
        else:
            velocity_class = "Stagnant"
            velocity_color = "danger"

        # Calculate days remaining
        days_remaining = current_stock / daily_sales_rate if daily_sales_rate > 0 else 999

        # Safety stock calculation (assuming 7-14 days safety buffer)
        safety_stock = max(1, int(daily_sales_rate * 14)) if daily_sales_rate > 0 else 5

        # Stock status based on safety stock
        if current_stock < safety_stock:
            stock_status = "Reorder Now"
            stock_status_class = "danger"
        elif current_stock < (safety_stock * 2):
            stock_status = "Low Stock"
            stock_status_class = "warning"
        else:
            stock_status = "Good"
            stock_status_class = "success"

        # Calculate inventory value
        inventory_value = current_stock * buy_price

        analytics.append({
            'id': product_id,
            'name': name,
            'category': category or 'Uncategorized',
            'current_stock': current_stock,
            'daily_sales_rate': round(daily_sales_rate, 2),
            'days_remaining': int(days_remaining) if days_remaining < 999 else "∞",
            'turnover_rate': round(turnover_rate, 2),
            'avg_inventory': round(avg_inventory, 2),
            'stock_to_sales_ratio': round(stock_to_sales_ratio, 2) if stock_to_sales_ratio != float('inf') else "∞",
            'gross_margin_percent': round(gross_margin_percent, 1),
            'holding_cost_monthly': round(holding_cost_monthly, 2),
            'velocity_class': velocity_class,
            'velocity_color': velocity_color,
            'stock_status': stock_status,
            'stock_status_class': stock_status_class,
            'safety_stock': safety_stock,
            'reorder_point': safety_stock * 2,
            'buy_price': buy_price,
            'sale_price': sale_price,
            'total_revenue_30_days': round(total_revenue_30_days, 2),
            'inventory_value': round(inventory_value, 2),
            'status': stock_status,  # For backward compatibility
            'status_class': stock_status_class  # For backward compatibility
        })

    # Calculate Operational Insights with proper data formatting
    total_inventory_value = sum(item['inventory_value'] for item in analytics)
    total_holding_cost = sum(item['holding_cost_monthly'] for item in analytics)
    avg_turnover_rate = sum(item['turnover_rate'] for item in analytics) / len(analytics) if analytics else 0
    products_needing_attention = len([item for item in analytics if item['stock_status'] in ['Reorder Now', 'Low Stock']])

    # Most profitable products (top 5 by gross margin %)
    most_profitable = sorted([item for item in analytics if item['gross_margin_percent'] > 0], 
                           key=lambda x: x['gross_margin_percent'], reverse=True)[:5]

    # Highest holding cost products (top 5)
    highest_holding_cost = sorted([item for item in analytics if item['holding_cost_monthly'] > 0], 
                                key=lambda x: x['holding_cost_monthly'], reverse=True)[:5]

    # Low turnover products (bottom 5 by turnover rate, excluding zero turnover)
    low_turnover_products = [item for item in analytics if 0 < item['turnover_rate'] < 1.0]
    low_turnover = sorted(low_turnover_products, key=lambda x: x['turnover_rate'])[:5]

    # Top revenue generators (top 5 by 30-day revenue)
    top_revenue = sorted([item for item in analytics if item['total_revenue_30_days'] > 0], 
                        key=lambda x: x['total_revenue_30_days'], reverse=True)[:5]

    # Fast-moving products (turnover rate >= 2.0)
    fast_moving = [item for item in analytics if item['turnover_rate'] >= 2.0][:5]

    # Products needing reorder
    reorder_needed = [item for item in analytics if item['stock_status'] == 'Reorder Now']

    # Stagnant products (no sales in 30 days)
    stagnant_products = [item for item in analytics if item['turnover_rate'] == 0][:5]

    operational_insights = {
        'total_inventory_value': round(total_inventory_value, 2),
        'total_holding_cost': round(total_holding_cost, 2),
        'avg_turnover_rate': round(avg_turnover_rate, 2),
        'products_needing_attention': products_needing_attention,
        'most_profitable': most_profitable,
        'highest_holding_cost': highest_holding_cost,
        'low_turnover': low_turnover,
        'top_revenue': top_revenue,
        'fast_moving': fast_moving,
        'reorder_needed': reorder_needed,
        'stagnant_products': stagnant_products
    }

    conn.close()
    return render_template("inventory_analytics.html", 
                         analytics=analytics, 
                         operational_insights=operational_insights)

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
        WHERE LOWER(v.city) = LOWER(?)
        AND EXISTS (
            SELECT 1 FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0
        )
        AND (
            v.is_online = 1 
            OR NOT (LOWER(v.category) LIKE '%groom%' OR LOWER(v.category) LIKE '%salon%' OR LOWER(v.category) LIKE '%spa%' OR LOWER(v.category) LIKE '%boarding%')
        )
        AND (v.account_status IS NULL OR v.account_status = 'active')
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
            "image_url": vendor[8] or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400&h=400&fit=crop&crop=face",
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

    # Get products with stock - recalculate inventory first to ensure accuracy
    if vendor["is_online"]:
        # Recalculate inventory from batches to ensure accuracy
        c.execute("""
            UPDATE products 
            SET quantity = (
                SELECT COALESCE(SUM(remaining_quantity), 0) 
                FROM inventory_batches 
                WHERE product_id = products.id
            )
            WHERE vendor_id = ?
        """, (vendor_id,))
        conn.commit()

        # Get products with stock
        c.execute("""
            SELECT id, name, description, sale_price, quantity, image_url 
            FROM products 
            WHERE vendor_id=? AND quantity > 0
            ORDER BY name
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

@app.route('/place-order', methods=["POST"])
def place_order():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    data = request.get_json()

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        # Create order
        c.execute("""
            INSERT INTO orders (user_email, vendor_id, total_amount, delivery_address, delivery_type, delivery_fee, estimated_delivery)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_email,
            data['vendor_id'],
            data['total_amount'],
            data['delivery_address'],
            data['delivery_type'],
            data['delivery_fee'],
            data.get('estimated_delivery', '')
        ))

        order_id = c.lastrowid

        # Add order items
        for item in data['items']:
            c.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['product_id'], item['quantity'], item['unit_price']))

        conn.commit()
        conn.close()

        return {"success": True, "order_id": order_id}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}, 400

@app.route('/my-orders')
def my_orders():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all orders for this user
    c.execute("""
        SELECT o.id, o.total_amount, o.status, o.delivery_type, o.delivery_fee, 
               o.estimated_delivery, o.tracking_notes, o.order_date, v.name as vendor_name
        FROM orders o
        JOIN vendors v ON o.vendor_id = v.id
        WHERE o.user_email = ?
        ORDER BY o.order_date DESC
    """, (user_email,))
    orders = c.fetchall()

    # Get order items for each order
    order_details = []
    for order in orders:
        c.execute("""
            SELECT oi.quantity, oi.unit_price, p.name as product_name, p.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order[0],))
        items = c.fetchall()
        order_details.append((order, items))

    conn.close()
    return render_template("my_orders.html", order_details=order_details)

# Vendor order management
@app.route('/erp/orders')
def erp_orders():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()

    if not vendor_result:
        conn.close()
        return render_template("erp_orders.html", orders=[])

    vendor_id = vendor_result[0]

    # Get all orders for this vendor
    c.execute("""
        SELECT o.id, o.user_email, o.total_amount, o.status, o.delivery_type, 
               o.delivery_address, o.estimated_delivery, o.order_date
        FROM orders o
        WHERE o.vendor_id = ?
        ORDER BY o.order_date DESC
    """, (vendor_id,))
    orders = c.fetchall()

    conn.close()
    return render_template("erp_orders.html", orders=orders)

@app.route('/erp/orders/update/<int:order_id>', methods=["POST"])
def update_order_status(order_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    new_status = request.form.get("status")
    tracking_notes = request.form.get("tracking_notes", "")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Update order status
    c.execute("""
        UPDATE orders 
        SET status = ?, tracking_notes = ?
        WHERE id = ? AND vendor_id = (SELECT id FROM vendors WHERE email = ?)
    """, (new_status, tracking_notes, order_id, email))

    conn.commit()
    conn.close()

    flash(f"Order status updated to {new_status}")
    return redirect(url_for("erp_orders"))

@app.route('/marketplace/purchase-history')
def purchase_history():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    # Get purchase history from database (you can expand this later)
    # For now, return empty list - purchases will be handled via localStorage on frontend
    purchases = []
    total_orders = 0
    total_spent = 0.0

    return render_template("purchase_history.html", 
                         purchases=purchases, 
                         total_orders=total_orders, 
                         total_spent=total_spent)

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

@app.route('/master/admin/vendors')
def manage_vendors():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get all vendors with their details
    c.execute("""
        SELECT id, name, email, password, category, city, phone, bio, 
               is_online, account_status, break_start_date, break_reason
        FROM vendors 
        ORDER BY name
    """)
    vendors = c.fetchall()

    # Get vendor statistics
    vendor_stats = []
    for vendor in vendors:
        vendor_id = vendor[0]
        
        # Get total products
        c.execute("SELECT COUNT(*) FROM products WHERE vendor_id = ?", (vendor_id,))
        total_products = c.fetchone()[0]
        
        # Get total sales
        c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id = ?", (vendor_id,))
        total_sales = c.fetchone()[0]
        
        # Get total bookings
        c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id = ?", (vendor_id,))
        total_bookings = c.fetchone()[0]
        
        # Get average rating
        c.execute("SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE vendor_id = ?", (vendor_id,))
        avg_rating = c.fetchone()[0]
        
        vendor_stats.append({
            'vendor': vendor,
            'total_products': total_products,
            'total_sales': round(total_sales, 2),
            'total_bookings': total_bookings,
            'avg_rating': round(avg_rating, 1)
        })

    conn.close()
    return render_template("admin_vendor_management.html", vendor_stats=vendor_stats)

@app.route('/master/admin/vendors/update-status', methods=["POST"])
def update_vendor_status():
    if not session.get("master_admin"):
        return {"success": False, "message": "Unauthorized"}, 403

    try:
        vendor_id = request.form.get("vendor_id")
        new_status = request.form.get("status")
        
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        c.execute("UPDATE vendors SET account_status = ? WHERE id = ?", (new_status, vendor_id))
        conn.commit()
        conn.close()
        
        flash(f"Vendor status updated to {new_status}")
        return redirect(url_for("manage_vendors"))
        
    except Exception as e:
        flash(f"Error updating vendor status: {str(e)}")
        return redirect(url_for("manage_vendors"))

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

# POS System Routes
@app.route('/erp/pos')
def pos_system():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()

    if not vendor_result:
        conn.close()
        return render_template("pos_system.html", products=[])

    vendor_id = vendor_result[0]

    # Get all products with stock for this vendor
    c.execute("""
        SELECT id, name, description, sale_price, quantity, image_url, barcode
        FROM products 
        WHERE vendor_id = ? AND quantity > 0
        ORDER BY name
    """, (vendor_id,))
    products = c.fetchall()

    conn.close()
    return render_template("pos_system.html", products=products)

@app.route('/erp/pos/process-sale', methods=["POST"])
def process_pos_sale():
    if "vendor" not in session:
        return {"success": False, "error": "Unauthorized"}, 403

    email = session["vendor"]
    data = request.get_json()

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            return {"success": False, "error": "Vendor not found"}, 404

        vendor_id = vendor_result[0]

        total_sale_amount = 0
        receipt_items = []

        # Process each item in the sale
        for item in data['items']:
            product_id = item['id']
            quantity_sold = item['quantity']
            sale_price = item['price']

            # Check current stock
            c.execute("SELECT quantity, name FROM products WHERE id = ? AND vendor_id = ?", (product_id, vendor_id))
            product_data = c.fetchone()

            if not product_data:
                return {"success": False, "error": f"Product {product_id} not found"}, 400

            current_stock, product_name = product_data

            if current_stock < quantity_sold:
                return {"success": False, "error": f"Insufficient stock for {product_name}"}, 400

            # Calculate sale amount
            item_total = sale_price * quantity_sold
            total_sale_amount += item_total

            # Update inventory using FIFO (First In, First Out)
            remaining_to_sell = quantity_sold
            c.execute("""
                SELECT id, remaining_quantity, unit_cost 
                FROM inventory_batches 
                WHERE product_id = ? AND remaining_quantity > 0 
                ORDER BY date_added ASC
            """, (product_id,))
            batches = c.fetchall()

            total_cogs = 0  # Cost of Goods Sold

            for batch in batches:
                if remaining_to_sell <= 0:
                    break

                batch_id, batch_remaining, unit_cost = batch
                units_from_batch = min(remaining_to_sell, batch_remaining)

                # Update batch quantity
                new_remaining = batch_remaining - units_from_batch
                c.execute("UPDATE inventory_batches SET remaining_quantity = ? WHERE id = ?", 
                         (new_remaining, batch_id))

                # Calculate COGS for this portion
                total_cogs += units_from_batch * unit_cost
                remaining_to_sell -= units_from_batch

            # Update product quantity
            c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity_sold, product_id))

            # Record sale in sales log
            c.execute("""
                INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, customer_email, sale_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vendor_id, product_id, quantity_sold, sale_price, item_total, 
                  data.get('customer_email', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # Add to ledger - Revenue (Credit) - POS Sales
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'credit', 'Sales Revenue', ?, ?, 'POS Sales')
            """, (vendor_id, item_total, f"POS Sale - {product_name} x{quantity_sold}"))

            # Add to ledger - COGS (Debit)
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'debit', 'Cost of Goods Sold', ?, ?, 'Product Sales')
            """, (vendor_id, total_cogs, f"COGS - {product_name} x{quantity_sold}"))

            receipt_items.append({
                'name': product_name,
                'quantity': quantity_sold,
                'unit_price': sale_price,
                'total': item_total
            })

        # Create receipt record
        c.execute("""
            INSERT INTO receipts (booking_id, amount, paid_on, payment_mode)
            VALUES (?, ?, ?, ?)
        """, (None, total_sale_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('payment_method', 'cash')))

        receipt_id = c.lastrowid

        conn.commit()
        conn.close()

        return {
            "success": True, 
            "receipt_id": receipt_id,
            "total_amount": total_sale_amount,
            "items": receipt_items
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}, 500

# Enhanced inventory management with automatic expense tracking
@app.route('/erp/inventory/add-stock/<int:product_id>', methods=["POST"])
def add_inventory_stock(product_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            flash("Vendor not found")
            return redirect(url_for("erp_products"))

        vendor_id = vendor_result[0]

        # Verify product belongs to vendor
        c.execute("SELECT name FROM products WHERE id = ? AND vendor_id = ?", (product_id, vendor_id))
        product_data = c.fetchone()
        if not product_data:
            flash("Product not found")
            return redirect(url_for("erp_products"))

        product_name = product_data[0]

        # Get form data
        quantity = int(request.form.get("quantity", 0))
        unit_cost = float(request.form.get("unit_cost", 0))
        batch_name = request.form.get("batch_name", f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        if quantity <= 0 or unit_cost <= 0:
            flash("Invalid quantity or cost")
            return redirect(url_for("view_product", product_id=product_id))

        total_cost = quantity * unit_cost

        # Add inventory batch
        c.execute("""
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        """, (product_id, quantity, unit_cost, quantity))

        # Add product batch for tracking
        c.execute("""
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, batch_name, quantity, unit_cost, datetime.now().strftime("%Y-%m-%d")))

        # Update product total quantity
        c.execute("""
            UPDATE products 
            SET quantity = quantity + ?, buy_price = ?
            WHERE id = ?
        """, (quantity, unit_cost, product_id))

        # Record inventory expense automatically
        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date)
            VALUES (?, 'Inventory', ?, ?, ?)
        """, (vendor_id, total_cost, f"Inventory purchase - {product_name} ({quantity} units @ ₹{unit_cost} each)", 
              datetime.now().strftime("%Y-%m-%d")))

        # Add to ledger - Inventory Asset (Debit)
        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'debit', 'Inventory', ?, ?, 'Inventory')
        """, (vendor_id, total_cost, f"Inventory Purchase - {product_name} ({quantity} units @ ₹{unit_cost} each)"))

        # Add to ledger - Cash/Accounts Payable (Credit)
        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'credit', 'Cash', ?, ?, 'Inventory Purchase')
        """, (vendor_id, total_cost, f"Payment for Inventory - {product_name}"))

        conn.commit()
        conn.close()

        flash(f"Successfully added {quantity} units to inventory. Expense of ${total_cost} recorded automatically.")
        return redirect(url_for("view_product", product_id=product_id))

    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f"Error adding inventory: {str(e)}")
        return redirect(url_for("view_product", product_id=product_id))

# Add alias route for inventory analytics
@app.route('/erp/inventory/analytics')
def inventory_analytics_alias():
    """Alias route for inventory analytics to match requested URL structure"""
    return inventory_analytics()

# Import the smart inventory bot
from inventory_bot import inventory_bot

# Inventory Bot Routes
@app.route('/erp/inventory-bot')
def inventory_bot_interface():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    return render_template("inventory_bot_chat.html")

@app.route('/erp/inventory-bot/query', methods=["POST"])
def inventory_bot_query():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json()
    query = data.get("query", "")
    session_id = data.get("session_id")
    vendor_email = session["vendor"]
    
    if not query:
        return {"error": "Query is required"}, 400
    
    try:
        # Process query through inventory bot (handles both smart and basic modes)
        response = inventory_bot.process_query(query, vendor_email)
        
        # Return response in expected format
        return {
            "response": response,
            "intent": "processed",
            "confidence": 0.8,
            "session_id": session_id or "default",
            "log_id": None
        }
    except Exception as e:
        print(f"Inventory bot error: {e}")
        return {"error": str(e)}, 500

@app.route('/erp/inventory-bot/feedback', methods=["POST"])
def inventory_bot_feedback():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json()
    log_id = data.get("log_id")
    feedback = data.get("feedback")  # 1 for helpful, 0 for not helpful
    
    if log_id is None or feedback is None:
        return {"error": "log_id and feedback are required"}, 400
    
    try:
        if hasattr(inventory_bot, 'smart_bot'):
            success = inventory_bot.smart_bot.submit_feedback(log_id, feedback)
            return {"success": success}
        else:
            return {"success": False, "error": "Smart bot not available"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/erp/inventory-bot/analytics')
def inventory_bot_analytics():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    try:
        if hasattr(inventory_bot, 'smart_bot'):
            analytics = inventory_bot.smart_bot.get_analytics_dashboard()
            return render_template("bot_analytics.html", analytics=analytics)
        else:
            return "Analytics not available", 404
    except Exception as e:
        return f"Error loading analytics: {str(e)}", 500

@app.route('/erp/inventory-bot/retrain', methods=["POST"])
def inventory_bot_retrain():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    try:
        if hasattr(inventory_bot, 'smart_bot'):
            result = inventory_bot.smart_bot.retrain_model()
            return {"success": result.get('success'), "message": "Model retrained successfully" if result.get('success') else result.get('error')}
        else:
            return {"success": False, "error": "Smart bot not available"}
    except Exception as e:
        return {"error": str(e)}, 500

# Business Analysis Route
@app.route('/erp/business-analysis')
def business_analysis():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    return render_template("business_analysis.html")

# Business Analysis Data API
@app.route('/api/business-analysis', methods=["POST"])
def business_analysis_api():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    email = session["vendor"]
    data = request.get_json()
    analysis_type = data.get("type", "comprehensive")
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    
    if not vendor_result:
        conn.close()
        return {"error": "Vendor not found"}, 404
    
    vendor_id = vendor_result[0]
    
    # Get comprehensive business data
    business_data = {}
    
    # Sales summary
    c.execute("""
        SELECT COUNT(*) as total_transactions,
               SUM(total_amount) as total_revenue,
               AVG(total_amount) as avg_transaction_value,
               SUM(quantity) as total_units_sold
        FROM sales_log 
        WHERE vendor_id = ? AND sale_date >= date('now', '-90 days')
    """, (vendor_id,))
    
    sales_data = c.fetchone()
    business_data['sales_summary'] = {
        'total_transactions': sales_data[0] or 0,
        'total_revenue': sales_data[1] or 0,
        'avg_transaction_value': sales_data[2] or 0,
        'total_units_sold': sales_data[3] or 0
    }
    
    # Product performance
    c.execute("""
        SELECT p.name, p.sale_price, p.buy_price, p.quantity,
               COALESCE(SUM(sl.quantity), 0) as units_sold,
               COALESCE(SUM(sl.total_amount), 0) as revenue,
               ((p.sale_price - p.buy_price) / p.sale_price * 100) as margin_percent
        FROM products p
        LEFT JOIN sales_log sl ON p.id = sl.product_id 
            AND sl.sale_date >= date('now', '-90 days')
        WHERE p.vendor_id = ?
        GROUP BY p.id, p.name, p.sale_price, p.buy_price, p.quantity
        ORDER BY revenue DESC
        LIMIT 10
    """, (vendor_id,))
    
    product_data = c.fetchall()
    business_data['product_performance'] = []
    for product in product_data:
        business_data['product_performance'].append({
            'name': product[0],
            'sale_price': product[1],
            'buy_price': product[2],
            'current_stock': product[3],
            'units_sold': product[4],
            'revenue': product[5],
            'margin_percent': product[6]
        })
    
    # Expense breakdown
    c.execute("""
        SELECT category, SUM(amount) as total_amount
        FROM expenses 
        WHERE vendor_id = ? AND date >= date('now', '-90 days')
        GROUP BY category
        ORDER BY total_amount DESC
    """, (vendor_id,))
    
    expense_data = c.fetchall()
    business_data['expenses'] = []
    for expense in expense_data:
        business_data['expenses'].append({
            'category': expense[0],
            'amount': expense[1]
        })
    
    # Inventory metrics
    c.execute("""
        SELECT COUNT(*) as total_products,
               SUM(quantity) as total_units,
               SUM(quantity * buy_price) as total_inventory_value,
               COUNT(CASE WHEN quantity <= 5 THEN 1 END) as low_stock_items
        FROM products 
        WHERE vendor_id = ?
    """, (vendor_id,))
    
    inventory_data = c.fetchone()
    business_data['inventory_metrics'] = {
        'total_products': inventory_data[0] or 0,
        'total_units': inventory_data[1] or 0,
        'total_inventory_value': inventory_data[2] or 0,
        'low_stock_items': inventory_data[3] or 0
    }
    
    # Monthly trends
    c.execute("""
        SELECT strftime('%Y-%m', sale_date) as month,
               COUNT(*) as transactions,
               SUM(total_amount) as revenue
        FROM sales_log 
        WHERE vendor_id = ? AND sale_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', sale_date)
        ORDER BY month DESC
        LIMIT 12
    """, (vendor_id,))
    
    monthly_data = c.fetchall()
    business_data['monthly_trends'] = []
    for month in monthly_data:
        business_data['monthly_trends'].append({
            'month': month[0],
            'transactions': month[1],
            'revenue': month[2]
        })
    
    # Key performance indicators
    total_revenue = business_data['sales_summary']['total_revenue']
    total_expenses = sum(expense['amount'] for expense in business_data['expenses'])
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    business_data['kpis'] = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'inventory_turnover': business_data['sales_summary']['total_units_sold'] / business_data['inventory_metrics']['total_units'] if business_data['inventory_metrics']['total_units'] > 0 else 0
    }
    
    conn.close()
    
    return {
        "success": True,
        "data": business_data,
        "analysis_type": analysis_type,
        "vendor_email": email
    }

# ---- CHAT SYSTEM ROUTES ----

@app.route('/chat')
def chat_interface():
    if "user" not in session and "vendor" not in session:
        return redirect(url_for("login"))
    
    return render_template("chat.html")

@app.route('/api/chat/conversations')
def get_conversations():
    if "user" not in session and "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    if "vendor" in session:
        vendor_email = session["vendor"]
        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            return {"conversations": []}
        
        vendor_id = vendor_result[0]
        
        # Get conversations for vendor
        c.execute("""
            SELECT cc.id, cc.user_email, cc.last_message_time, cc.vendor_unread_count, cc.user_unread_count,
                   (SELECT message_text FROM chat_messages WHERE conversation_id = cc.id ORDER BY timestamp DESC LIMIT 1) as last_message
            FROM chat_conversations cc
            WHERE cc.vendor_id = ?
            ORDER BY cc.last_message_time DESC
        """, (vendor_id,))
        
        conversations = []
        for conv in c.fetchall():
            conversations.append({
                "id": conv[0],
                "user_email": conv[1],
                "vendor_name": conv[1],  # For consistency
                "last_message_time": conv[2],
                "vendor_unread_count": conv[3],
                "user_unread_count": conv[4],
                "last_message": conv[5]
            })
    else:
        user_email = session["user"]
        
        # Get conversations for user
        c.execute("""
            SELECT cc.id, cc.vendor_id, cc.last_message_time, cc.vendor_unread_count, cc.user_unread_count,
                   v.name as vendor_name,
                   (SELECT message_text FROM chat_messages WHERE conversation_id = cc.id ORDER BY timestamp DESC LIMIT 1) as last_message
            FROM chat_conversations cc
            JOIN vendors v ON cc.vendor_id = v.id
            WHERE cc.user_email = ?
            ORDER BY cc.last_message_time DESC
        """, (user_email,))
        
        conversations = []
        for conv in c.fetchall():
            conversations.append({
                "id": conv[0],
                "vendor_id": conv[1],
                "last_message_time": conv[2],
                "vendor_unread_count": conv[3],
                "user_unread_count": conv[4],
                "vendor_name": conv[5],
                "last_message": conv[6]
            })
    
    conn.close()
    return {"conversations": conversations}

@app.route('/api/chat/messages/<int:conversation_id>')
def get_messages(conversation_id):
    if "user" not in session and "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Verify user has access to this conversation
    if "vendor" in session:
        vendor_email = session["vendor"]
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            return {"error": "Unauthorized"}, 401
        
        vendor_id = vendor_result[0]
        c.execute("SELECT id FROM chat_conversations WHERE id = ? AND vendor_id = ?", 
                 (conversation_id, vendor_id))
    else:
        user_email = session["user"]
        c.execute("SELECT id FROM chat_conversations WHERE id = ? AND user_email = ?", 
                 (conversation_id, user_email))
    
    if not c.fetchone():
        return {"error": "Conversation not found"}, 404
    
    # Get messages
    c.execute("""
        SELECT id, sender_type, sender_id, message_text, timestamp, is_read
        FROM chat_messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,))
    
    messages = []
    for msg in c.fetchall():
        messages.append({
            "id": msg[0],
            "sender_type": msg[1],
            "sender_id": msg[2],
            "message_text": msg[3],
            "timestamp": msg[4],
            "is_read": msg[5]
        })
    
    conn.close()
    return {"messages": messages}

@app.route('/api/chat/send', methods=["POST"])
def send_message():
    if "user" not in session and "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json()
    conversation_id = data.get("conversation_id")
    message_text = data.get("message")
    
    if not conversation_id or not message_text:
        return {"error": "Missing required data"}, 400
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Determine sender info
    if "vendor" in session:
        sender_type = "vendor"
        sender_id = session["vendor"]
        
        # Verify access and get vendor ID
        c.execute("SELECT id FROM vendors WHERE email = ?", (sender_id,))
        vendor_result = c.fetchone()
        if not vendor_result:
            return {"error": "Unauthorized"}, 401
        
        vendor_id = vendor_result[0]
        c.execute("SELECT id FROM chat_conversations WHERE id = ? AND vendor_id = ?", 
                 (conversation_id, vendor_id))
        
        if not c.fetchone():
            return {"error": "Conversation not found"}, 404
        
        # Update unread count for user
        c.execute("UPDATE chat_conversations SET user_unread_count = user_unread_count + 1 WHERE id = ?", 
                 (conversation_id,))
    else:
        sender_type = "user"
        sender_id = session["user"]
        
        # Verify access
        c.execute("SELECT id FROM chat_conversations WHERE id = ? AND user_email = ?", 
                 (conversation_id, sender_id))
        
        if not c.fetchone():
            return {"error": "Conversation not found"}, 404
        
        # Update unread count for vendor
        c.execute("UPDATE chat_conversations SET vendor_unread_count = vendor_unread_count + 1 WHERE id = ?", 
                 (conversation_id,))
    
    # Insert message
    c.execute("""
        INSERT INTO chat_messages (conversation_id, sender_type, sender_id, message_text)
        VALUES (?, ?, ?, ?)
    """, (conversation_id, sender_type, sender_id, message_text))
    
    # Update conversation last message time
    c.execute("UPDATE chat_conversations SET last_message_time = CURRENT_TIMESTAMP WHERE id = ?", 
             (conversation_id,))
    
    conn.commit()
    conn.close()
    
    # Emit real-time message
    socketio.emit('new_message', {
        'conversation_id': conversation_id,
        'sender_type': sender_type,
        'message': message_text
    }, room=f'conversation_{conversation_id}')
    
    return {"success": True}

@app.route('/api/chat/mark-read/<int:conversation_id>', methods=["POST"])
def mark_messages_read(conversation_id):
    if "user" not in session and "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Update unread count
    if "vendor" in session:
        c.execute("UPDATE chat_conversations SET vendor_unread_count = 0 WHERE id = ?", 
                 (conversation_id,))
    else:
        c.execute("UPDATE chat_conversations SET user_unread_count = 0 WHERE id = ?", 
                 (conversation_id,))
    
    conn.commit()
    conn.close()
    
    return {"success": True}

@app.route('/api/chat/start-conversation', methods=["POST"])
def start_conversation():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json()
    vendor_id = data.get("vendor_id")
    
    if not vendor_id:
        return {"error": "Vendor ID required"}, 400
    
    user_email = session["user"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Check if conversation already exists
    c.execute("SELECT id FROM chat_conversations WHERE vendor_id = ? AND user_email = ?", 
             (vendor_id, user_email))
    existing = c.fetchone()
    
    if existing:
        return {"conversation_id": existing[0]}
    
    # Create new conversation
    c.execute("""
        INSERT INTO chat_conversations (vendor_id, user_email)
        VALUES (?, ?)
    """, (vendor_id, user_email))
    
    conversation_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"conversation_id": conversation_id}

# ---- WEBSOCKET HANDLERS ----

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'Joined room {room}'})

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'Left room {room}'})

# Run app
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
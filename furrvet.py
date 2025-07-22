
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import hashlib
import json
import os
from werkzeug.utils import secure_filename

# Initialize FurrVet Flask app
furrvet_app = Flask(__name__, 
                   template_folder='templates/furrvet',
                   static_folder='static/furrvet')
furrvet_app.secret_key = 'furrvet_secret_key_2024'

# Configuration
UPLOAD_FOLDER = 'static/furrvet/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
furrvet_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_furrvet_db():
    """Initialize FurrVet database with all required tables"""
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Veterinarian accounts
    c.execute('''
        CREATE TABLE IF NOT EXISTS vets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            license_number TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            clinic_name TEXT,
            address TEXT,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Pet owners/clients
    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            address TEXT,
            city TEXT,
            emergency_contact TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pets/Patients
    c.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            gender TEXT,
            date_of_birth DATE,
            weight REAL,
            microchip_id TEXT UNIQUE,
            owner_id INTEGER NOT NULL,
            color TEXT,
            distinguishing_marks TEXT,
            insurance_info TEXT,
            allergies TEXT,
            medical_conditions TEXT,
            photo_url TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES pet_owners (id)
        )
    ''')
    
    # Appointments
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            appointment_type TEXT NOT NULL,
            duration INTEGER DEFAULT 30,
            status TEXT DEFAULT 'scheduled',
            reason TEXT,
            notes TEXT,
            follow_up_required BOOLEAN DEFAULT 0,
            follow_up_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Medical records
    c.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            appointment_id INTEGER,
            visit_date DATE NOT NULL,
            chief_complaint TEXT,
            physical_examination TEXT,
            diagnosis TEXT,
            treatment_plan TEXT,
            prescription TEXT,
            follow_up_instructions TEXT,
            vitals_temperature REAL,
            vitals_weight REAL,
            vitals_heart_rate INTEGER,
            vitals_respiratory_rate INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id),
            FOREIGN KEY (appointment_id) REFERENCES appointments (id)
        )
    ''')
    
    # Vaccinations
    c.execute('''
        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            vaccine_name TEXT NOT NULL,
            vaccine_type TEXT,
            batch_number TEXT,
            manufacturer TEXT,
            vaccination_date DATE NOT NULL,
            next_due_date DATE,
            site_of_injection TEXT,
            adverse_reactions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Laboratory tests
    c.execute('''
        CREATE TABLE IF NOT EXISTS lab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            test_type TEXT,
            ordered_date DATE NOT NULL,
            completed_date DATE,
            status TEXT DEFAULT 'pending',
            results TEXT,
            reference_values TEXT,
            lab_technician TEXT,
            external_lab TEXT,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Imaging/X-rays
    c.execute('''
        CREATE TABLE IF NOT EXISTS imaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            imaging_type TEXT NOT NULL,
            body_part TEXT,
            imaging_date DATE NOT NULL,
            findings TEXT,
            image_urls TEXT,
            radiologist_notes TEXT,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Hospitalizations
    c.execute('''
        CREATE TABLE IF NOT EXISTS hospitalizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            admission_date DATE NOT NULL,
            discharge_date DATE,
            reason TEXT NOT NULL,
            bed_number TEXT,
            ward_type TEXT,
            daily_notes TEXT,
            feeding_instructions TEXT,
            medication_schedule TEXT,
            status TEXT DEFAULT 'admitted',
            total_cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Surgeries/Procedures
    c.execute('''
        CREATE TABLE IF NOT EXISTS surgeries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            surgery_date DATE NOT NULL,
            surgery_type TEXT NOT NULL,
            procedure_description TEXT,
            anesthesia_type TEXT,
            pre_op_notes TEXT,
            post_op_notes TEXT,
            complications TEXT,
            recovery_instructions TEXT,
            follow_up_date DATE,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Inventory/Pharmacy
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            description TEXT,
            unit_of_measure TEXT,
            current_stock INTEGER DEFAULT 0,
            minimum_stock INTEGER DEFAULT 10,
            unit_cost REAL,
            selling_price REAL,
            supplier TEXT,
            batch_number TEXT,
            expiry_date DATE,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Invoices/Billing
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            pet_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            invoice_date DATE NOT NULL,
            due_date DATE,
            subtotal REAL NOT NULL,
            tax_rate REAL DEFAULT 18.0,
            tax_amount REAL,
            discount_rate REAL DEFAULT 0.0,
            discount_amount REAL,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (owner_id) REFERENCES pet_owners (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    # Invoice items
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            item_description TEXT NOT NULL,
            item_type TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id)
        )
    ''')
    
    # Staff management
    c.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            role TEXT NOT NULL,
            department TEXT,
            salary REAL,
            hire_date DATE,
            shift_timing TEXT,
            qualifications TEXT,
            emergency_contact TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create demo data
    c.execute('''
        INSERT OR IGNORE INTO vets (name, email, password, license_number, specialization, phone, clinic_name, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Dr. Sarah Johnson", "vet@furrvet.com", "vet123", "VET-2024-001", "Small Animals", "+91-9876543210", "FurrVet Clinic", "Trivandrum"))
    
    c.execute('''
        INSERT OR IGNORE INTO pet_owners (name, email, phone, address, city)
        VALUES (?, ?, ?, ?, ?)
    ''', ("John Smith", "john@example.com", "+91-9876543211", "123 Pet Street", "Trivandrum"))
    
    c.execute('''
        INSERT OR IGNORE INTO pets (name, species, breed, gender, date_of_birth, weight, owner_id, color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Buddy", "Dog", "Golden Retriever", "Male", "2020-05-15", 32.5, 1, "Golden"))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_furrvet_db()

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'vet_id' not in session:
            return redirect(url_for('vet_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@furrvet_app.route('/furrvet')
@furrvet_app.route('/furrvet/')
def furrvet_home():
    if 'vet_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('vet_login'))

@furrvet_app.route('/furrvet/login', methods=['GET', 'POST'])
def vet_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vets WHERE email=? AND password=? AND is_active=1", (email, password))
        vet = c.fetchone()
        conn.close()
        
        if vet:
            session['vet_id'] = vet[0]
            session['vet_name'] = vet[1]
            session['vet_email'] = vet[2]
            session['clinic_name'] = vet[7]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('furrvet_login.html')

@furrvet_app.route('/furrvet/logout')
def logout():
    session.clear()
    return redirect(url_for('vet_login'))

@furrvet_app.route('/furrvet/dashboard')
@login_required
def dashboard():
    vet_id = session['vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Today's appointments
    c.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE vet_id = ? AND DATE(appointment_date) = DATE('now')
    """, (vet_id,))
    today_appointments = c.fetchone()[0]
    
    # Total patients
    c.execute("SELECT COUNT(*) FROM pets")
    total_patients = c.fetchone()[0]
    
    # Today's revenue
    c.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM invoices 
        WHERE vet_id = ? AND DATE(invoice_date) = DATE('now') AND payment_status = 'paid'
    """, (vet_id,))
    today_revenue = c.fetchone()[0]
    
    # Pending appointments
    c.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE vet_id = ? AND status = 'scheduled'
    """, (vet_id,))
    pending_appointments = c.fetchone()[0]
    
    # Recent appointments
    c.execute("""
        SELECT a.id, p.name as pet_name, po.name as owner_name, a.appointment_date, 
               a.appointment_time, a.appointment_type, a.status
        FROM appointments a
        JOIN pets p ON a.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE a.vet_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        LIMIT 5
    """, (vet_id,))
    recent_appointments = c.fetchall()
    
    conn.close()
    
    stats = {
        'today_appointments': today_appointments,
        'total_patients': total_patients,
        'today_revenue': today_revenue,
        'pending_appointments': pending_appointments
    }
    
    return render_template('furrvet_dashboard.html', 
                         stats=stats, 
                         recent_appointments=recent_appointments,
                         vet_name=session['vet_name'],
                         clinic_name=session['clinic_name'])

@furrvet_app.route('/furrvet/patients')
@login_required
def patients():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    search = request.args.get('search', '')
    if search:
        c.execute("""
            SELECT p.*, po.name as owner_name, po.phone as owner_phone
            FROM pets p
            JOIN pet_owners po ON p.owner_id = po.id
            WHERE p.name LIKE ? OR po.name LIKE ? OR p.microchip_id LIKE ?
            ORDER BY p.name
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        c.execute("""
            SELECT p.*, po.name as owner_name, po.phone as owner_phone
            FROM pets p
            JOIN pet_owners po ON p.owner_id = po.id
            ORDER BY p.name
        """)
    
    patients = c.fetchall()
    conn.close()
    
    return render_template('furrvet_patients.html', patients=patients, search=search)

@furrvet_app.route('/furrvet/patients/<int:pet_id>')
@login_required
def patient_detail(pet_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Get pet details
    c.execute("""
        SELECT p.*, po.name as owner_name, po.email as owner_email, 
               po.phone as owner_phone, po.address as owner_address
        FROM pets p
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE p.id = ?
    """, (pet_id,))
    pet = c.fetchone()
    
    if not pet:
        flash('Patient not found')
        return redirect(url_for('patients'))
    
    # Get medical history
    c.execute("""
        SELECT mr.*, v.name as vet_name
        FROM medical_records mr
        JOIN vets v ON mr.vet_id = v.id
        WHERE mr.pet_id = ?
        ORDER BY mr.visit_date DESC
    """, (pet_id,))
    medical_records = c.fetchall()
    
    # Get vaccinations
    c.execute("""
        SELECT v.*, vt.name as vet_name
        FROM vaccinations v
        JOIN vets vt ON v.vet_id = vt.id
        WHERE v.pet_id = ?
        ORDER BY v.vaccination_date DESC
    """, (pet_id,))
    vaccinations = c.fetchall()
    
    # Get upcoming appointments
    c.execute("""
        SELECT * FROM appointments
        WHERE pet_id = ? AND appointment_date >= DATE('now')
        ORDER BY appointment_date, appointment_time
    """, (pet_id,))
    upcoming_appointments = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet_patient_detail.html',
                         pet=pet,
                         medical_records=medical_records,
                         vaccinations=vaccinations,
                         upcoming_appointments=upcoming_appointments)

@furrvet_app.route('/furrvet/appointments')
@login_required
def appointments():
    vet_id = session['vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    c.execute("""
        SELECT a.*, p.name as pet_name, p.species, po.name as owner_name, po.phone as owner_phone
        FROM appointments a
        JOIN pets p ON a.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE a.vet_id = ? AND DATE(a.appointment_date) = ?
        ORDER BY a.appointment_time
    """, (vet_id, date_filter))
    
    appointments_list = c.fetchall()
    conn.close()
    
    return render_template('furrvet_appointments.html', 
                         appointments=appointments_list, 
                         selected_date=date_filter)

@furrvet_app.route('/furrvet/appointments/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    if request.method == 'POST':
        vet_id = session['vet_id']
        pet_id = request.form.get('pet_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        appointment_type = request.form.get('appointment_type')
        reason = request.form.get('reason', '')
        
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO appointments (pet_id, vet_id, appointment_date, appointment_time, 
                                    appointment_type, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pet_id, vet_id, appointment_date, appointment_time, appointment_type, reason))
        
        conn.commit()
        conn.close()
        
        flash('Appointment scheduled successfully!')
        return redirect(url_for('appointments'))
    
    # Get all pets for the dropdown
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.name, po.name as owner_name
        FROM pets p
        JOIN pet_owners po ON p.owner_id = po.id
        ORDER BY p.name
    """)
    pets = c.fetchall()
    conn.close()
    
    return render_template('furrvet_new_appointment.html', pets=pets)

@furrvet_app.route('/furrvet/billing')
@login_required
def billing():
    vet_id = session['vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT i.*, p.name as pet_name, po.name as owner_name
        FROM invoices i
        JOIN pets p ON i.pet_id = p.id
        JOIN pet_owners po ON i.owner_id = po.id
        WHERE i.vet_id = ?
        ORDER BY i.invoice_date DESC
        LIMIT 50
    """, (vet_id,))
    
    invoices = c.fetchall()
    conn.close()
    
    return render_template('furrvet_billing.html', invoices=invoices)

@furrvet_app.route('/furrvet/inventory')
@login_required
def inventory():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Get low stock items
    c.execute("SELECT * FROM inventory WHERE current_stock <= minimum_stock ORDER BY current_stock")
    low_stock_items = c.fetchall()
    
    # Get all inventory
    c.execute("SELECT * FROM inventory ORDER BY item_name")
    all_items = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet_inventory.html', 
                         low_stock_items=low_stock_items, 
                         all_items=all_items)

if __name__ == '__main__':
    furrvet_app.run(host='0.0.0.0', port=5000, debug=True)


from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import hashlib
import json
import os
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

furrvet_bp = Blueprint('furrvet', __name__,
                       template_folder='templates/furrvet',
                       url_prefix='/furrvet')

UPLOAD_FOLDER = 'static/furrvet/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_furrvet_db():
    """Initialize FurrVet database with all required tables"""
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
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
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT,
            upload_date DATE DEFAULT CURRENT_DATE,
            expiry_date DATE,
            uploaded_by INTEGER,
            description TEXT,
            compliance_category TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (uploaded_by) REFERENCES vets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_insurance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            insurance_provider TEXT NOT NULL,
            policy_number TEXT NOT NULL,
            policy_start_date DATE NOT NULL,
            policy_end_date DATE,
            coverage_amount REAL,
            deductible REAL,
            premium_amount REAL,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS insurance_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            insurance_id INTEGER NOT NULL,
            claim_number TEXT UNIQUE NOT NULL,
            claim_date DATE NOT NULL,
            treatment_date DATE,
            claim_amount REAL NOT NULL,
            approved_amount REAL,
            status TEXT DEFAULT 'submitted',
            description TEXT,
            documents TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (insurance_id) REFERENCES pet_insurance (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            payment_terms TEXT,
            rating REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            expected_delivery DATE,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_by INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
            FOREIGN KEY (created_by) REFERENCES vets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            campaign_type TEXT NOT NULL,
            target_segment TEXT,
            start_date DATE,
            end_date DATE,
            message_template TEXT,
            status TEXT DEFAULT 'draft',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES vets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS client_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            reminder_date DATE NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'pending',
            sent_date DATE,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS staff_certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            certification_name TEXT NOT NULL,
            issuing_body TEXT,
            issue_date DATE,
            expiry_date DATE,
            status TEXT DEFAULT 'valid',
            document_path TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS clinic_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            purchase_date DATE,
            purchase_cost REAL,
            current_value REAL,
            depreciation_rate REAL,
            last_maintenance DATE,
            next_maintenance DATE,
            location TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES vets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS telehealth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            pet_id INTEGER NOT NULL,
            vet_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            session_time TIME NOT NULL,
            duration INTEGER,
            session_url TEXT,
            session_notes TEXT,
            prescription TEXT,
            follow_up_required BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (pet_id) REFERENCES pets (id),
            FOREIGN KEY (vet_id) REFERENCES vets (id)
        )
    ''')
    
    c.execute('''
        INSERT OR IGNORE INTO vets (name, email, password, license_number, specialization, phone, clinic_name, city)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("Dr. Sarah Johnson", "vet@furrvet.com", generate_password_hash("vet123"), "VET-2024-001", "Small Animals", "+91-9876543210", "FurrVet Clinic", "Trivandrum"))
    
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


def furrvet_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'furrvet_vet_id' not in session:
            return redirect(url_for('furrvet.vet_login'))
        return f(*args, **kwargs)
    return decorated_function


@furrvet_bp.route('/')
@furrvet_bp.route('')
def furrvet_home():
    if 'furrvet_vet_id' in session:
        return redirect(url_for('furrvet.dashboard'))
    return redirect(url_for('furrvet.vet_login'))

@furrvet_bp.route('/login', methods=['GET', 'POST'])
def vet_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vets WHERE email=? AND is_active=1", (email,))
        vet = c.fetchone()
        
        if vet:
            stored_pw = vet[3]
            if stored_pw.startswith('pbkdf2:') or stored_pw.startswith('scrypt:'):
                pw_ok = check_password_hash(stored_pw, password)
            else:
                pw_ok = (stored_pw == password)
                if pw_ok:
                    hashed = generate_password_hash(password)
                    c.execute("UPDATE vets SET password=? WHERE id=?", (hashed, vet[0]))
                    conn.commit()
            
            if pw_ok:
                session['furrvet_vet_id'] = vet[0]
                session['furrvet_vet_name'] = vet[1]
                session['furrvet_vet_email'] = vet[2]
                session['furrvet_clinic_name'] = vet[7]
                conn.close()
                return redirect(url_for('furrvet.dashboard'))
        
        conn.close()
        flash('Invalid FurrVet credentials')
    
    return render_template('furrvet/furrvet_login.html')

@furrvet_bp.route('/logout')
def vet_logout():
    session.pop('furrvet_vet_id', None)
    session.pop('furrvet_vet_name', None)
    session.pop('furrvet_vet_email', None)
    session.pop('furrvet_clinic_name', None)
    return redirect(url_for('furrvet.vet_login'))

@furrvet_bp.route('/dashboard')
@furrvet_login_required
def dashboard():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE vet_id = ? AND DATE(appointment_date) = DATE('now')
    """, (vet_id,))
    today_appointments = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM pets")
    total_patients = c.fetchone()[0]
    
    c.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM invoices 
        WHERE vet_id = ? AND DATE(invoice_date) = DATE('now') AND payment_status = 'paid'
    """, (vet_id,))
    today_revenue = c.fetchone()[0]
    
    c.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE vet_id = ? AND status = 'scheduled'
    """, (vet_id,))
    pending_appointments = c.fetchone()[0]
    
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
    
    return render_template('furrvet/furrvet_dashboard.html', 
                         stats=stats, 
                         recent_appointments=recent_appointments,
                         vet_name=session.get('furrvet_vet_name', ''),
                         clinic_name=session.get('furrvet_clinic_name', ''))

@furrvet_bp.route('/patients')
@furrvet_login_required
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
    
    return render_template('furrvet/furrvet_patients.html', patients=patients, search=search)

@furrvet_bp.route('/patients/<int:pet_id>')
@furrvet_login_required
def patient_detail(pet_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
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
        return redirect(url_for('furrvet.patients'))
    
    c.execute("""
        SELECT mr.*, v.name as vet_name
        FROM medical_records mr
        JOIN vets v ON mr.vet_id = v.id
        WHERE mr.pet_id = ?
        ORDER BY mr.visit_date DESC
    """, (pet_id,))
    medical_records = c.fetchall()
    
    c.execute("""
        SELECT v.*, vt.name as vet_name
        FROM vaccinations v
        JOIN vets vt ON v.vet_id = vt.id
        WHERE v.pet_id = ?
        ORDER BY v.vaccination_date DESC
    """, (pet_id,))
    vaccinations = c.fetchall()
    
    c.execute("""
        SELECT * FROM appointments
        WHERE pet_id = ? AND appointment_date >= DATE('now')
        ORDER BY appointment_date, appointment_time
    """, (pet_id,))
    upcoming_appointments = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_patient_detail.html',
                         pet=pet,
                         medical_records=medical_records,
                         vaccinations=vaccinations,
                         upcoming_appointments=upcoming_appointments)

@furrvet_bp.route('/appointments')
@furrvet_login_required
def appointments():
    vet_id = session['furrvet_vet_id']
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
    
    return render_template('furrvet/furrvet_appointments.html', 
                         appointments=appointments_list, 
                         selected_date=date_filter)

@furrvet_bp.route('/appointments/new', methods=['GET', 'POST'])
@furrvet_login_required
def new_appointment():
    if request.method == 'POST':
        vet_id = session['furrvet_vet_id']
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
        return redirect(url_for('furrvet.appointments'))
    
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
    
    return render_template('furrvet/furrvet_new_appointment.html', pets=pets)

@furrvet_bp.route('/billing')
@furrvet_login_required
def billing():
    vet_id = session['furrvet_vet_id']
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
    
    return render_template('furrvet/furrvet_billing.html', invoices=invoices)

@furrvet_bp.route('/inventory')
@furrvet_login_required
def furrvet_inventory():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM inventory WHERE current_stock <= minimum_stock ORDER BY current_stock")
    low_stock_items = c.fetchall()
    
    c.execute("SELECT * FROM inventory ORDER BY item_name")
    all_items = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_inventory.html', 
                         low_stock_items=low_stock_items, 
                         all_items=all_items)

@furrvet_bp.route('/compliance')
@furrvet_login_required
def compliance():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT d.*, v.name as uploaded_by_name 
        FROM documents d
        LEFT JOIN vets v ON d.uploaded_by = v.id
        WHERE d.expiry_date <= DATE('now', '+30 days')
        ORDER BY d.expiry_date
    """)
    expiring_docs = c.fetchall()
    
    c.execute("""
        SELECT d.*, v.name as uploaded_by_name 
        FROM documents d
        LEFT JOIN vets v ON d.uploaded_by = v.id
        ORDER BY d.upload_date DESC
    """)
    all_docs = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_compliance.html', 
                         expiring_docs=expiring_docs,
                         all_docs=all_docs)

@furrvet_bp.route('/insurance')
@furrvet_login_required
def insurance():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT pi.*, p.name as pet_name, po.name as owner_name
        FROM pet_insurance pi
        JOIN pets p ON pi.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        ORDER BY pi.policy_start_date DESC
    """)
    insurance_policies = c.fetchall()
    
    c.execute("""
        SELECT ic.*, p.name as pet_name, pi.insurance_provider
        FROM insurance_claims ic
        JOIN pets p ON ic.pet_id = p.id
        JOIN pet_insurance pi ON ic.insurance_id = pi.id
        ORDER BY ic.claim_date DESC
        LIMIT 20
    """)
    recent_claims = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_insurance.html',
                         insurance_policies=insurance_policies,
                         recent_claims=recent_claims)

@furrvet_bp.route('/suppliers')
@furrvet_login_required
def suppliers():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM suppliers ORDER BY name")
    suppliers_list = c.fetchall()
    
    c.execute("""
        SELECT po.*, s.name as supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        ORDER BY po.order_date DESC
        LIMIT 10
    """)
    recent_orders = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_suppliers.html',
                         suppliers=suppliers_list,
                         recent_orders=recent_orders)

@furrvet_bp.route('/crm')
@furrvet_login_required
def crm_dashboard():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM crm_campaigns 
        WHERE status = 'active' 
        ORDER BY start_date DESC
    """)
    active_campaigns = c.fetchall()
    
    c.execute("""
        SELECT cr.*, p.name as pet_name, po.name as owner_name
        FROM client_reminders cr
        JOIN pets p ON cr.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE cr.status = 'pending' AND cr.reminder_date <= DATE('now', '+7 days')
        ORDER BY cr.reminder_date
    """)
    pending_reminders = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_crm.html',
                         active_campaigns=active_campaigns,
                         pending_reminders=pending_reminders)

@furrvet_bp.route('/assets')
@furrvet_login_required
def asset_management():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM clinic_assets ORDER BY asset_name")
    assets = c.fetchall()
    
    c.execute("""
        SELECT * FROM clinic_assets 
        WHERE next_maintenance <= DATE('now', '+30 days')
        ORDER BY next_maintenance
    """)
    maintenance_due = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_assets.html',
                         assets=assets,
                         maintenance_due=maintenance_due)

@furrvet_bp.route('/telehealth')
@furrvet_login_required
def telehealth():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT ts.*, p.name as pet_name, po.name as owner_name, po.phone
        FROM telehealth_sessions ts
        JOIN pets p ON ts.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE ts.vet_id = ?
        ORDER BY ts.session_date DESC, ts.session_time DESC
    """, (vet_id,))
    telehealth_sessions = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_telehealth.html',
                         telehealth_sessions=telehealth_sessions)

@furrvet_bp.route('/analytics')
@furrvet_login_required
def advanced_analytics():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            DATE(invoice_date) as date,
            SUM(total_amount) as daily_revenue,
            COUNT(*) as invoice_count
        FROM invoices 
        WHERE vet_id = ? AND invoice_date >= DATE('now', '-30 days')
        GROUP BY DATE(invoice_date)
        ORDER BY date
    """, (vet_id,))
    daily_revenue = c.fetchall()
    
    c.execute("""
        SELECT species, COUNT(*) as count
        FROM pets
        GROUP BY species
        ORDER BY count DESC
    """)
    species_stats = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_analytics.html',
                         daily_revenue=daily_revenue,
                         species_stats=species_stats)

@furrvet_bp.route('/medical-records')
@furrvet_login_required
def medical_records():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT mr.*, p.name as pet_name, po.name as owner_name
        FROM medical_records mr
        JOIN pets p ON mr.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE mr.vet_id = ?
        ORDER BY mr.visit_date DESC
        LIMIT 50
    """, (vet_id,))
    
    records = c.fetchall()
    conn.close()
    
    return render_template('furrvet/furrvet_medical_records.html', records=records)

@furrvet_bp.route('/laboratory')
@furrvet_login_required
def laboratory():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    lab_tests = []
    imaging_records = []
    
    conn.close()
    
    return render_template('furrvet/furrvet_laboratory.html', 
                         lab_tests=lab_tests, 
                         imaging_records=imaging_records)

@furrvet_bp.route('/reports')
@furrvet_login_required
def reports():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END) as pending_amount
        FROM invoices 
        WHERE vet_id = ? AND invoice_date >= date('now', '-30 days')
    """, (vet_id,))
    financial_summary = c.fetchone()
    
    c.execute("""
        SELECT 
            COUNT(*) as total_appointments,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_appointments,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_appointments
        FROM appointments 
        WHERE vet_id = ? AND appointment_date >= date('now', '-30 days')
    """, (vet_id,))
    appointment_stats = c.fetchone()
    
    c.execute("SELECT COUNT(*) FROM pets")
    total_patients = c.fetchone()[0]
    
    c.execute("""
        SELECT appointment_type, COUNT(*) as count
        FROM appointments 
        WHERE vet_id = ? AND appointment_date >= date('now', '-30 days')
        GROUP BY appointment_type
        ORDER BY count DESC
        LIMIT 5
    """, (vet_id,))
    popular_services = c.fetchall()
    
    conn.close()
    
    stats = {
        'financial': financial_summary,
        'appointments': appointment_stats,
        'total_patients': total_patients,
        'popular_services': popular_services
    }
    
    return render_template('furrvet/furrvet_reports.html', stats=stats)

@furrvet_bp.route('/hospitalization')
@furrvet_login_required
def hospitalization():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""
        SELECT h.*, p.name as pet_name, po.name as owner_name
        FROM hospitalizations h
        JOIN pets p ON h.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE h.vet_id = ?
        ORDER BY h.admission_date DESC
    """, (vet_id,))
    hospitalizations = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_hospitalization.html', hospitalizations=hospitalizations)


@furrvet_bp.route('/patients/new', methods=['GET', 'POST'])
@furrvet_login_required
def add_patient():
    if request.method == 'POST':
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        owner_phone = request.form.get('owner_phone', '').strip()
        c.execute("SELECT id FROM pet_owners WHERE phone=?", (owner_phone,))
        existing = c.fetchone()
        if existing:
            owner_id = existing[0]
            c.execute("""UPDATE pet_owners SET name=?, email=?, address=?, city=?, emergency_contact=?
                WHERE id=?""", (
                request.form.get('owner_name', '').strip(),
                request.form.get('owner_email', '').strip() or None,
                request.form.get('owner_address', '').strip(),
                request.form.get('owner_city', '').strip(),
                request.form.get('emergency_contact', '').strip(),
                owner_id))
        else:
            c.execute("""INSERT INTO pet_owners (name, email, phone, address, city, emergency_contact)
                VALUES (?,?,?,?,?,?)""", (
                request.form.get('owner_name', '').strip(),
                request.form.get('owner_email', '').strip() or None,
                owner_phone,
                request.form.get('owner_address', '').strip(),
                request.form.get('owner_city', '').strip(),
                request.form.get('emergency_contact', '').strip()))
            owner_id = c.lastrowid
        microchip = request.form.get('microchip_id', '').strip() or None
        c.execute("""INSERT INTO pets (name, species, breed, gender, date_of_birth, weight, color,
            distinguishing_marks, microchip_id, allergies, medical_conditions, insurance_info, owner_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form.get('pet_name', '').strip(),
            request.form.get('species', ''),
            request.form.get('breed', '').strip(),
            request.form.get('gender', ''),
            request.form.get('date_of_birth', '') or None,
            request.form.get('weight', type=float) or None,
            request.form.get('color', '').strip(),
            request.form.get('distinguishing_marks', '').strip(),
            microchip,
            request.form.get('allergies', '').strip(),
            request.form.get('medical_conditions', '').strip(),
            request.form.get('insurance_info', '').strip(),
            owner_id))
        pet_id = c.lastrowid
        conn.commit()
        conn.close()
        flash(f"Patient {request.form.get('pet_name', '')} registered successfully!")
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    return render_template('furrvet/add_patient.html')


@furrvet_bp.route('/patients/<int:pet_id>/edit', methods=['GET', 'POST'])
@furrvet_login_required
def edit_patient(pet_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT p.*, po.name as owner_name, po.email as owner_email,
        po.phone as owner_phone, po.address as owner_address, po.city as owner_city,
        po.emergency_contact as owner_emergency
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id WHERE p.id=?""", (pet_id,))
    pet = c.fetchone()
    if not pet:
        conn.close()
        flash('Patient not found')
        return redirect(url_for('furrvet.patients'))
    if request.method == 'POST':
        c.execute("""UPDATE pet_owners SET name=?, email=?, phone=?, address=?, city=?, emergency_contact=?
            WHERE id=?""", (
            request.form.get('owner_name', '').strip(),
            request.form.get('owner_email', '').strip() or None,
            request.form.get('owner_phone', '').strip(),
            request.form.get('owner_address', '').strip(),
            request.form.get('owner_city', '').strip(),
            request.form.get('emergency_contact', '').strip(),
            pet[8]))
        microchip = request.form.get('microchip_id', '').strip() or None
        c.execute("""UPDATE pets SET name=?, species=?, breed=?, gender=?, date_of_birth=?,
            weight=?, color=?, distinguishing_marks=?, microchip_id=?, allergies=?,
            medical_conditions=?, insurance_info=? WHERE id=?""", (
            request.form.get('pet_name', '').strip(),
            request.form.get('species', ''),
            request.form.get('breed', '').strip(),
            request.form.get('gender', ''),
            request.form.get('date_of_birth', '') or None,
            request.form.get('weight', type=float) or None,
            request.form.get('color', '').strip(),
            request.form.get('distinguishing_marks', '').strip(),
            microchip,
            request.form.get('allergies', '').strip(),
            request.form.get('medical_conditions', '').strip(),
            request.form.get('insurance_info', '').strip(),
            pet_id))
        conn.commit()
        conn.close()
        flash('Patient updated successfully!')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    conn.close()
    return render_template('furrvet/edit_patient.html', pet=pet)


@furrvet_bp.route('/patients/<int:pet_id>/photo', methods=['POST'])
@furrvet_login_required
def upload_patient_photo(pet_id):
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    file = request.files['photo']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file'}), 400
    filename = secure_filename(f"pet_{pet_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("UPDATE pets SET photo_url=? WHERE id=?", (f"/static/furrvet/uploads/{filename}", pet_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'photo_url': f"/static/furrvet/uploads/{filename}"})


@furrvet_bp.route('/patients/<int:pet_id>/medical/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_medical_record(pet_id):
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT p.*, po.name as owner_name, po.email as owner_email
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id WHERE p.id=?""", (pet_id,))
    pet = c.fetchone()
    if not pet:
        conn.close()
        flash('Patient not found')
        return redirect(url_for('furrvet.patients'))
    c.execute("""SELECT id, appointment_date, appointment_time, appointment_type
        FROM appointments WHERE pet_id=? AND DATE(appointment_date)=DATE('now') AND vet_id=?
        ORDER BY appointment_time""", (pet_id, vet_id))
    today_appointments = c.fetchall()
    if request.method == 'POST':
        owner_observations = request.form.get('owner_observations', '').strip()
        duration_symptoms = request.form.get('duration_symptoms', '').strip()
        history_notes = request.form.get('history_notes', '').strip()
        bcs_score = request.form.get('bcs_score', '').strip()
        mucous_membranes = request.form.get('mucous_membranes', '').strip()
        crt = request.form.get('capillary_refill_time', '').strip()
        differential = request.form.get('differential_diagnoses', '').strip()
        prognosis = request.form.get('prognosis', '').strip()
        dietary = request.form.get('dietary_recommendations', '').strip()
        activity = request.form.get('activity_restrictions', '').strip()
        subjective_json = json.dumps({
            'chief_complaint': request.form.get('chief_complaint', '').strip(),
            'owner_observations': owner_observations,
            'duration_symptoms': duration_symptoms,
            'history_notes': history_notes
        })
        objective_json = json.dumps({
            'bcs_score': bcs_score,
            'mucous_membranes': mucous_membranes,
            'capillary_refill_time': crt,
            'physical_examination': request.form.get('physical_examination', '').strip()
        })
        assessment_json = json.dumps({
            'differential_diagnoses': differential,
            'prognosis': prognosis
        })
        plan_json = json.dumps({
            'dietary_recommendations': dietary,
            'activity_restrictions': activity
        })
        full_exam = f"SUBJECTIVE: {subjective_json}\nOBJECTIVE: {objective_json}\nASSESSMENT: {assessment_json}\nPLAN: {plan_json}"
        appt_id = request.form.get('appointment_id', type=int) or None
        c.execute("""INSERT INTO medical_records (pet_id, vet_id, appointment_id, visit_date,
            chief_complaint, physical_examination, diagnosis, treatment_plan, prescription,
            follow_up_instructions, vitals_temperature, vitals_weight, vitals_heart_rate,
            vitals_respiratory_rate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            pet_id, vet_id, appt_id,
            request.form.get('visit_date', datetime.now().strftime('%Y-%m-%d')),
            request.form.get('chief_complaint', '').strip(),
            full_exam,
            request.form.get('diagnosis', '').strip(),
            request.form.get('treatment_plan', '').strip(),
            request.form.get('prescription', '').strip(),
            request.form.get('follow_up_instructions', '').strip(),
            request.form.get('temperature', type=float),
            request.form.get('weight', type=float),
            request.form.get('heart_rate', type=int),
            request.form.get('respiratory_rate', type=int)))
        record_id = c.lastrowid
        if request.form.get('follow_up_required') and request.form.get('follow_up_date'):
            c.execute("""INSERT INTO appointments (pet_id, vet_id, appointment_date, appointment_time,
                appointment_type, status, reason) VALUES (?,?,?,?,?,?,?)""", (
                pet_id, vet_id, request.form.get('follow_up_date'), '10:00', 'Follow Up',
                'scheduled', f"Follow up for: {request.form.get('diagnosis', '')}"))
        prescription_text = request.form.get('prescription', '').strip()
        if prescription_text and pet:
            owner_email = pet[-5] if pet else None
            if owner_email:
                try:
                    from main import bridge_furrvet_to_reminder
                    bridge_furrvet_to_reminder(
                        owner_email, pet[1], f"Prescription from visit",
                        prescription_text, request.form.get('follow_up_date', ''),
                        session.get('furrvet_clinic_name', ''),
                        prescription_text[:50], '', '')
                except Exception:
                    pass
        conn.commit()
        conn.close()
        flash('Medical record saved successfully!')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    conn.close()
    return render_template('furrvet/add_medical_record.html', pet=pet, today_appointments=today_appointments,
        vet_name=session.get('furrvet_vet_name', ''))


@furrvet_bp.route('/patients/<int:pet_id>/medical/<int:record_id>')
@furrvet_login_required
def view_medical_record(pet_id, record_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT mr.*, v.name as vet_name, v.license_number
        FROM medical_records mr JOIN vets v ON mr.vet_id = v.id
        WHERE mr.id=? AND mr.pet_id=?""", (record_id, pet_id))
    record = c.fetchone()
    if not record:
        conn.close()
        flash('Record not found')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    c.execute("""SELECT p.*, po.name as owner_name, po.phone as owner_phone
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id WHERE p.id=?""", (pet_id,))
    pet = c.fetchone()
    conn.close()
    return render_template('furrvet/view_medical_record.html', record=record, pet=pet,
        clinic_name=session.get('furrvet_clinic_name', ''))


@furrvet_bp.route('/patients/<int:pet_id>/vaccinations/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_vaccination(pet_id):
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT p.*, po.name as owner_name, po.email as owner_email
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id WHERE p.id=?""", (pet_id,))
    pet = c.fetchone()
    if not pet:
        conn.close()
        flash('Patient not found')
        return redirect(url_for('furrvet.patients'))
    if request.method == 'POST':
        vaccine_name = request.form.get('vaccine_name', '')
        if vaccine_name == 'Other':
            vaccine_name = request.form.get('vaccine_name_other', '').strip()
        next_due = request.form.get('next_due_date', '')
        if not next_due:
            vacc_date = request.form.get('vaccination_date', datetime.now().strftime('%Y-%m-%d'))
            try:
                vd = datetime.strptime(vacc_date, '%Y-%m-%d')
                if 'Rabies' in vaccine_name:
                    next_due = (vd + timedelta(days=365)).strftime('%Y-%m-%d')
                else:
                    next_due = (vd + timedelta(days=365)).strftime('%Y-%m-%d')
            except Exception:
                next_due = None
        c.execute("""INSERT INTO vaccinations (pet_id, vet_id, vaccine_name, vaccine_type,
            batch_number, manufacturer, vaccination_date, next_due_date, site_of_injection,
            adverse_reactions) VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            pet_id, vet_id, vaccine_name,
            request.form.get('vaccine_type', ''),
            request.form.get('batch_number', '').strip(),
            request.form.get('manufacturer', '').strip(),
            request.form.get('vaccination_date', datetime.now().strftime('%Y-%m-%d')),
            next_due,
            request.form.get('site_of_injection', ''),
            request.form.get('adverse_reactions', '').strip()))
        vacc_id = c.lastrowid
        owner_email = pet[-5] if pet else None
        if owner_email:
            try:
                conn_erp = sqlite3.connect('erp.db')
                c_erp = conn_erp.cursor()
                c_erp.execute("""INSERT OR REPLACE INTO pawsport_documents
                    (pet_index, user_email, document_type, document_name, verified, verified_by,
                    issued_by, upload_date) VALUES (
                    (SELECT pet_index FROM pawsport_documents WHERE user_email=? LIMIT 1),
                    ?, 'Vaccination Records', ?, 1, 'furrvet', ?, DATE('now'))""",
                    (owner_email, owner_email, f"{vaccine_name} vaccination",
                     session.get('furrvet_clinic_name', '')))
                conn_erp.commit()
                conn_erp.close()
            except Exception:
                pass
            if next_due:
                try:
                    from main import bridge_furrvet_to_reminder
                    bridge_furrvet_to_reminder(
                        owner_email, pet[1], f"{vaccine_name} vaccination due",
                        f"Next {vaccine_name} vaccination is due", next_due,
                        session.get('furrvet_clinic_name', ''),
                        vaccine_name, '', 'Once')
                except Exception:
                    pass
        conn.commit()
        conn.close()
        flash('Vaccination recorded successfully!')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    conn.close()
    return render_template('furrvet/add_vaccination.html', pet=pet)


@furrvet_bp.route('/patients/<int:pet_id>/vaccinations/<int:vacc_id>/certificate')
@furrvet_login_required
def vaccination_certificate(pet_id, vacc_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT v.*, p.name as pet_name, p.species, p.breed, po.name as owner_name,
        vt.name as vet_name, vt.license_number, vt.clinic_name
        FROM vaccinations v
        JOIN pets p ON v.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        JOIN vets vt ON v.vet_id = vt.id
        WHERE v.id=? AND v.pet_id=?""", (vacc_id, pet_id))
    vacc = c.fetchone()
    conn.close()
    if not vacc:
        flash('Vaccination record not found')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    return render_template('furrvet/vaccination_certificate.html', vacc=vacc,
        clinic_name=session.get('furrvet_clinic_name', ''))


@furrvet_bp.route('/lab/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_lab_test():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT id, name, species FROM pets ORDER BY name")
    all_pets = c.fetchall()
    if request.method == 'POST':
        test_name = request.form.get('test_name', '')
        if test_name == 'Other':
            test_name = request.form.get('test_name_other', '').strip()
        pet_id = request.form.get('pet_id', type=int)
        c.execute("""INSERT INTO lab_tests (pet_id, vet_id, test_name, test_type, ordered_date,
            external_lab, cost, status) VALUES (?,?,?,?,?,?,?,?)""", (
            pet_id, vet_id, test_name,
            request.form.get('test_type', ''),
            request.form.get('ordered_date', datetime.now().strftime('%Y-%m-%d')),
            request.form.get('external_lab', '').strip(),
            request.form.get('cost', type=float),
            'pending'))
        conn.commit()
        test_id = c.lastrowid
        conn.close()
        flash('Lab test ordered successfully!')
        return redirect(url_for('furrvet.patient_detail', pet_id=pet_id))
    conn.close()
    return render_template('furrvet/add_lab_test.html', pets=all_pets)


@furrvet_bp.route('/lab/<int:test_id>/results', methods=['GET', 'POST'])
@furrvet_login_required
def enter_lab_results(test_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT lt.*, p.name as pet_name, p.species, po.name as owner_name, po.email as owner_email
        FROM lab_tests lt
        JOIN pets p ON lt.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE lt.id=? AND lt.vet_id=?""", (test_id, session['furrvet_vet_id']))
    test = c.fetchone()
    if not test:
        conn.close()
        flash('Test not found')
        return redirect(url_for('furrvet.laboratory'))
    ref_values = get_reference_values(test[3])
    if request.method == 'POST':
        abnormal = request.form.getlist('abnormal_flags')
        c.execute("""UPDATE lab_tests SET results=?, reference_values=?, completed_date=?,
            lab_technician=?, status=? WHERE id=?""", (
            request.form.get('results', '').strip(),
            request.form.get('reference_values', '').strip(),
            request.form.get('completed_date', datetime.now().strftime('%Y-%m-%d')),
            request.form.get('lab_technician', '').strip(),
            'completed' if request.form.get('mark_complete') else 'in_progress',
            test_id))
        if abnormal and test[-1]:
            try:
                from main import bridge_furrvet_to_reminder
                bridge_furrvet_to_reminder(
                    test[-1], test[-4], f"Abnormal lab results: {test[3]}",
                    f"Abnormal values found in {test[3]}. Please contact the clinic.",
                    datetime.now().strftime('%Y-%m-%d'),
                    session.get('furrvet_clinic_name', ''),
                    test[3], '', 'Urgent')
            except Exception:
                pass
        conn.commit()
        conn.close()
        flash('Results entered successfully!')
        return redirect(url_for('furrvet.patient_detail', pet_id=test[1]))
    conn.close()
    return render_template('furrvet/enter_results.html', test=test, ref_values=ref_values)


def get_reference_values(test_name):
    refs = {
        'Complete Blood Count (CBC)': 'RBC: 5.5-8.5 M/uL, WBC: 5.5-16.9 K/uL, Platelets: 175-500 K/uL, Hgb: 12-18 g/dL, HCT: 37-55%',
        'Blood Chemistry Panel': 'BUN: 7-27 mg/dL, Creatinine: 0.5-1.8 mg/dL, ALT: 10-125 U/L, ALP: 23-212 U/L, Glucose: 74-143 mg/dL',
        'Urinalysis': 'pH: 6.0-7.5, Specific Gravity: 1.015-1.045, Protein: Negative, Glucose: Negative',
        'Thyroid Panel (T4)': 'Total T4: 1.0-4.0 ug/dL, Free T4: 0.7-2.0 ng/dL',
    }
    return refs.get(test_name, '')


@furrvet_bp.route('/hospitalize', methods=['GET', 'POST'])
@furrvet_login_required
def admit_patient():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT id, name, species FROM pets ORDER BY name")
    all_pets = c.fetchall()
    if request.method == 'POST':
        pet_id = request.form.get('pet_id', type=int)
        c.execute("""INSERT INTO hospitalizations (pet_id, vet_id, admission_date, reason,
            bed_number, ward_type, feeding_instructions, medication_schedule, daily_notes, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            pet_id, vet_id,
            request.form.get('admission_date', datetime.now().strftime('%Y-%m-%d')),
            request.form.get('reason', '').strip(),
            request.form.get('bed_number', '').strip(),
            request.form.get('ward_type', ''),
            request.form.get('feeding_instructions', '').strip(),
            request.form.get('medication_schedule', '').strip(),
            json.dumps([{'date': datetime.now().strftime('%Y-%m-%d'),
                         'note': request.form.get('initial_notes', '').strip(),
                         'by': session.get('furrvet_vet_name', '')}]),
            'admitted'))
        conn.commit()
        hosp_id = c.lastrowid
        conn.close()
        flash('Patient admitted successfully!')
        return redirect(url_for('furrvet.hospitalization_detail', hosp_id=hosp_id))
    conn.close()
    return render_template('furrvet/admit_patient.html', pets=all_pets)


@furrvet_bp.route('/hospitalization/<int:hosp_id>', methods=['GET', 'POST'])
@furrvet_login_required
def hospitalization_detail(hosp_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT h.*, p.name as pet_name, p.species, po.name as owner_name, po.phone
        FROM hospitalizations h
        JOIN pets p ON h.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE h.id=? AND h.vet_id=?""", (hosp_id, session['furrvet_vet_id']))
    hosp = c.fetchone()
    if not hosp:
        conn.close()
        flash('Record not found')
        return redirect(url_for('furrvet.hospitalization'))
    if request.method == 'POST':
        daily_notes = json.loads(hosp[8] or '[]')
        daily_notes.append({
            'date': request.form.get('note_date', datetime.now().strftime('%Y-%m-%d')),
            'note': request.form.get('daily_note', '').strip(),
            'vitals': request.form.get('vitals', '').strip(),
            'by': session.get('furrvet_vet_name', '')
        })
        c.execute("UPDATE hospitalizations SET daily_notes=? WHERE id=?",
            (json.dumps(daily_notes), hosp_id))
        conn.commit()
        flash('Daily note added!')
        c.execute("""SELECT h.*, p.name as pet_name, p.species, po.name as owner_name, po.phone
            FROM hospitalizations h JOIN pets p ON h.pet_id = p.id
            JOIN pet_owners po ON p.owner_id = po.id WHERE h.id=? AND h.vet_id=?""", (hosp_id, session['furrvet_vet_id']))
        hosp = c.fetchone()
    notes = json.loads(hosp[8] or '[]') if hosp[8] else []
    conn.close()
    return render_template('furrvet/hospitalization_detail.html', hosp=hosp, daily_notes=notes)


@furrvet_bp.route('/hospitalization/<int:hosp_id>/discharge', methods=['GET', 'POST'])
@furrvet_login_required
def discharge_patient(hosp_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT h.*, p.name as pet_name, p.species, po.name as owner_name
        FROM hospitalizations h JOIN pets p ON h.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id WHERE h.id=? AND h.vet_id=?""", (hosp_id, session['furrvet_vet_id']))
    hosp = c.fetchone()
    if not hosp:
        conn.close()
        flash('Record not found')
        return redirect(url_for('furrvet.hospitalization'))
    if request.method == 'POST':
        daily_notes = json.loads(hosp[8] or '[]')
        daily_notes.append({
            'date': request.form.get('discharge_date', datetime.now().strftime('%Y-%m-%d')),
            'note': f"DISCHARGE: {request.form.get('discharge_summary', '')}",
            'by': session.get('furrvet_vet_name', '')
        })
        c.execute("""UPDATE hospitalizations SET status='discharged', discharge_date=?,
            daily_notes=? WHERE id=?""", (
            request.form.get('discharge_date', datetime.now().strftime('%Y-%m-%d')),
            json.dumps(daily_notes), hosp_id))
        if request.form.get('follow_up_date'):
            c.execute("""INSERT INTO appointments (pet_id, vet_id, appointment_date, appointment_time,
                appointment_type, status, reason) VALUES (?,?,?,?,?,?,?)""", (
                hosp[1], hosp[2], request.form.get('follow_up_date'), '10:00',
                'Post-Hospitalization Follow Up', 'scheduled',
                f"Follow up after hospitalization for: {hosp[4]}"))
        conn.commit()
        conn.close()
        flash('Patient discharged successfully!')
        return redirect(url_for('furrvet.hospitalization'))
    conn.close()
    return render_template('furrvet/discharge_patient.html', hosp=hosp)


@furrvet_bp.route('/billing/new', methods=['GET', 'POST'])
@furrvet_login_required
def create_invoice():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT p.id, p.name, p.species, po.name as owner_name, po.id as owner_id
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id ORDER BY p.name""")
    all_pets = c.fetchall()
    if request.method == 'POST':
        pet_id = request.form.get('pet_id', type=int)
        c.execute("SELECT owner_id FROM pets WHERE id=?", (pet_id,))
        owner_row = c.fetchone()
        owner_id = owner_row[0] if owner_row else 1
        c.execute("SELECT COUNT(*) FROM invoices WHERE vet_id=?", (vet_id,))
        seq = c.fetchone()[0] + 1
        inv_num = f"INV-{vet_id}-{datetime.now().year}-{seq:04d}"
        descriptions = request.form.getlist('item_description[]')
        item_types = request.form.getlist('item_type[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        subtotal = 0
        items = []
        for i in range(len(descriptions)):
            if descriptions[i].strip():
                qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0
                total = qty * price
                subtotal += total
                items.append((descriptions[i].strip(),
                    item_types[i] if i < len(item_types) else '',
                    qty, price, total))
        tax_rate = request.form.get('tax_rate', 18.0, type=float)
        discount_rate = request.form.get('discount_rate', 0.0, type=float)
        tax_amount = subtotal * tax_rate / 100
        discount_amount = subtotal * discount_rate / 100
        total_amount = subtotal + tax_amount - discount_amount
        c.execute("""INSERT INTO invoices (invoice_number, pet_id, owner_id, vet_id, invoice_date,
            due_date, subtotal, tax_rate, tax_amount, discount_rate, discount_amount, total_amount,
            payment_status, payment_method, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            inv_num, pet_id, owner_id, vet_id,
            request.form.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
            request.form.get('due_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
            subtotal, tax_rate, tax_amount, discount_rate, discount_amount, total_amount,
            request.form.get('payment_status', 'pending'),
            request.form.get('payment_method', ''),
            request.form.get('notes', '').strip()))
        inv_id = c.lastrowid
        for item in items:
            c.execute("""INSERT INTO invoice_items (invoice_id, item_description, item_type,
                quantity, unit_price, total_price) VALUES (?,?,?,?,?,?)""",
                (inv_id, item[0], item[1], item[2], item[3], item[4]))
        conn.commit()
        conn.close()
        flash('Invoice created successfully!')
        return redirect(url_for('furrvet.view_invoice', inv_id=inv_id))
    conn.close()
    return render_template('furrvet/create_invoice.html', pets=all_pets,
        today=datetime.now().strftime('%Y-%m-%d'),
        due_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))


@furrvet_bp.route('/billing/<int:inv_id>')
@furrvet_login_required
def view_invoice(inv_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT i.*, p.name as pet_name, p.species, po.name as owner_name,
        po.phone as owner_phone, po.address as owner_address, po.email as owner_email,
        v.name as vet_name, v.license_number, v.clinic_name
        FROM invoices i
        JOIN pets p ON i.pet_id = p.id
        JOIN pet_owners po ON i.owner_id = po.id
        JOIN vets v ON i.vet_id = v.id
        WHERE i.id=?""", (inv_id,))
    invoice = c.fetchone()
    if not invoice:
        conn.close()
        flash('Invoice not found')
        return redirect(url_for('furrvet.billing'))
    c.execute("SELECT * FROM invoice_items WHERE invoice_id=?", (inv_id,))
    items = c.fetchall()
    conn.close()
    return render_template('furrvet/view_invoice.html', invoice=invoice, items=items,
        clinic_name=session.get('furrvet_clinic_name', ''))


@furrvet_bp.route('/billing/<int:inv_id>/pay', methods=['POST'])
@furrvet_login_required
def pay_invoice(inv_id):
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""UPDATE invoices SET payment_status='paid', payment_date=?,
        payment_method=? WHERE id=? AND vet_id=?""", (
        datetime.now().strftime('%Y-%m-%d'),
        request.form.get('payment_method', 'Cash'), inv_id, vet_id))
    conn.commit()
    conn.close()
    flash('Payment recorded successfully!')
    return redirect(url_for('furrvet.view_invoice', inv_id=inv_id))


@furrvet_bp.route('/inventory/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_inventory():
    if request.method == 'POST':
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        c.execute("""INSERT INTO inventory (item_name, item_type, category, brand,
            unit_of_measure, current_stock, minimum_stock, unit_cost, selling_price,
            supplier, batch_number, expiry_date, location) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form.get('item_name', '').strip(),
            request.form.get('item_type', ''),
            request.form.get('category', '').strip(),
            request.form.get('brand', '').strip(),
            request.form.get('unit_of_measure', ''),
            request.form.get('current_stock', 0, type=int),
            request.form.get('minimum_stock', 10, type=int),
            request.form.get('unit_cost', type=float),
            request.form.get('selling_price', type=float),
            request.form.get('supplier', '').strip(),
            request.form.get('batch_number', '').strip(),
            request.form.get('expiry_date', '') or None,
            request.form.get('location', '').strip()))
        conn.commit()
        conn.close()
        flash('Inventory item added successfully!')
        return redirect(url_for('furrvet.furrvet_inventory'))
    return render_template('furrvet/add_inventory.html')


@furrvet_bp.route('/inventory/<int:item_id>/restock', methods=['POST'])
@furrvet_login_required
def restock_inventory(item_id):
    qty = request.form.get('quantity_added', 0, type=int)
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("UPDATE inventory SET current_stock = current_stock + ?, batch_number=?, expiry_date=?, supplier=? WHERE id=?", (
        qty, request.form.get('batch_number', '').strip(),
        request.form.get('expiry_date', '') or None,
        request.form.get('supplier', '').strip(), item_id))
    conn.commit()
    conn.close()
    flash(f'Stock updated: +{qty} units')
    return redirect(url_for('furrvet.furrvet_inventory'))


@furrvet_bp.route('/staff/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_staff():
    if request.method == 'POST':
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        c.execute("""INSERT INTO staff (name, email, phone, role, department, salary,
            hire_date, shift_timing, qualifications, emergency_contact)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            request.form.get('name', '').strip(),
            request.form.get('email', '').strip() or None,
            request.form.get('phone', '').strip(),
            request.form.get('role', ''),
            request.form.get('department', ''),
            request.form.get('salary', type=float),
            request.form.get('hire_date', '') or None,
            request.form.get('shift_timing', '').strip(),
            request.form.get('qualifications', '').strip(),
            request.form.get('emergency_contact', '').strip()))
        conn.commit()
        conn.close()
        flash('Staff member added successfully!')
        return redirect(url_for('furrvet.staff_management'))
    return render_template('furrvet/add_staff.html')


@furrvet_bp.route('/staff/<int:staff_id>/certification/add', methods=['GET', 'POST'])
@furrvet_login_required
def add_staff_certification(staff_id):
    if request.method == 'POST':
        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        doc_path = None
        if 'document' in request.files:
            file = request.files['document']
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(f"cert_{staff_id}_{datetime.now().strftime('%Y%m%d')}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                doc_path = f"/static/furrvet/uploads/{filename}"
        c.execute("""INSERT INTO staff_certifications (staff_id, certification_name, issuing_body,
            issue_date, expiry_date, document_path) VALUES (?,?,?,?,?,?)""", (
            staff_id,
            request.form.get('certification_name', '').strip(),
            request.form.get('issuing_body', '').strip(),
            request.form.get('issue_date', '') or None,
            request.form.get('expiry_date', '') or None,
            doc_path))
        conn.commit()
        conn.close()
        flash('Certification added successfully!')
        return redirect(url_for('furrvet.staff_management'))
    return render_template('furrvet/add_certification.html', staff_id=staff_id)


@furrvet_bp.route('/appointments/<int:appt_id>/update', methods=['POST'])
@furrvet_login_required
def update_appointment(appt_id):
    status = request.form.get('status', '')
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    vet_id = session['furrvet_vet_id']
    c.execute("UPDATE appointments SET status=? WHERE id=? AND vet_id=?", (status, appt_id, vet_id))
    conn.commit()
    if status == 'completed':
        c.execute("SELECT pet_id FROM appointments WHERE id=?", (appt_id,))
        row = c.fetchone()
        if row:
            c.execute("SELECT COUNT(*) FROM medical_records WHERE appointment_id=?", (appt_id,))
            if c.fetchone()[0] == 0:
                flash("Don't forget to add a SOAP note for this appointment")
    conn.close()
    flash(f'Appointment status updated to {status}')
    return redirect(url_for('furrvet.appointments'))


@furrvet_bp.route('/appointments/calendar')
@furrvet_login_required
def appointment_calendar():
    vet_id = session['furrvet_vet_id']
    import calendar
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT DATE(appointment_date) as d, COUNT(*) as cnt
        FROM appointments WHERE vet_id=?
        AND strftime('%%Y', appointment_date)=? AND strftime('%%m', appointment_date)=?
        GROUP BY d""", (vet_id, str(year), f"{month:02d}"))
    day_counts = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    cal = calendar.Calendar()
    weeks = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return render_template('furrvet/appointment_calendar.html',
        weeks=weeks, day_counts=day_counts, year=year, month=month,
        month_name=month_name, prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year)


@furrvet_bp.route('/prescriptions/new', methods=['GET', 'POST'])
@furrvet_login_required
def new_prescription():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT p.id, p.name, p.species, po.name as owner_name
        FROM pets p JOIN pet_owners po ON p.owner_id = po.id ORDER BY p.name""")
    all_pets = c.fetchall()
    c.execute("SELECT item_name FROM inventory WHERE item_type='Medication' ORDER BY item_name")
    medications = [r[0] for r in c.fetchall()]
    if request.method == 'POST':
        pet_id = request.form.get('pet_id', type=int)
        drug_names = request.form.getlist('drug_name[]')
        strengths = request.form.getlist('strength[]')
        forms = request.form.getlist('drug_form[]')
        doses = request.form.getlist('dose[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('drug_instructions[]')
        prescription_lines = []
        for i in range(len(drug_names)):
            if drug_names[i].strip():
                line = f"{drug_names[i].strip()}"
                if i < len(strengths) and strengths[i]: line += f" {strengths[i]}"
                if i < len(forms) and forms[i]: line += f" ({forms[i]})"
                if i < len(doses) and doses[i]: line += f" - {doses[i]}"
                if i < len(frequencies) and frequencies[i]: line += f" {frequencies[i]}"
                if i < len(durations) and durations[i]: line += f" for {durations[i]}"
                if i < len(instructions) and instructions[i]: line += f" [{instructions[i]}]"
                prescription_lines.append(line)
        prescription_text = '\n'.join(prescription_lines)
        general_instructions = request.form.get('general_instructions', '').strip()
        if general_instructions:
            prescription_text += f"\n\nGeneral: {general_instructions}"
        c.execute("""INSERT INTO medical_records (pet_id, vet_id, visit_date, chief_complaint,
            diagnosis, prescription, treatment_plan) VALUES (?,?,?,?,?,?,?)""", (
            pet_id, vet_id, request.form.get('rx_date', datetime.now().strftime('%Y-%m-%d')),
            'Prescription', 'Prescription', prescription_text,
            f"Refill: {'Yes' if request.form.get('refill_allowed') else 'No'}"))
        rx_id = c.lastrowid
        c.execute("""SELECT p.name, po.email FROM pets p
            JOIN pet_owners po ON p.owner_id = po.id WHERE p.id=?""", (pet_id,))
        pet_info = c.fetchone()
        if pet_info and pet_info[1]:
            for i in range(len(drug_names)):
                if drug_names[i].strip():
                    try:
                        from main import bridge_furrvet_to_reminder
                        bridge_furrvet_to_reminder(
                            pet_info[1], pet_info[0], f"Rx: {drug_names[i]}",
                            instructions[i] if i < len(instructions) else '',
                            '', session.get('furrvet_clinic_name', ''),
                            drug_names[i], doses[i] if i < len(doses) else '',
                            frequencies[i] if i < len(frequencies) else '')
                    except Exception:
                        pass
        conn.commit()
        conn.close()
        flash('Prescription created successfully!')
        return redirect(url_for('furrvet.view_prescription', rx_id=rx_id))
    conn.close()
    return render_template('furrvet/prescription.html', pets=all_pets, medications=medications,
        vet_name=session.get('furrvet_vet_name', ''),
        vet_license=session.get('furrvet_vet_license', ''))


@furrvet_bp.route('/prescriptions/<int:rx_id>')
@furrvet_login_required
def view_prescription(rx_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT mr.*, p.name as pet_name, p.species, p.breed, po.name as owner_name,
        po.phone as owner_phone, v.name as vet_name, v.license_number, v.clinic_name
        FROM medical_records mr
        JOIN pets p ON mr.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        JOIN vets v ON mr.vet_id = v.id
        WHERE mr.id=? AND mr.chief_complaint='Prescription'""", (rx_id,))
    rx = c.fetchone()
    conn.close()
    if not rx:
        flash('Prescription not found')
        return redirect(url_for('furrvet.patients'))
    return render_template('furrvet/view_prescription.html', rx=rx,
        clinic_name=session.get('furrvet_clinic_name', ''))


@furrvet_bp.route('/staff-management')
@furrvet_login_required
def staff_management():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT * FROM staff WHERE status='active' ORDER BY name")
    staff_list = c.fetchall()
    c.execute("""SELECT sc.*, s.name as staff_name FROM staff_certifications sc
        JOIN staff s ON sc.staff_id = s.id
        WHERE sc.expiry_date IS NOT NULL AND sc.expiry_date <= DATE('now', '+60 days')
        AND sc.status='valid' ORDER BY sc.expiry_date""")
    expiring_certs = c.fetchall()
    c.execute("SELECT sc.*, s.name as staff_name FROM staff_certifications sc JOIN staff s ON sc.staff_id = s.id ORDER BY sc.expiry_date")
    all_certs = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_staff_dashboard.html', staff=staff_list,
        expiring_certs=expiring_certs, all_certs=all_certs)


@furrvet_bp.route('/staff/<int:staff_id>')
@furrvet_login_required
def staff_detail(staff_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT * FROM staff WHERE id=?", (staff_id,))
    member = c.fetchone()
    if not member:
        conn.close()
        flash('Staff member not found')
        return redirect(url_for('furrvet.staff_management'))
    c.execute("SELECT * FROM staff_certifications WHERE staff_id=? ORDER BY expiry_date", (staff_id,))
    certs = c.fetchall()
    conn.close()
    return render_template('furrvet/staff_detail.html', member=member, certs=certs)


@furrvet_bp.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@furrvet_login_required
def edit_staff(staff_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT * FROM staff WHERE id=?", (staff_id,))
    member = c.fetchone()
    if not member:
        conn.close()
        flash('Staff member not found')
        return redirect(url_for('furrvet.staff_management'))
    if request.method == 'POST':
        c.execute("""UPDATE staff SET name=?, email=?, phone=?, role=?, department=?,
            salary=?, shift_timing=?, qualifications=?, emergency_contact=? WHERE id=?""", (
            request.form.get('name', '').strip(),
            request.form.get('email', '').strip() or None,
            request.form.get('phone', '').strip(),
            request.form.get('role', ''),
            request.form.get('department', ''),
            request.form.get('salary', type=float),
            request.form.get('shift_timing', '').strip(),
            request.form.get('qualifications', '').strip(),
            request.form.get('emergency_contact', '').strip(),
            staff_id))
        conn.commit()
        conn.close()
        flash('Staff member updated!')
        return redirect(url_for('furrvet.staff_detail', staff_id=staff_id))
    conn.close()
    return render_template('furrvet/edit_staff.html', member=member)


@furrvet_bp.route('/clients')
@furrvet_login_required
def clients():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT po.*, COUNT(p.id) as pet_count,
        MAX(a.appointment_date) as last_visit,
        COALESCE(SUM(CASE WHEN i.payment_status='paid' THEN i.total_amount ELSE 0 END), 0) as total_spend
        FROM pet_owners po
        LEFT JOIN pets p ON po.id = p.owner_id
        LEFT JOIN appointments a ON p.id = a.pet_id
        LEFT JOIN invoices i ON po.id = i.owner_id
        GROUP BY po.id ORDER BY po.name""")
    owners = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_clients.html', owners=owners)


@furrvet_bp.route('/clients/<int:owner_id>')
@furrvet_login_required
def client_detail(owner_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pet_owners WHERE id=?", (owner_id,))
    owner = c.fetchone()
    if not owner:
        conn.close()
        flash('Client not found')
        return redirect(url_for('furrvet.clients'))
    c.execute("""SELECT p.*, MAX(a.appointment_date) as last_visit
        FROM pets p LEFT JOIN appointments a ON p.id = a.pet_id
        WHERE p.owner_id=? GROUP BY p.id""", (owner_id,))
    pets = c.fetchall()
    c.execute("""SELECT i.* FROM invoices i WHERE i.owner_id=? ORDER BY i.invoice_date DESC LIMIT 20""", (owner_id,))
    invoices = c.fetchall()
    c.execute("""SELECT a.*, p.name as pet_name FROM appointments a
        JOIN pets p ON a.pet_id = p.id WHERE p.owner_id=?
        ORDER BY a.appointment_date DESC LIMIT 20""", (owner_id,))
    appointments = c.fetchall()
    c.execute("""SELECT v.*, p.name as pet_name FROM vaccinations v
        JOIN pets p ON v.pet_id = p.id WHERE p.owner_id=?
        AND (v.next_due_date IS NOT NULL AND v.next_due_date <= DATE('now', '+30 days'))
        ORDER BY v.next_due_date""", (owner_id,))
    due_vaccinations = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_client_detail.html', owner=owner, pets=pets,
        invoices=invoices, appointments=appointments, due_vaccinations=due_vaccinations)


@furrvet_bp.route('/clients/reminders')
@furrvet_login_required
def client_reminders():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    status_filter = request.args.get('status', 'pending')
    c.execute("""SELECT cr.*, p.name as pet_name, po.name as owner_name, po.phone as owner_phone
        FROM client_reminders cr
        JOIN pets p ON cr.pet_id = p.id
        JOIN pet_owners po ON p.owner_id = po.id
        WHERE cr.status=?
        ORDER BY cr.reminder_date""", (status_filter,))
    reminders = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_client_reminders.html', reminders=reminders,
        status_filter=status_filter)


@furrvet_bp.route('/clients/reminders/<int:rem_id>/sent', methods=['POST'])
@furrvet_login_required
def mark_reminder_sent(rem_id):
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("UPDATE client_reminders SET status='sent', sent_date=DATE('now') WHERE id=?", (rem_id,))
    conn.commit()
    conn.close()
    flash('Reminder marked as sent')
    return redirect(url_for('furrvet.client_reminders'))


@furrvet_bp.route('/clients/campaigns', methods=['GET', 'POST'])
@furrvet_login_required
def campaigns():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    if request.method == 'POST':
        target = request.form.get('target_segment', '')
        if target == 'dogs_rabies_due':
            c.execute("""SELECT DISTINCT p.id, p.name, po.name, po.phone
                FROM pets p JOIN pet_owners po ON p.owner_id = po.id
                JOIN vaccinations v ON p.id = v.pet_id
                WHERE p.species='Dog' AND v.vaccine_name LIKE '%Rabies%'
                AND v.next_due_date <= DATE('now', '+30 days')""")
        elif target == 'cats_fvrcp_due':
            c.execute("""SELECT DISTINCT p.id, p.name, po.name, po.phone
                FROM pets p JOIN pet_owners po ON p.owner_id = po.id
                JOIN vaccinations v ON p.id = v.pet_id
                WHERE p.species='Cat' AND v.vaccine_name LIKE '%FVRCP%'
                AND v.next_due_date <= DATE('now', '+30 days')""")
        elif target == 'not_seen_6months':
            c.execute("""SELECT DISTINCT p.id, p.name, po.name, po.phone
                FROM pets p JOIN pet_owners po ON p.owner_id = po.id
                LEFT JOIN appointments a ON p.id = a.pet_id
                GROUP BY p.id
                HAVING MAX(a.appointment_date) < DATE('now', '-180 days')
                OR MAX(a.appointment_date) IS NULL""")
        else:
            c.execute("""SELECT p.id, p.name, po.name, po.phone
                FROM pets p JOIN pet_owners po ON p.owner_id = po.id""")
        target_pets = c.fetchall()
        c.execute("""INSERT INTO crm_campaigns (campaign_name, campaign_type, target_segment,
            start_date, message_template, status, created_by)
            VALUES (?,?,?,DATE('now'),?,?,?)""", (
            request.form.get('campaign_name', '').strip(),
            'reminder', target,
            request.form.get('message_template', '').strip(),
            'active', vet_id))
        conn.commit()
        conn.close()
        flash(f'Campaign created! {len(target_pets)} pets targeted.')
        return render_template('furrvet/furrvet_campaigns.html', target_pets=target_pets, campaigns=[])
    c.execute("SELECT * FROM crm_campaigns ORDER BY created_at DESC LIMIT 20")
    campaigns_list = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_campaigns.html', campaigns=campaigns_list, target_pets=None)


@furrvet_bp.route('/financials')
@furrvet_login_required
def financials():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT COALESCE(SUM(total_amount), 0) FROM invoices
        WHERE vet_id=? AND payment_status='paid' AND DATE(invoice_date)=DATE('now')""", (vet_id,))
    today_revenue = c.fetchone()[0]
    c.execute("""SELECT COALESCE(SUM(total_amount), 0) FROM invoices
        WHERE vet_id=? AND payment_status='paid'
        AND strftime('%%Y-%%m', invoice_date)=strftime('%%Y-%%m', 'now')""", (vet_id,))
    month_revenue = c.fetchone()[0]
    c.execute("""SELECT COALESCE(SUM(total_amount), 0) FROM invoices
        WHERE vet_id=? AND payment_status='pending'""", (vet_id,))
    outstanding = c.fetchone()[0]
    c.execute("""SELECT COALESCE(SUM(total_amount), 0) FROM purchase_orders
        WHERE status='pending'""")
    pending_ap = c.fetchone()[0]
    conn.close()
    return render_template('furrvet/furrvet_financials.html',
        today_revenue=today_revenue, month_revenue=month_revenue,
        outstanding=outstanding, pending_ap=pending_ap)


@furrvet_bp.route('/financials/pnl')
@furrvet_login_required
def pnl_report():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT ii.item_type, COALESCE(SUM(ii.total_price), 0) as revenue
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.vet_id=? AND i.payment_status='paid'
        AND strftime('%%Y-%%m', i.invoice_date)=strftime('%%Y-%%m', 'now')
        GROUP BY ii.item_type ORDER BY revenue DESC""", (vet_id,))
    revenue_by_type = c.fetchall()
    c.execute("""SELECT COALESCE(SUM(total_amount), 0) FROM purchase_orders
        WHERE status='received' AND strftime('%%Y-%%m', order_date)=strftime('%%Y-%%m', 'now')""")
    total_expenses = c.fetchone()[0]
    total_revenue = sum(r[1] for r in revenue_by_type)
    conn.close()
    return render_template('furrvet/furrvet_pnl.html', revenue_by_type=revenue_by_type,
        total_revenue=total_revenue, total_expenses=total_expenses,
        net_profit=total_revenue - total_expenses)


@furrvet_bp.route('/financials/ar')
@furrvet_login_required
def accounts_receivable():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT i.*, po.name as owner_name, po.phone,
        CAST(julianday('now') - julianday(i.invoice_date) AS INTEGER) as days_outstanding
        FROM invoices i JOIN pet_owners po ON i.owner_id = po.id
        WHERE i.vet_id=? AND i.payment_status='pending'
        ORDER BY i.invoice_date""", (vet_id,))
    receivables = c.fetchall()
    conn.close()
    current = [r for r in receivables if r[-1] <= 30]
    overdue = [r for r in receivables if 30 < r[-1] <= 60]
    serious = [r for r in receivables if r[-1] > 60]
    return render_template('furrvet/furrvet_ar.html', current=current, overdue=overdue, serious=serious)


@furrvet_bp.route('/financials/ap')
@furrvet_login_required
def accounts_payable():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT po.*, s.name as supplier_name FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.status='pending' ORDER BY po.order_date""")
    payables = c.fetchall()
    conn.close()
    return render_template('furrvet/furrvet_ap.html', payables=payables)


@furrvet_bp.route('/financials/gst')
@furrvet_login_required
def gst_report():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT COALESCE(SUM(tax_amount), 0) FROM invoices
        WHERE vet_id=? AND payment_status='paid'
        AND strftime('%%Y-%%m', invoice_date)=strftime('%%Y-%%m', 'now')""", (vet_id,))
    gst_collected = c.fetchone()[0]
    c.execute("""SELECT COALESCE(SUM(total_amount * 0.18), 0) FROM purchase_orders
        WHERE status='received' AND strftime('%%Y-%%m', order_date)=strftime('%%Y-%%m', 'now')""")
    gst_paid = c.fetchone()[0]
    conn.close()
    return render_template('furrvet/furrvet_gst.html', gst_collected=gst_collected,
        gst_paid=gst_paid, net_gst=gst_collected - gst_paid)


@furrvet_bp.route('/financials/export/pnl')
@furrvet_login_required
def export_pnl():
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""SELECT ii.item_type, SUM(ii.total_price) as revenue
        FROM invoice_items ii JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.vet_id=? AND i.payment_status='paid'
        GROUP BY ii.item_type ORDER BY revenue DESC""", (vet_id,))
    data = c.fetchall()
    conn.close()
    from flask import Response
    csv_content = "Category,Revenue\n"
    for row in data:
        csv_content += f"{row[0] or 'Other'},{row[1]}\n"
    return Response(csv_content, mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=pnl_report.csv'})

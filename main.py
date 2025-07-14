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
from typing import Optional
from i18n import i18n, t, get_supported_languages, get_current_language

# Import WhatsApp routes
from whatsapp_routes import whatsapp_bp

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
            break_reason TEXT,
            address TEXT,
            state TEXT,
            pincode TEXT
        )
    ''')

    # Add new address columns if they don't exist
    try:
        c.execute("ALTER TABLE vendors ADD COLUMN address TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN state TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN pincode TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

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
        ('marketplace_listing_fee', 0.0, 'Fee for listing products on marketplace'),
        ('offline_transaction_fee', 0.01, 'Commission percentage for offline POS transactions')
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

    # Handler profiles and escrow management tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS handler_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            country TEXT NOT NULL,
            base_price REAL NOT NULL,
            services_offered TEXT,
            experience_years INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 100.0,
            total_bookings INTEGER DEFAULT 0,
            profile_image TEXT,
            bio TEXT,
            languages TEXT,
            certifications TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS handler_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handler_id INTEGER NOT NULL,
            pet_parent_email TEXT NOT NULL,
            pet_name TEXT NOT NULL,
            pet_type TEXT NOT NULL,
            destination_country TEXT NOT NULL,
            travel_date TEXT,
            total_amount REAL NOT NULL,
            handler_fee REAL NOT NULL,
            platform_fee REAL NOT NULL,
            escrow_status TEXT DEFAULT 'held' CHECK(escrow_status IN ('held', 'released', 'refunded')),
            booking_status TEXT DEFAULT 'pending' CHECK(booking_status IN ('pending', 'confirmed', 'docs_uploaded', 'completed', 'cancelled')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            documents_uploaded_at TEXT,
            escrow_released_at TEXT,
            auto_release_time TEXT,
            notes TEXT,
            FOREIGN KEY (handler_id) REFERENCES handler_profiles(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS handler_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            handler_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            upload_time TEXT DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            FOREIGN KEY (booking_id) REFERENCES handler_bookings(id),
            FOREIGN KEY (handler_id) REFERENCES handler_profiles(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS handler_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handler_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL,
            pet_parent_email TEXT NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (handler_id) REFERENCES handler_profiles(id),
            FOREIGN KEY (booking_id) REFERENCES handler_bookings(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS escrow_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('hold', 'release', 'refund')),
            amount REAL NOT NULL,
            initiated_by TEXT NOT NULL,
            reason TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES handler_bookings(id)
        )
    ''')

    # CRM Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            customer_type TEXT DEFAULT 'online' CHECK(customer_type IN ('online', 'offline', 'lead')),
            user_email TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            phone TEXT,
            secondary_phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            date_of_birth TEXT,
            customer_source TEXT,
            acquisition_date TEXT DEFAULT CURRENT_TIMESTAMP,
            customer_status TEXT DEFAULT 'active' CHECK(customer_status IN ('active', 'inactive', 'prospect', 'churned')),
            lifecycle_stage TEXT DEFAULT 'new' CHECK(lifecycle_stage IN ('new', 'lead', 'opportunity', 'customer', 'repeat_customer', 'vip')),
            assigned_to TEXT,
            notes TEXT,
            preferred_contact_method TEXT DEFAULT 'email' CHECK(preferred_contact_method IN ('email', 'phone', 'whatsapp', 'sms')),
            last_contact_date TEXT,
            next_follow_up_date TEXT,
            total_spent REAL DEFAULT 0.0,
            total_orders INTEGER DEFAULT 0,
            avg_order_value REAL DEFAULT 0.0,
            customer_ltv REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            pet_name TEXT NOT NULL,
            pet_type TEXT,
            breed TEXT,
            age INTEGER,
            weight REAL,
            color TEXT,
            gender TEXT,
            microchip_number TEXT,
            special_needs TEXT,
            allergies TEXT,
            medical_conditions TEXT,
            vaccination_status TEXT,
            last_visit_date TEXT,
            next_appointment_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES crm_customers(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            interaction_type TEXT NOT NULL CHECK(interaction_type IN ('call', 'email', 'sms', 'whatsapp', 'in_person', 'website', 'social_media', 'chat')),
            direction TEXT NOT NULL CHECK(direction IN ('inbound', 'outbound')),
            subject TEXT,
            description TEXT,
            outcome TEXT,
            follow_up_required BOOLEAN DEFAULT 0,
            follow_up_date TEXT,
            duration_minutes INTEGER,
            created_by TEXT NOT NULL,
            interaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
            attachments TEXT,
            tags TEXT,
            FOREIGN KEY (customer_id) REFERENCES crm_customers(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            opportunity_name TEXT NOT NULL,
            opportunity_type TEXT,
            stage TEXT DEFAULT 'prospecting' CHECK(stage IN ('prospecting', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost')),
            probability INTEGER DEFAULT 10,
            expected_value REAL,
            expected_close_date TEXT,
            actual_close_date TEXT,
            source TEXT,
            description TEXT,
            next_action TEXT,
            assigned_to TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES crm_customers(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            campaign_name TEXT NOT NULL,
            campaign_type TEXT CHECK(campaign_type IN ('email', 'sms', 'whatsapp', 'promotional', 'retention', 'acquisition')),
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            budget REAL,
            target_audience TEXT,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'paused', 'completed')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_campaign_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            status TEXT DEFAULT 'sent' CHECK(status IN ('sent', 'delivered', 'opened', 'clicked', 'responded', 'unsubscribed')),
            sent_date TEXT,
            response_date TEXT,
            FOREIGN KEY (campaign_id) REFERENCES crm_campaigns(id),
            FOREIGN KEY (customer_id) REFERENCES crm_customers(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            customer_id INTEGER,
            task_type TEXT CHECK(task_type IN ('call', 'email', 'meeting', 'follow_up', 'demo', 'quote')),
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
            due_date TEXT,
            assigned_to TEXT,
            completed_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (customer_id) REFERENCES crm_customers(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS crm_offline_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            collected_by TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            pet_name TEXT,
            pet_type TEXT,
            service_interest TEXT,
            notes TEXT,
            collection_method TEXT CHECK(collection_method IN ('business_card', 'form', 'phone_call', 'referral', 'event')),
            follow_up_priority TEXT DEFAULT 'medium' CHECK(follow_up_priority IN ('low', 'medium', 'high')),
            invited_status TEXT DEFAULT 'pending' CHECK(invited_status IN ('pending', 'invited', 'joined', 'declined')),
            invitation_sent_date TEXT,
            joined_date TEXT,
            collection_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Enhanced Order Management Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_status_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            previous_status TEXT,
            new_status TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            change_reason TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    # Stray Tracker System Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS ngo_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            organization_type TEXT CHECK(organization_type IN ('NGO', 'NPO', 'CSR')) NOT NULL,
            registration_number TEXT,
            license_number TEXT,
            contact_person TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            digital_signature_key TEXT UNIQUE,
            verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'approved', 'rejected', 'suspended')),
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            verified_at TEXT,
            total_strays_registered INTEGER DEFAULT 0,
            total_vaccinations INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stray_dogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_uid TEXT UNIQUE NOT NULL,
            qr_code TEXT UNIQUE NOT NULL,
            ngo_id INTEGER NOT NULL,
            registered_by_email TEXT NOT NULL,
            photo_url TEXT NOT NULL,
            location_latitude REAL NOT NULL,
            location_longitude REAL NOT NULL,
            location_address TEXT,
            breed_type TEXT,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Unknown')),
            age_estimation TEXT,
            fur_color TEXT,
            distinctive_marks TEXT,
            temperament TEXT DEFAULT 'Unknown' CHECK(temperament IN ('Friendly', 'Cautious', 'Aggressive', 'Unknown')),
            collar_color TEXT,
            current_status TEXT DEFAULT 'Active' CHECK(current_status IN ('Active', 'Relocated', 'Deceased', 'Adopted', 'Missing')),
            verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'flagged', 'rejected')),
            audit_flags INTEGER DEFAULT 0,
            total_vaccinations INTEGER DEFAULT 0,
            last_vaccination_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ngo_id) REFERENCES ngo_partners(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stray_vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_id INTEGER NOT NULL,
            ngo_id INTEGER NOT NULL,
            vaccination_photo_url TEXT NOT NULL,
            certificate_url TEXT,
            vaccine_name TEXT NOT NULL,
            vaccine_batch_number TEXT NOT NULL,
            vaccine_expiration_date TEXT NOT NULL,
            vaccinator_name TEXT NOT NULL,
            vaccinator_contact TEXT,
            vaccinator_license TEXT,
            is_furrbutler_vet BOOLEAN DEFAULT 0,
            digital_signature TEXT NOT NULL,
            signature_timestamp TEXT NOT NULL,
            vaccination_date TEXT NOT NULL,
            vaccination_cost REAL DEFAULT 0,
            additional_notes TEXT,
            verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'verified', 'flagged', 'rejected')),
            audit_score REAL DEFAULT 0,
            image_hash TEXT,
            is_duplicate_flagged BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            verified_at TEXT,
            FOREIGN KEY (stray_id) REFERENCES stray_dogs(id),
            FOREIGN KEY (ngo_id) REFERENCES ngo_partners(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stray_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_id INTEGER NOT NULL,
            ngo_id INTEGER NOT NULL,
            expense_type TEXT NOT NULL CHECK(expense_type IN ('Vaccination', 'Food', 'Travel', 'Accommodation', 'Medical', 'Collar', 'Other')),
            amount REAL NOT NULL,
            description TEXT,
            receipt_url TEXT,
            expense_date TEXT NOT NULL,
            created_by TEXT NOT NULL,
            verification_status TEXT DEFAULT 'approved' CHECK(verification_status IN ('pending', 'approved', 'rejected')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stray_id) REFERENCES stray_dogs(id),
            FOREIGN KEY (ngo_id) REFERENCES ngo_partners(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stray_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_id INTEGER,
            vaccination_id INTEGER,
            audit_type TEXT NOT NULL CHECK(audit_type IN ('image_verification', 'pattern_analysis', 'citizen_report', 'random_audit', 'manual_review')),
            audit_result TEXT CHECK(audit_result IN ('passed', 'flagged', 'failed')),
            confidence_score REAL,
            audit_details TEXT,
            flagged_reason TEXT,
            audited_by TEXT,
            audit_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            action_taken TEXT,
            FOREIGN KEY (stray_id) REFERENCES stray_dogs(id),
            FOREIGN KEY (vaccination_id) REFERENCES stray_vaccinations(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS citizen_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_id INTEGER,
            vaccination_id INTEGER,
            reporter_email TEXT,
            report_type TEXT CHECK(report_type IN ('suspicious_activity', 'duplicate_image', 'false_information', 'location_mismatch', 'other')),
            description TEXT NOT NULL,
            evidence_url TEXT,
            report_status TEXT DEFAULT 'pending' CHECK(report_status IN ('pending', 'investigating', 'resolved', 'dismissed')),
            priority_level TEXT DEFAULT 'medium' CHECK(priority_level IN ('low', 'medium', 'high', 'critical')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            investigated_at TEXT,
            investigated_by TEXT,
            resolution_notes TEXT,
            FOREIGN KEY (stray_id) REFERENCES stray_dogs(id),
            FOREIGN KEY (vaccination_id) REFERENCES stray_vaccinations(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stray_community_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stray_id INTEGER NOT NULL,
            ngo_id INTEGER NOT NULL,
            update_type TEXT CHECK(update_type IN ('collar_tagging', 'location_update', 'status_change', 'community_interaction', 'feeding', 'medical_care')),
            description TEXT NOT NULL,
            photo_url TEXT,
            video_url TEXT,
            location_latitude REAL,
            location_longitude REAL,
            created_by TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stray_id) REFERENCES stray_dogs(id),
            FOREIGN KEY (ngo_id) REFERENCES ngo_partners(id)
        )
    ''')

    # Discount Management Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            discount_type TEXT NOT NULL CHECK(discount_type IN ('percentage', 'fixed')),
            discount_value REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            start_date TEXT DEFAULT CURRENT_TIMESTAMP,
            end_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS vendor_blanket_discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER UNIQUE NOT NULL,
            discount_type TEXT NOT NULL CHECK(discount_type IN ('percentage', 'fixed')),
            discount_value REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            start_date TEXT DEFAULT CURRENT_TIMESTAMP,
            end_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS fulfillment_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            fulfillment_method TEXT DEFAULT 'warehouse',
            delivery_time REAL,
            on_time_delivery BOOLEAN DEFAULT 1,
            customer_satisfaction INTEGER DEFAULT 5,
            cost_efficiency REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            customer_email TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            message TEXT NOT NULL,
            delivery_method TEXT DEFAULT 'email',
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS shipping_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            tracking_number TEXT,
            carrier TEXT,
            shipping_method TEXT,
            shipped_date TEXT,
            estimated_delivery TEXT,
            actual_delivery TEXT,
            tracking_url TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    # Add new columns if they don't exist
    try:
        c.execute("ALTER TABLE vendors ADD COLUMN account_status TEXT DEFAULT 'active'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add enhanced order management columns
    try:
        c.execute("ALTER TABLE orders ADD COLUMN last_updated TEXT DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN fulfillment_method TEXT DEFAULT 'warehouse'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN priority_level TEXT DEFAULT 'normal'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN shipped_date TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN tracking_number TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN carrier TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE orders ADD COLUMN delivery_instructions TEXT")
    except sqlite3.OperationalError:
        pass

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

    # Insert demo handler profiles
    demo_handlers = [
        ("Sarah Johnson", "sarah@globalpaws.com", "handler123", "USA", 1200.00, "International Pet Transport, USDA Documentation", 8, 98.5, 45, "https://images.unsplash.com/photo-1494790108755-2616b332446c?w=400", "Certified international pet transport specialist with 8+ years experience", "English, Spanish", "USDA Certified, IATA Live Animal Regulations", 1),
        ("Marco Silva", "marco@petmover.com", "handler123", "Brazil", 800.00, "South American Pet Transport, Quarantine Management", 5, 96.2, 32, "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400", "Specialized in South American pet relocations and quarantine procedures", "Portuguese, English, Spanish", "Brazilian Ministry Certified", 1),
        ("Yuki Tanaka", "yuki@asiapet.com", "handler123", "Japan", 1500.00, "Asian Pet Transport, Health Certification", 12, 99.1, 78, "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400", "Expert in Asian pet transport regulations with perfect success rate", "Japanese, English, Mandarin", "Japan Animal Quarantine Service Certified", 1)
    ]

    for handler in demo_handlers:
        c.execute('''
            INSERT OR IGNORE INTO handler_profiles 
            (name, email, password, country, base_price, services_offered, experience_years, success_rate, total_bookings, profile_image, bio, languages, certifications, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', handler)

    # Insert demo NGO partners
    demo_ngos = [
        ("Paws For Life Foundation", "contact@pawsforlife.org", "ngo123", "NGO", "REG/NGO/2023/001", "LIC-001-2023", "Dr. Meera Sharma", "+91-9876543210", "123 Charity Street", "Mumbai", "Maharashtra", "400001", "PFL-DSC-001", "approved"),
        ("Street Dog Welfare Society", "info@streetdogwelfare.org", "ngo123", "NPO", "REG/NPO/2023/002", "LIC-002-2023", "Raj Kumar", "+91-9876543211", "456 Animal Avenue", "Delhi", "Delhi", "110001", "SDWS-DSC-002", "approved"),
        ("Corporate Pet Care Initiative", "csr@corpetcare.com", "ngo123", "CSR", "REG/CSR/2023/003", "LIC-003-2023", "Priya Gupta", "+91-9876543212", "789 Business Park", "Bangalore", "Karnataka", "560001", "CPCI-DSC-003", "approved")
    ]

    for ngo in demo_ngos:
        c.execute('''
            INSERT OR IGNORE INTO ngo_partners 
            (name, email, password, organization_type, registration_number, license_number, contact_person, phone, address, city, state, pincode, digital_signature_key, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ngo)

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

# Register i18n functions with Jinja2
app.jinja_env.globals.update(
    t=t,
    get_supported_languages=get_supported_languages,
    get_current_language=get_current_language
)

# Register WhatsApp blueprint
app.register_blueprint(whatsapp_bp)

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

# ---- STRAY TRACKER ROUTES ----

@app.route('/stray-tracker')
def stray_tracker_home():
    """Public stray tracker view for citizens"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get verified stray dogs with recent activity
    c.execute("""
        SELECT sd.stray_uid, sd.photo_url, sd.location_address, sd.breed_type, 
               sd.temperament, sd.collar_color, sd.total_vaccinations, sd.last_vaccination_date,
               np.name as ngo_name, sd.location_latitude, sd.location_longitude
        FROM stray_dogs sd
        JOIN ngo_partners np ON sd.ngo_id = np.id
        WHERE sd.verification_status = 'verified' AND sd.current_status = 'Active'
        ORDER BY sd.last_updated DESC
        LIMIT 50
    """)
    
    strays = c.fetchall()
    
    # Get tracker statistics
    c.execute("SELECT COUNT(*) FROM stray_dogs WHERE verification_status = 'verified'")
    total_verified_strays = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM stray_vaccinations WHERE verification_status = 'verified'")
    total_vaccinations = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT ngo_id) FROM stray_dogs")
    active_ngos = c.fetchone()[0] or 0
    
    stats = {
        'total_verified_strays': total_verified_strays,
        'total_vaccinations': total_vaccinations,
        'active_ngos': active_ngos
    }
    
    conn.close()
    return render_template("stray_tracker_public.html", strays=strays, stats=stats)

@app.route('/stray/<stray_uid>')
def stray_detail(stray_uid):
    """Detailed view of a specific stray dog"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get stray details
    c.execute("""
        SELECT sd.*, np.name as ngo_name, np.contact_person, np.phone
        FROM stray_dogs sd
        JOIN ngo_partners np ON sd.ngo_id = np.id
        WHERE sd.stray_uid = ? AND sd.verification_status = 'verified'
    """, (stray_uid,))
    
    stray = c.fetchone()
    if not stray:
        return "Stray not found", 404
    
    # Get vaccination history
    c.execute("""
        SELECT * FROM stray_vaccinations
        WHERE stray_id = ? AND verification_status = 'verified'
        ORDER BY vaccination_date DESC
    """, (stray[0],))
    vaccinations = c.fetchall()
    
    # Get expense breakdown
    c.execute("""
        SELECT expense_type, SUM(amount) as total_amount, COUNT(*) as count
        FROM stray_expenses
        WHERE stray_id = ? AND verification_status = 'approved'
        GROUP BY expense_type
    """, (stray[0],))
    expenses = c.fetchall()
    
    # Get community updates
    c.execute("""
        SELECT * FROM stray_community_updates
        WHERE stray_id = ? AND is_verified = 1
        ORDER BY created_at DESC
        LIMIT 10
    """, (stray[0],))
    updates = c.fetchall()
    
    conn.close()
    return render_template("stray_detail.html", 
                         stray=stray, 
                         vaccinations=vaccinations, 
                         expenses=expenses, 
                         updates=updates)

@app.route('/ngo/login', methods=["GET", "POST"])
def ngo_login():
    """NGO partner login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM ngo_partners WHERE email=? AND password=? AND is_active=1 AND verification_status='approved'", (email, password))
        ngo = c.fetchone()
        conn.close()

        if ngo:
            session["ngo"] = email
            session["ngo_id"] = ngo[0]
            session["ngo_name"] = ngo[1]
            session["ngo_type"] = ngo[3]
            session["ngo_signature_key"] = ngo[13]
            return redirect(url_for("ngo_dashboard"))
        else:
            flash("Invalid NGO credentials or account not approved")

    return render_template("ngo_login.html")

@app.route('/ngo/register', methods=["GET", "POST"])
def ngo_register():
    """NGO partner registration"""
    if request.method == "POST":
        import secrets
        
        form_data = {
            'name': request.form.get("name"),
            'email': request.form.get("email"),
            'password': request.form.get("password"),
            'organization_type': request.form.get("organization_type"),
            'registration_number': request.form.get("registration_number"),
            'license_number': request.form.get("license_number"),
            'contact_person': request.form.get("contact_person"),
            'phone': request.form.get("phone"),
            'address': request.form.get("address"),
            'city': request.form.get("city"),
            'state': request.form.get("state"),
            'pincode': request.form.get("pincode")
        }
        
        # Generate unique digital signature key
        signature_key = f"{form_data['organization_type']}-DSC-{secrets.token_hex(8).upper()}"
        
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        try:
            c.execute("""
                INSERT INTO ngo_partners 
                (name, email, password, organization_type, registration_number, license_number, 
                 contact_person, phone, address, city, state, pincode, digital_signature_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (form_data['name'], form_data['email'], form_data['password'], 
                  form_data['organization_type'], form_data['registration_number'], 
                  form_data['license_number'], form_data['contact_person'], form_data['phone'],
                  form_data['address'], form_data['city'], form_data['state'], 
                  form_data['pincode'], signature_key))
            
            conn.commit()
            conn.close()
            
            flash("Registration successful! Your account is pending verification. You'll receive an email once approved.")
            return redirect(url_for("ngo_login"))
            
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered or registration number already exists")
    
    return render_template("ngo_register.html")

@app.route('/ngo/dashboard')
def ngo_dashboard():
    """NGO dashboard showing strays and statistics"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    ngo_name = session["ngo_name"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get NGO statistics
    c.execute("SELECT total_strays_registered, total_vaccinations FROM ngo_partners WHERE id = ?", (ngo_id,))
    ngo_stats = c.fetchone()
    
    c.execute("SELECT COUNT(*) FROM stray_dogs WHERE ngo_id = ? AND current_status = 'Active'", (ngo_id,))
    active_strays = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM stray_dogs WHERE ngo_id = ? AND verification_status = 'pending'", (ngo_id,))
    pending_verification = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM citizen_reports WHERE stray_id IN (SELECT id FROM stray_dogs WHERE ngo_id = ?) AND report_status = 'pending'", (ngo_id,))
    pending_reports = c.fetchone()[0] or 0
    
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM stray_expenses WHERE ngo_id = ? AND verification_status = 'approved'", (ngo_id,))
    total_expenses = c.fetchone()[0] or 0
    
    stats = {
        'total_registered': ngo_stats[0] if ngo_stats else 0,
        'total_vaccinations': ngo_stats[1] if ngo_stats else 0,
        'active_strays': active_strays,
        'pending_verification': pending_verification,
        'pending_reports': pending_reports,
        'total_expenses': total_expenses
    }

    # Get recent strays
    c.execute("""
        SELECT id, stray_uid, photo_url, breed_type, temperament, verification_status, created_at
        FROM stray_dogs 
        WHERE ngo_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (ngo_id,))
    recent_strays = c.fetchall()

    conn.close()
    return render_template("ngo_dashboard.html", 
                         stats=stats, 
                         recent_strays=recent_strays, 
                         ngo_name=ngo_name)

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
        address = request.form.get("address", "")
        city = request.form.get("city", "")
        state = request.form.get("state", "")
        pincode = request.form.get("pincode", "")
        phone = request.form.get("phone", "")
        bio = request.form.get("bio", "")
        image_url = request.form.get("image_url", "")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Convert coordinates to float if provided
        try:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None
        except (ValueError, TypeError):
            lat = lng = None

        try:
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("""INSERT INTO vendors 
                         (email, name, password, category, address, city, state, pincode, phone, bio, image_url, latitude, longitude) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                     (email, name, password, category, address, city, state, pincode, phone, bio, image_url, lat, lng))
            conn.commit()
            conn.close()
            flash("Vendor registration successful! You can now log in.")
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
    c.execute("SELECT id, name, email, phone, bio, image_url, city, latitude, longitude, category, account_status, break_start_date, break_reason, address, state, pincode FROM vendors WHERE email=?", (email,))
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
        address = request.form.get("address", "")
        city = request.form.get("city", "")
        state = request.form.get("state", "")
        pincode = request.form.get("pincode", "")
        category = request.form.get("category", "")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Convert coordinates to float if provided
        try:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None
        except (ValueError, TypeError):
            lat = lng = None

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
            SET name=?, phone=?, bio=?, image_url=?, address=?, city=?, state=?, pincode=?, category=?, latitude=?, longitude=?
            WHERE email=?
        ''', (name, phone, bio, image_url, address, city, state, pincode, category, lat, lng, email))

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

        # Get products with stock and discount information
        c.execute("""
            SELECT p.id, p.name, p.description, p.sale_price, p.quantity, p.image_url,
                   COALESCE(pd.discount_type, 'none') as discount_type,
                   COALESCE(pd.discount_value, 0) as discount_value,
                   COALESCE(pd.is_active, 0) as is_active,
                   CASE 
                     WHEN pd.discount_type = 'percentage' AND pd.is_active = 1 
                     THEN p.sale_price * (1 - pd.discount_value / 100)
                     WHEN pd.discount_type = 'fixed' AND pd.is_active = 1 
                     THEN p.sale_price - pd.discount_value
                     ELSE p.sale_price
                   END as discounted_price,
                   CASE 
                     WHEN pd.discount_type IS NOT NULL AND pd.is_active = 1 
                     THEN 1 ELSE 0 
                   END as has_discount
            FROM products p
            LEFT JOIN product_discounts pd ON p.id = pd.product_id
            WHERE p.vendor_id=? AND p.quantity > 0
            ORDER BY p.name
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

# Vendor order management with enhanced features
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
        return render_template("erp_orders.html", orders=[], order_stats={})

    vendor_id = vendor_result[0]

    # Get all orders for this vendor with enhanced information
    c.execute("""
        SELECT o.id, o.user_email, o.total_amount, o.status, o.delivery_type, 
               o.delivery_address, o.estimated_delivery, o.order_date, o.tracking_notes,
               o.delivery_fee, o.order_date,
               COUNT(oi.id) as item_count,
               CASE 
                 WHEN o.delivery_type = 'same_day' THEN 'urgent'
                 WHEN o.delivery_type = 'express' THEN 'high'
                 ELSE 'normal'
               END as priority_level
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.vendor_id = ?
        GROUP BY o.id
        ORDER BY 
          CASE o.status 
            WHEN 'pending' THEN 1
            WHEN 'confirmed' THEN 2
            WHEN 'packed' THEN 3
            WHEN 'shipped' THEN 4
            WHEN 'out-for-delivery' THEN 5
            WHEN 'delivered' THEN 6
            ELSE 7
          END,
          o.order_date DESC
    """, (vendor_id,))
    orders = c.fetchall()

    # Calculate order statistics
    c.execute("""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN status IN ('shipped', 'out-for-delivery') THEN 1 END) as in_transit_orders,
            COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_orders,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
            AVG(total_amount) as avg_order_value,
            SUM(CASE WHEN status = 'delivered' THEN total_amount ELSE 0 END) as delivered_revenue
        FROM orders 
        WHERE vendor_id = ? AND order_date >= date('now', '-30 days')
    """, (vendor_id,))
    
    stats_data = c.fetchone()
    order_stats = {
        'total_orders': stats_data[0] or 0,
        'pending_orders': stats_data[1] or 0,
        'in_transit_orders': stats_data[2] or 0,
        'delivered_orders': stats_data[3] or 0,
        'cancelled_orders': stats_data[4] or 0,
        'avg_order_value': stats_data[5] or 0,
        'delivered_revenue': stats_data[6] or 0,
        'fulfillment_rate': round((stats_data[3] / stats_data[0] * 100), 1) if stats_data[0] > 0 else 0
    }

    conn.close()
    return render_template("erp_orders.html", orders=orders, order_stats=order_stats)

@app.route('/erp/orders/update/<int:order_id>', methods=["POST"])
def update_order_status(order_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    new_status = request.form.get("status")
    tracking_notes = request.form.get("tracking_notes", "")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID and verify order ownership
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        flash("Vendor not found")
        return redirect(url_for("erp_orders"))

    vendor_id = vendor_result[0]

    # Get current order details
    c.execute("""
        SELECT o.status, o.user_email, o.delivery_type, o.total_amount 
        FROM orders o 
        WHERE o.id = ? AND o.vendor_id = ?
    """, (order_id, vendor_id))
    
    order_data = c.fetchone()
    if not order_data:
        flash("Order not found")
        return redirect(url_for("erp_orders"))

    current_status, customer_email, delivery_type, order_amount = order_data

    # Update order status with timestamp tracking
    c.execute("""
        UPDATE orders 
        SET status = ?, tracking_notes = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ? AND vendor_id = ?
    """, (new_status, tracking_notes, order_id, vendor_id))

    # Log order status change for audit trail
    c.execute("""
        INSERT INTO order_status_log (order_id, previous_status, new_status, changed_by, change_reason, timestamp)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (order_id, current_status, new_status, email, tracking_notes))

    # Update estimated delivery based on status
    if new_status == "shipped":
        if delivery_type == "same_day":
            estimated_delivery = datetime.now().strftime("%Y-%m-%d")
        elif delivery_type == "express":
            estimated_delivery = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            estimated_delivery = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        c.execute("""
            UPDATE orders 
            SET estimated_delivery = ? 
            WHERE id = ?
        """, (estimated_delivery, order_id))

    # Record fulfillment metrics for analytics
    if new_status == "delivered":
        c.execute("""
            INSERT INTO fulfillment_metrics (order_id, delivery_time, on_time_delivery, customer_satisfaction)
            VALUES (?, julianday('now') - julianday((SELECT order_date FROM orders WHERE id = ?)), 1, 5)
        """, (order_id, order_id))

    # Automated customer notifications (mock implementation)
    notification_messages = {
        "confirmed": f"Great news! Your order #{order_id} has been confirmed and is being prepared.",
        "packed": f"Your order #{order_id} has been packed and will be shipped soon.",
        "shipped": f"Your order #{order_id} is on its way! Track your package for updates.",
        "out-for-delivery": f"Your order #{order_id} is out for delivery and will arrive soon!",
        "delivered": f"Your order #{order_id} has been delivered. Thank you for your business!",
        "cancelled": f"Your order #{order_id} has been cancelled. A refund will be processed if applicable."
    }
    
    if new_status in notification_messages:
        # In a real implementation, send email/SMS here
        notification_message = notification_messages[new_status]
        
        # Log the notification
        c.execute("""
            INSERT INTO customer_notifications (order_id, customer_email, notification_type, message, sent_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (order_id, customer_email, "status_update", notification_message))

    conn.commit()
    conn.close()

    flash(f"Order #{order_id} status updated to {new_status.replace('_', ' ').title()}")
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

    marketplace_commission = float(request.form.get("marketplace_commission_rate", 10.0))
    grooming_commission = float(request.form.get("grooming_commission_rate", 15.0))
    offline_transaction_fee = float(request.form.get("offline_transaction_fee", 0.01))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Update master settings
    c.execute("""
        UPDATE master_settings 
        SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE setting_name = 'marketplace_commission_rate'
    """, (marketplace_commission,))

    c.execute("""
        UPDATE master_settings 
        SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE setting_name = 'grooming_commission_rate'
    """, (grooming_commission,))

    c.execute("""
        UPDATE master_settings 
        SET previous_value = setting_value, setting_value = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE setting_name = 'offline_transaction_fee'
    """, (offline_transaction_fee,))

    conn.commit()
    conn.close()

    flash(f"Settings updated: Marketplace Commission {marketplace_commission}%, Grooming Commission {grooming_commission}%, Offline Transaction Fee {offline_transaction_fee}%")
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

# ---- HANDLER ESCROW MANAGEMENT ROUTES ----

@app.route('/handlers')
def handlers_list():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT id, name, country, base_price, services_offered, experience_years, 
               success_rate, total_bookings, profile_image, bio, languages, 
               certifications, is_active
        FROM handler_profiles 
        WHERE is_active = 1
        ORDER BY success_rate DESC, total_bookings DESC
    """)
    
    handlers_data = c.fetchall()
    handlers = []
    
    for handler in handlers_data:
        handlers.append({
            'id': handler[0],
            'name': handler[1],
            'country': handler[2],
            'base_price': handler[3],
            'services_offered': handler[4],
            'experience_years': handler[5],
            'success_rate': handler[6],
            'total_bookings': handler[7],
            'profile_image': handler[8],
            'bio': handler[9],
            'languages': handler[10],
            'certifications': handler[11]
        })
    
    conn.close()
    return render_template("handlers.html", handlers=handlers)

@app.route('/handler/<int:handler_id>')
def handler_detail(handler_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get handler details
    c.execute("""
        SELECT id, name, country, base_price, services_offered, experience_years, 
               success_rate, total_bookings, profile_image, bio, languages, 
               certifications, is_active
        FROM handler_profiles 
        WHERE id = ?
    """, (handler_id,))
    
    handler_data = c.fetchone()
    if not handler_data:
        return "Handler not found", 404
    
    handler = {
        'id': handler_data[0],
        'name': handler_data[1],
        'country': handler_data[2],
        'base_price': handler_data[3],
        'services_offered': handler_data[4],
        'experience_years': handler_data[5],
        'success_rate': handler_data[6],
        'total_bookings': handler_data[7],
        'profile_image': handler_data[8],
        'bio': handler_data[9],
        'languages': handler_data[10],
        'certifications': handler_data[11]
    }
    
    # Get reviews
    c.execute("""
        SELECT hr.id, hr.handler_id, hr.pet_parent_email, hr.rating, hr.review_text, hr.created_at
        FROM handler_reviews hr
        WHERE hr.handler_id = ?
        ORDER BY hr.created_at DESC
    """, (handler_id,))
    
    reviews = c.fetchall()
    conn.close()
    
    return render_template("handler_detail.html", handler=handler, reviews=reviews)

@app.route('/handler/<int:handler_id>/book', methods=["GET", "POST"])
def book_handler(handler_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get handler details
    c.execute("""
        SELECT id, name, country, base_price, email
        FROM handler_profiles 
        WHERE id = ? AND is_active = 1
    """, (handler_id,))
    
    handler_data = c.fetchone()
    if not handler_data:
        return "Handler not found", 404
    
    handler = {
        'id': handler_data[0],
        'name': handler_data[1],
        'country': handler_data[2],
        'base_price': handler_data[3],
        'email': handler_data[4]
    }
    
    if request.method == "POST":
        pet_name = request.form.get("pet_name")
        pet_type = request.form.get("pet_type")
        destination_country = request.form.get("destination_country")
        travel_date = request.form.get("travel_date")
        notes = request.form.get("notes", "")
        
        pet_parent_email = session["user"]
        total_amount = handler['base_price']
        handler_fee = total_amount * 0.9  # 90% to handler
        platform_fee = total_amount * 0.1  # 10% platform fee
        
        # Calculate auto-release time (48 hours from now)
        from datetime import datetime, timedelta
        auto_release_time = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Create booking
        c.execute("""
            INSERT INTO handler_bookings 
            (handler_id, pet_parent_email, pet_name, pet_type, destination_country, 
             travel_date, total_amount, handler_fee, platform_fee, auto_release_time, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (handler_id, pet_parent_email, pet_name, pet_type, destination_country,
              travel_date, total_amount, handler_fee, platform_fee, auto_release_time, notes))
        
        booking_id = c.lastrowid
        
        # Create initial escrow transaction
        c.execute("""
            INSERT INTO escrow_transactions 
            (booking_id, transaction_type, amount, initiated_by, reason)
            VALUES (?, 'hold', ?, ?, 'Initial booking escrow hold')
        """, (booking_id, total_amount, pet_parent_email))
        
        # Update handler's total bookings
        c.execute("""
            UPDATE handler_profiles 
            SET total_bookings = total_bookings + 1 
            WHERE id = ?
        """, (handler_id,))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for("handler_invoice", booking_id=booking_id))
    
    conn.close()
    return render_template("handler_booking.html", handler=handler)

@app.route('/handler/invoice/<int:booking_id>')
def handler_invoice(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get booking details with handler info
    c.execute("""
        SELECT hb.*, hp.name as handler_name, hp.email as handler_email, hp.country
        FROM handler_bookings hb
        JOIN handler_profiles hp ON hb.handler_id = hp.id
        WHERE hb.id = ? AND hb.pet_parent_email = ?
    """, (booking_id, session["user"]))
    
    booking_data = c.fetchone()
    if not booking_data:
        return "Booking not found", 404
    
    booking = {
        'id': booking_data[0],
        'handler_id': booking_data[1],
        'pet_parent_email': booking_data[2],
        'pet_name': booking_data[3],
        'pet_type': booking_data[4],
        'destination_country': booking_data[5],
        'travel_date': booking_data[6],
        'total_amount': booking_data[7],
        'handler_fee': booking_data[8],
        'platform_fee': booking_data[9],
        'escrow_status': booking_data[10],
        'booking_status': booking_data[11],
        'created_at': booking_data[12],
        'documents_uploaded_at': booking_data[13],
        'escrow_released_at': booking_data[14],
        'auto_release_time': booking_data[15],
        'notes': booking_data[16]
    }
    
    handler = {
        'name': booking_data[17],
        'email': booking_data[18],
        'country': booking_data[19]
    }
    
    conn.close()
    return render_template("handler_invoice.html", booking=booking, handler=handler)

@app.route('/my-handler-bookings')
def my_handler_bookings():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get all bookings for this user
    c.execute("""
        SELECT hb.*, hp.name as handler_name, hp.country, hp.profile_image
        FROM handler_bookings hb
        JOIN handler_profiles hp ON hb.handler_id = hp.id
        WHERE hb.pet_parent_email = ?
        ORDER BY hb.created_at DESC
    """, (session["user"],))
    
    bookings_data = c.fetchall()
    bookings = []
    
    for booking in bookings_data:
        bookings.append({
            'id': booking[0],
            'handler_id': booking[1],
            'pet_name': booking[3],
            'pet_type': booking[4],
            'destination_country': booking[5],
            'travel_date': booking[6],
            'total_amount': booking[7],
            'handler_fee': booking[8],
            'platform_fee': booking[9],
            'escrow_status': booking[10],
            'booking_status': booking[11],
            'created_at': booking[12],
            'handler_name': booking[17],
            'handler_country': booking[18],
            'handler_image': booking[19]
        })
    
    conn.close()
    return render_template("my_handler_bookings.html", bookings=bookings)

# Handler login and dashboard routes
@app.route('/handler/profile/login', methods=["GET", "POST"])
def handler_profile_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM handler_profiles WHERE email=? AND password=? AND is_active=1", (email, password))
        handler = c.fetchone()
        conn.close()

        if handler:
            session["handler_profile"] = email
            session["handler_profile_id"] = handler[0]
            session["handler_profile_name"] = handler[1]
            return redirect(url_for("handler_profile_dashboard"))
        else:
            flash("Invalid handler credentials")

    return render_template("handler_profile_login.html")

@app.route('/handler/profile/dashboard')
def handler_profile_dashboard():
    if "handler_profile" not in session:
        return redirect(url_for("handler_profile_login"))

    handler_id = session["handler_profile_id"]
    handler_name = session["handler_profile_name"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get handler bookings
    c.execute("""
        SELECT hb.*, 
               (SELECT COUNT(*) FROM handler_documents WHERE booking_id = hb.id) as doc_count
        FROM handler_bookings hb
        WHERE hb.handler_id = ?
        ORDER BY hb.created_at DESC
    """, (handler_id,))
    
    bookings_data = c.fetchall()
    bookings = []
    
    for booking in bookings_data:
        # Get documents for this booking
        c.execute("""
            SELECT document_type, filename, upload_time, description
            FROM handler_documents 
            WHERE booking_id = ?
            ORDER BY upload_time DESC
        """, (booking[0],))
        documents = c.fetchall()
        
        bookings.append({
            'id': booking[0],
            'pet_parent_email': booking[2],
            'pet_name': booking[3],
            'pet_type': booking[4],
            'destination_country': booking[5],
            'travel_date': booking[6],
            'total_amount': booking[7],
            'handler_fee': booking[8],
            'platform_fee': booking[9],
            'escrow_status': booking[10],
            'booking_status': booking[11],
            'created_at': booking[12],
            'notes': booking[16] if len(booking) > 16 else '',
            'documents': documents
        })

    # Calculate stats
    total_bookings = len(bookings)
    total_earnings = sum(b['handler_fee'] for b in bookings if b['escrow_status'] == 'released')
    
    stats = {
        'total_bookings': total_bookings,
        'total_earnings': total_earnings
    }

    conn.close()
    return render_template("handler_dashboard.html", 
                         bookings=bookings, 
                         handler_name=handler_name,
                         stats=stats)

@app.route('/handler/update-booking-status', methods=["POST"])
def handler_update_booking_status():
    if "handler_profile" not in session:
        return redirect(url_for("handler_profile_login"))

    booking_id = request.form.get("booking_id")
    new_status = request.form.get("status")
    handler_id = session["handler_profile_id"]

    if not booking_id or not new_status:
        flash("Missing required information")
        return redirect(url_for("handler_profile_dashboard"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Update booking status
    c.execute("""
        UPDATE handler_bookings 
        SET booking_status = ?
        WHERE id = ? AND handler_id = ?
    """, (new_status, booking_id, handler_id))

    # If status is docs_uploaded, set the timestamp
    if new_status == 'docs_uploaded':
        c.execute("""
            UPDATE handler_bookings 
            SET documents_uploaded_at = CURRENT_TIMESTAMP
            WHERE id = ? AND handler_id = ?
        """, (booking_id, handler_id))

    conn.commit()
    conn.close()

    flash(f"Booking status updated to {new_status.replace('_', ' ').title()}")
    return redirect(url_for("handler_profile_dashboard"))





# Admin escrow management routes
@app.route('/admin/escrow')
def admin_escrow_dashboard():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get statistics
    c.execute("SELECT COUNT(*) FROM handler_bookings")
    total_bookings = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM handler_bookings WHERE escrow_status = 'held'")
    total_held = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(platform_fee), 0) FROM handler_bookings")
    total_platform_fees = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM handler_bookings WHERE escrow_status = 'held' AND booking_status = 'docs_uploaded'")
    pending_releases = c.fetchone()[0]

    stats = {
        'total_bookings': total_bookings,
        'total_held': total_held,
        'total_platform_fees': total_platform_fees,
        'pending_releases': pending_releases
    }

    # Get all bookings with handler details
    c.execute("""
        SELECT hb.*, hp.name as handler_name, hp.email as handler_email
        FROM handler_bookings hb
        JOIN handler_profiles hp ON hb.handler_id = hp.id
        ORDER BY hb.created_at DESC
    """)
    bookings_data = c.fetchall()

    bookings = []
    for booking in bookings_data:
        bookings.append({
            'id': booking[0],
            'handler_id': booking[1],
            'pet_parent_email': booking[2],
            'pet_name': booking[3],
            'pet_type': booking[4],
            'destination_country': booking[5],
            'travel_date': booking[6],
            'total_amount': booking[7],
            'handler_fee': booking[8],
            'platform_fee': booking[9],
            'escrow_status': booking[10],
            'booking_status': booking[11],
            'created_at': booking[12],
            'auto_release_time': booking[15],
            'handler_name': booking[17],
            'handler_email': booking[18]
        })

    # Get recent escrow transactions
    c.execute("""
        SELECT * FROM escrow_transactions 
        ORDER BY timestamp DESC 
        LIMIT 20
    """)
    recent_transactions = c.fetchall()

    conn.close()
    return render_template("admin_escrow_dashboard.html", 
                         stats=stats, 
                         bookings=bookings, 
                         recent_transactions=recent_transactions)

@app.route('/admin/escrow/release', methods=["POST"])
def admin_release_escrow():
    if not session.get("master_admin"):
        return {"error": "Unauthorized"}, 403

    data = request.get_json()
    booking_id = data.get("booking_id")
    reason = data.get("reason", "Manual release by admin")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        # Update escrow status
        c.execute("""
            UPDATE handler_bookings 
            SET escrow_status = 'released', escrow_released_at = CURRENT_TIMESTAMP
            WHERE id = ? AND escrow_status = 'held'
        """, (booking_id,))

        # Get booking details for transaction log
        c.execute("SELECT total_amount FROM handler_bookings WHERE id = ?", (booking_id,))
        amount = c.fetchone()[0]

        # Log the transaction
        c.execute("""
            INSERT INTO escrow_transactions 
            (booking_id, transaction_type, amount, initiated_by, reason)
            VALUES (?, 'release', ?, 'admin', ?)
        """, (booking_id, amount, reason))

        conn.commit()
        conn.close()

        return {"success": True}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": str(e)}, 500

@app.route('/admin/escrow/refund', methods=["POST"])
def admin_refund_escrow():
    if not session.get("master_admin"):
        return {"error": "Unauthorized"}, 403

    data = request.get_json()
    booking_id = data.get("booking_id")
    reason = data.get("reason", "Manual refund by admin")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        # Update escrow status
        c.execute("""
            UPDATE handler_bookings 
            SET escrow_status = 'refunded', booking_status = 'cancelled'
            WHERE id = ? AND escrow_status = 'held'
        """, (booking_id,))

        # Get booking details for transaction log
        c.execute("SELECT total_amount FROM handler_bookings WHERE id = ?", (booking_id,))
        amount = c.fetchone()[0]

        # Log the transaction
        c.execute("""
            INSERT INTO escrow_transactions 
            (booking_id, transaction_type, amount, initiated_by, reason)
            VALUES (?, 'refund', ?, 'admin', ?)
        """, (booking_id, amount, reason))

        conn.commit()
        conn.close()

        return {"success": True}
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"error": str(e)}, 500

# Fulfillment optimization API
@app.route('/api/orders/<int:order_id>/fulfillment-options')
def get_fulfillment_options(order_id):
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get order details
    c.execute("""
        SELECT o.delivery_address, o.delivery_type, o.total_amount,
               oi.product_id, oi.quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.id = ?
    """, (order_id,))
    
    order_data = c.fetchall()
    if not order_data:
        conn.close()
        return {"error": "Order not found"}, 404

    # Calculate fulfillment costs and recommendations
    delivery_address = order_data[0][0]
    delivery_type = order_data[0][1]
    order_value = order_data[0][2]

    # Mock fulfillment options calculation
    options = [
        {
            "method": "store_pickup",
            "name": "Store Pickup",
            "cost": 0.00,
            "time": "Same day",
            "availability": "Available",
            "recommended": delivery_type == "standard" and order_value < 50
        },
        {
            "method": "warehouse",
            "name": "Warehouse Fulfillment",
            "cost": 4.99 if delivery_type == "standard" else 8.99,
            "time": "1-3 business days",
            "availability": "Available",
            "recommended": delivery_type in ["standard", "express"]
        },
        {
            "method": "third_party",
            "name": "3rd Party Fulfillment",
            "cost": 6.99 if delivery_type == "standard" else 15.99,
            "time": "2-5 business days" if delivery_type == "standard" else "Same day",
            "availability": "Available",
            "recommended": delivery_type == "same_day"
        }
    ]

    conn.close()
    return {"options": options}

@app.route('/api/orders/<int:order_id>/update-fulfillment', methods=["POST"])
def update_fulfillment_method(order_id):
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401

    data = request.get_json()
    fulfillment_method = data.get("method")

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("""
        UPDATE orders 
        SET fulfillment_method = ? 
        WHERE id = ?
    """, (fulfillment_method, order_id))

    # Log the fulfillment decision
    c.execute("""
        INSERT INTO fulfillment_metrics (order_id, fulfillment_method, cost_efficiency)
        VALUES (?, ?, ?)
    """, (order_id, fulfillment_method, 0.85))  # Mock efficiency score

    conn.commit()
    conn.close()

    return {"success": True, "method": fulfillment_method}

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

        # Get offline transaction fee from master settings
        c.execute("SELECT setting_value FROM master_settings WHERE setting_name = 'offline_transaction_fee'")
        offline_fee_result = c.fetchone()
        offline_transaction_fee = offline_fee_result[0] if offline_fee_result else 0.01

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

        # Calculate offline transaction commission - minimum of 0.01% or 0.01 currency units
        percentage_commission = total_sale_amount * (offline_transaction_fee / 100)
        minimum_commission = 0.01
        commission_amount = max(percentage_commission, minimum_commission)
        
        # Record platform commission if applicable
        if commission_amount > 0:
            c.execute("""
                INSERT INTO platform_earnings (vendor_id, transaction_type, service_type, base_amount, commission_rate, commission_amount)
                VALUES (?, 'offline_sale', 'pos_transaction', ?, ?, ?)
            """, (vendor_id, total_sale_amount, offline_transaction_fee, commission_amount))
            
            # Add commission to ledger - Platform Fee (Debit)
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'debit', 'Platform Fees', ?, ?, 'Offline Transaction Fee')
            """, (vendor_id, commission_amount, f"Offline transaction fee ({offline_transaction_fee}% of ₹{total_sale_amount})"))

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

@app.route('/erp/inventory')
def inventory_management():
    """Main inventory management dashboard"""
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("inventory_management.html", 
                             inventory_summary={}, 
                             inventory_alerts=[], 
                             procurement_summary={},
                             inventory_items=[],
                             chart_data={})

    vendor_id = result[0]

    # Get inventory summary
    c.execute("""
        SELECT COUNT(*) as total_products,
               SUM(quantity) as total_units,
               SUM(quantity * buy_price) as total_value
        FROM products WHERE vendor_id = ?
    """, (vendor_id,))
    
    summary_data = c.fetchone()
    inventory_summary = {
        'total_products': summary_data[0] or 0,
        'total_units': summary_data[1] or 0,
        'total_value': summary_data[2] or 0,
        'turnover_rate': 2.5  # Calculate based on sales data
    }

    # Get inventory alerts (low stock items)
    c.execute("""
        SELECT name, quantity FROM products 
        WHERE vendor_id = ? AND quantity <= 5
        ORDER BY quantity ASC
    """, (vendor_id,))
    
    low_stock_items = c.fetchall()
    inventory_alerts = []
    for item in low_stock_items:
        inventory_alerts.append({
            'product_name': item[0],
            'message': f'Low stock: only {item[1]} units remaining'
        })

    # Procurement summary (mock data)
    procurement_summary = {
        'pending_orders': 3,
        'incoming_units': 150,
        'pending_value': 12500
    }

    # Get detailed inventory items
    c.execute("""
        SELECT id, name, category, quantity, 
               CASE 
                 WHEN quantity <= 5 THEN 'Reorder Now'
                 WHEN quantity <= 15 THEN 'Low Stock'
                 ELSE 'Good'
               END as status,
               CASE 
                 WHEN quantity <= 5 THEN 'danger'
                 WHEN quantity <= 15 THEN 'warning'
                 ELSE 'good'
               END as status_class
        FROM products 
        WHERE vendor_id = ?
        ORDER BY quantity ASC
    """, (vendor_id,))
    
    inventory_items = []
    for item in c.fetchall():
        inventory_items.append({
            'id': item[0],
            'name': item[1],
            'sku': f'SKU-{item[0]:04d}',
            'category': item[2] or 'General',
            'current_stock': item[3],
            'location': 'Main Warehouse',
            'reorder_point': 10,
            'lead_time_days': 7,
            'turnover_rate': 2.1,
            'status': item[4],
            'status_class': item[5],
            'unit_type': 'units'
        })

    # Chart data (mock)
    chart_data = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'turnover_data': [2.1, 2.3, 2.5, 2.2, 2.4, 2.6],
        'stock_data': [150, 145, 160, 155, 170, 165]
    }

    conn.close()
    return render_template("inventory_management.html",
                         inventory_summary=inventory_summary,
                         inventory_alerts=inventory_alerts,
                         procurement_summary=procurement_summary,
                         inventory_items=inventory_items,
                         chart_data=chart_data)

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

# ---- CUSTOMER INTEGRATION API ----

@app.route('/api/customer/<customer_email>/bookings')
def get_customer_bookings(customer_email):
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    vendor_email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (vendor_email,))
    vendor_result = c.fetchone()
    
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}
    
    vendor_id = vendor_result[0]
    
    # Get customer's bookings with this vendor
    c.execute("""
        SELECT service, date, time, status, pet_name
        FROM bookings 
        WHERE vendor_id = ? AND user_email = ?
        ORDER BY date DESC
        LIMIT 10
    """, (vendor_id, customer_email))
    
    bookings_data = c.fetchall()
    bookings = []
    
    for booking in bookings_data:
        bookings.append({
            'service': booking[0],
            'date': booking[1],
            'time': booking[2],
            'status': booking[3],
            'pet_name': booking[4]
        })
    
    conn.close()
    
    return {
        "success": True,
        "bookings": bookings,
        "customer_email": customer_email
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

# ---- DASHBOARD METRICS API ----

@app.route('/api/dashboard/metrics')
def dashboard_metrics():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}
    
    vendor_id = vendor_result[0]
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get pending orders count
    c.execute("""
        SELECT COUNT(*) FROM orders 
        WHERE vendor_id = ? AND status IN ('pending', 'confirmed', 'packed')
    """, (vendor_id,))
    pending_orders = c.fetchone()[0] or 0
    
    # Get today's bookings count
    c.execute("""
        SELECT COUNT(*) FROM bookings 
        WHERE vendor_id = ? AND date = ?
    """, (vendor_id, today))
    todays_bookings = c.fetchone()[0] or 0
    
    # Get today's revenue (from sales and completed bookings)
    c.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM sales_log 
        WHERE vendor_id = ? AND DATE(sale_date) = ?
    """, (vendor_id, today))
    daily_revenue = c.fetchone()[0] or 0
    
    # Add completed booking revenue (estimated)
    c.execute("""
        SELECT COUNT(*) FROM bookings 
        WHERE vendor_id = ? AND date = ? AND status = 'completed'
    """, (vendor_id, today))
    completed_bookings = c.fetchone()[0] or 0
    daily_revenue += completed_bookings * 50  # Estimate $50 per completed booking
    
    # Get low stock items count
    c.execute("""
        SELECT COUNT(*) FROM products 
        WHERE vendor_id = ? AND quantity <= 5
    """, (vendor_id,))
    low_stock_items = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "success": True,
        "pending_orders": pending_orders,
        "todays_bookings": todays_bookings,
        "daily_revenue": daily_revenue,
        "low_stock_items": low_stock_items
    }

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

# ---- ENHANCED FINANCIAL MANAGEMENT ROUTES ----

@app.route('/erp/finance/accounts-receivable')
def accounts_receivable():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("accounts_receivable.html", receivables=[])

    vendor_id = result[0]

    # Get outstanding customer payments (from marketplace orders)
    c.execute("""
        SELECT o.id, o.user_email, o.total_amount, o.order_date, o.status,
               CASE 
                 WHEN o.status = 'confirmed' THEN 'Pending Payment'
                 WHEN o.status = 'paid' THEN 'Paid'
                 WHEN o.status = 'shipped' THEN 'Invoice Sent'
                 ELSE 'Under Review'
               END as ar_status,
               julianday('now') - julianday(o.order_date) as days_outstanding
        FROM orders o
        WHERE o.vendor_id = ? AND o.status != 'cancelled'
        ORDER BY o.order_date DESC
    """, (vendor_id,))
    
    receivables = c.fetchall()
    
    # Calculate AR summary
    c.execute("""
        SELECT 
            SUM(CASE WHEN status != 'paid' THEN total_amount ELSE 0 END) as total_outstanding,
            SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as total_collected,
            COUNT(CASE WHEN status != 'paid' THEN 1 END) as pending_count
        FROM orders WHERE vendor_id = ?
    """, (vendor_id,))
    
    ar_summary = c.fetchone()
    
    conn.close()
    return render_template("accounts_receivable.html", 
                         receivables=receivables, 
                         ar_summary=ar_summary)

@app.route('/erp/finance/accounts-payable')
def accounts_payable():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("accounts_payable.html", payables=[])

    vendor_id = result[0]

    # Get unpaid expenses (representing vendor bills)
    c.execute("""
        SELECT e.id, e.category, e.amount, e.description, e.date,
               'Unpaid' as status,
               julianday('now') - julianday(e.date) as days_outstanding,
               e.date as due_date
        FROM expenses e
        WHERE e.vendor_id = ?
        ORDER BY e.date DESC
    """, (vendor_id,))
    
    payables = c.fetchall()
    
    # Calculate AP summary
    c.execute("""
        SELECT 
            SUM(amount) as total_outstanding,
            COUNT(*) as bill_count,
            AVG(amount) as avg_bill_amount
        FROM expenses WHERE vendor_id = ?
    """, (vendor_id,))
    
    ap_summary = c.fetchone()
    
    conn.close()
    return render_template("accounts_payable.html", 
                         payables=payables, 
                         ap_summary=ap_summary)

@app.route('/erp/finance/balance-sheet')
def balance_sheet():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("balance_sheet.html", balance_sheet={})

    vendor_id = result[0]

    # Calculate Assets
    # Current Assets - Cash
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    cash_from_sales = c.fetchone()[0] or 0
    
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    cash_expenses = c.fetchone()[0] or 0
    
    cash = cash_from_sales - cash_expenses

    # Inventory
    c.execute("SELECT COALESCE(SUM(quantity * buy_price), 0) FROM products WHERE vendor_id=?", (vendor_id,))
    inventory = c.fetchone()[0] or 0

    # Accounts Receivable
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE vendor_id=? AND status != 'paid'", (vendor_id,))
    accounts_receivable = c.fetchone()[0] or 0

    # Total Current Assets
    current_assets = cash + inventory + accounts_receivable

    # Fixed Assets (simplified)
    fixed_assets = 50000  # Placeholder for equipment, furniture, etc.

    total_assets = current_assets + fixed_assets

    # Calculate Liabilities
    # Accounts Payable (unpaid expenses)
    accounts_payable = cash_expenses * 0.3  # Estimate 30% still unpaid

    # Current Liabilities
    current_liabilities = accounts_payable

    # Long-term Debt
    long_term_debt = 25000  # Placeholder

    total_liabilities = current_liabilities + long_term_debt

    # Calculate Equity
    retained_earnings = total_assets - total_liabilities
    owner_equity = 100000  # Initial investment
    total_equity = owner_equity + retained_earnings

    balance_sheet = {
        'assets': {
            'current': {
                'cash': cash,
                'accounts_receivable': accounts_receivable,
                'inventory': inventory,
                'total': current_assets
            },
            'fixed': {
                'equipment': fixed_assets,
                'total': fixed_assets
            },
            'total': total_assets
        },
        'liabilities': {
            'current': {
                'accounts_payable': accounts_payable,
                'total': current_liabilities
            },
            'long_term': {
                'debt': long_term_debt,
                'total': long_term_debt
            },
            'total': total_liabilities
        },
        'equity': {
            'owner_equity': owner_equity,
            'retained_earnings': retained_earnings,
            'total': total_equity
        }
    }

    conn.close()
    return render_template("balance_sheet.html", balance_sheet=balance_sheet)

@app.route('/erp/finance/cash-flow')
def cash_flow_statement():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("cash_flow.html", cash_flow={})

    vendor_id = result[0]

    # Operating Activities
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=? AND sale_date >= date('now', '-30 days')", (vendor_id,))
    cash_from_sales = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE vendor_id=? AND date >= date('now', '-30 days')", (vendor_id,))
    cash_for_expenses = c.fetchone()[0] or 0

    operating_cash_flow = cash_from_sales - cash_for_expenses

    # Investing Activities (simplified)
    investing_cash_flow = -5000  # Equipment purchases

    # Financing Activities (simplified)
    financing_cash_flow = 0  # No financing activities

    net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow

    cash_flow = {
        'operating': {
            'cash_from_sales': cash_from_sales,
            'cash_for_expenses': -cash_for_expenses,
            'net_operating': operating_cash_flow
        },
        'investing': {
            'equipment_purchases': investing_cash_flow,
            'net_investing': investing_cash_flow
        },
        'financing': {
            'net_financing': financing_cash_flow
        },
        'net_change': net_cash_flow,
        'beginning_cash': 25000,  # Assumed starting balance
        'ending_cash': 25000 + net_cash_flow
    }

    conn.close()
    return render_template("cash_flow.html", cash_flow=cash_flow)

@app.route('/erp/finance/tax-management')
def tax_management():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID and tax settings
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("tax_management.html", tax_data={})

    vendor_id = result[0]

    # Get GST rate from settings
    c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    gst_result = c.fetchone()
    gst_rate = gst_result[0] if gst_result else 18.0

    # Calculate tax liabilities
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_sales = c.fetchone()[0] or 0

    gst_on_sales = total_sales * (gst_rate / 100)
    
    # Input tax credit (simplified)
    input_tax_credit = gst_on_sales * 0.6  # Assuming 60% input credit
    
    net_gst_payable = gst_on_sales - input_tax_credit

    tax_data = {
        'gst_rate': gst_rate,
        'total_sales': total_sales,
        'gst_on_sales': gst_on_sales,
        'input_tax_credit': input_tax_credit,
        'net_gst_payable': net_gst_payable,
        'last_filing_date': '2024-01-20',
        'next_due_date': '2024-02-20'
    }

    conn.close()
    return render_template("tax_management.html", tax_data=tax_data)

@app.route('/erp/finance/planning-analysis')
def financial_planning():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("financial_planning.html", planning_data={})

    vendor_id = result[0]

    # Get current financial data for analysis
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    current_revenue = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    current_expenses = c.fetchone()[0] or 0

    # Budget vs Actual analysis
    budget_revenue = current_revenue * 1.2  # 20% growth target
    budget_expenses = current_expenses * 1.1  # 10% expense increase
    
    revenue_variance = current_revenue - budget_revenue
    expense_variance = current_expenses - budget_expenses

    # Scenario planning
    best_case_revenue = current_revenue * 1.5
    worst_case_revenue = current_revenue * 0.8
    
    planning_data = {
        'current': {
            'revenue': current_revenue,
            'expenses': current_expenses,
            'profit': current_revenue - current_expenses
        },
        'budget': {
            'revenue': budget_revenue,
            'expenses': budget_expenses,
            'profit': budget_revenue - budget_expenses
        },
        'variance': {
            'revenue': revenue_variance,
            'expense': expense_variance,
            'revenue_percent': (revenue_variance / budget_revenue * 100) if budget_revenue > 0 else 0
        },
        'scenarios': {
            'best_case': {
                'revenue': best_case_revenue,
                'profit': best_case_revenue - (current_expenses * 1.2)
            },
            'worst_case': {
                'revenue': worst_case_revenue,
                'profit': worst_case_revenue - current_expenses
            }
        }
    }

    conn.close()
    return render_template("financial_planning.html", planning_data=planning_data)

@app.route('/erp/finance/revenue-recognition')
def revenue_recognition():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("revenue_recognition.html", revenue_data={})

    vendor_id = result[0]

    # Get revenue recognition data
    c.execute("""
        SELECT 
            DATE(sale_date) as recognition_date,
            SUM(total_amount) as daily_revenue,
            COUNT(*) as transaction_count
        FROM sales_log 
        WHERE vendor_id=? 
        GROUP BY DATE(sale_date)
        ORDER BY sale_date DESC
        LIMIT 30
    """, (vendor_id,))
    
    daily_revenue = c.fetchall()

    # Deferred revenue (for future services like grooming bookings)
    c.execute("""
        SELECT COALESCE(SUM(
            CASE 
                WHEN date > date('now') THEN 100.0
                ELSE 0 
            END
        ), 0) as deferred_revenue
        FROM bookings WHERE vendor_id=?
    """, (vendor_id,))
    
    deferred_revenue = c.fetchone()[0] or 0

    # Revenue recognition summary
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_recognized = c.fetchone()[0] or 0

    revenue_data = {
        'total_recognized': total_recognized,
        'deferred_revenue': deferred_revenue,
        'recognition_method': 'Point of Sale / Service Completion',
        'compliance_standard': 'Indian GAAP / Ind AS 115',
        'daily_revenue': daily_revenue
    }

    conn.close()
    return render_template("revenue_recognition.html", revenue_data=revenue_data)

# ---- LANGUAGE SETTINGS ROUTES ----

@app.route('/settings')
def app_settings():
    if "user" not in session and "vendor" not in session:
        return redirect(url_for("login"))
    
    return render_template("app_settings.html")

@app.route('/set-language', methods=["POST"])
def set_language():
    lang_code = request.form.get("language")
    if i18n.set_language(lang_code):
        flash(t("language_updated_successfully"))
    else:
        flash(t("invalid_language_selection"))
    
    # Redirect back to the referrer or dashboard
    return redirect(request.referrer or url_for("dashboard"))

@app.route('/api/set-language', methods=["POST"])
def api_set_language():
    """API endpoint for setting language"""
    data = request.get_json()
    lang_code = data.get("language")
    
    if i18n.set_language(lang_code):
        return {"success": True, "message": t("language_updated_successfully")}
    else:
        return {"success": False, "message": t("invalid_language_selection")}, 400

@app.route('/api/translations/<lang_code>')
def get_translations(lang_code):
    """API endpoint to get translations for a specific language"""
    if lang_code in i18n.supported_languages:
        return jsonify(i18n.translations.get(lang_code, {}))
    else:
        return {"error": "Language not supported"}, 404

# ---- DISCOUNT MANAGEMENT ROUTES ----

@app.route('/erp/discounts')
def discount_management():
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
        return render_template("discount_management.html", products=[])

    vendor_id = vendor_result[0]

    # Get all products with discount information
    c.execute("""
        SELECT p.id, p.name, p.buy_price, p.sale_price, p.quantity,
               COALESCE(pd.discount_type, 'none') as discount_type,
               COALESCE(pd.discount_value, 0) as discount_value,
               COALESCE(pd.is_active, 0) as is_active,
               CASE 
                 WHEN pd.discount_type = 'percentage' THEN p.sale_price * (1 - pd.discount_value / 100)
                 WHEN pd.discount_type = 'fixed' THEN p.sale_price - pd.discount_value
                 ELSE p.sale_price
               END as discounted_price
        FROM products p
        LEFT JOIN product_discounts pd ON p.id = pd.product_id
        WHERE p.vendor_id = ?
        ORDER BY p.name
    """, (vendor_id,))
    
    products = c.fetchall()
    
    # Get blanket discount information
    c.execute("""
        SELECT discount_type, discount_value, is_active 
        FROM vendor_blanket_discounts 
        WHERE vendor_id = ?
    """, (vendor_id,))
    
    blanket_discount = c.fetchone()
    
    conn.close()
    return render_template("discount_management.html", 
                         products=products, 
                         blanket_discount=blanket_discount)

@app.route('/erp/discounts/apply', methods=["POST"])
def apply_discount():
    if "vendor" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    email = session["vendor"]
    data = request.get_json()
    
    product_id = data.get("product_id")
    discount_type = data.get("discount_type")  # 'percentage' or 'fixed'
    discount_value = float(data.get("discount_value", 0))
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Verify product belongs to vendor
    c.execute("SELECT sale_price FROM products WHERE id = ? AND vendor_id = ?", (product_id, vendor_id))
    product_data = c.fetchone()
    if not product_data:
        conn.close()
        return {"success": False, "error": "Product not found"}, 404

    sale_price = product_data[0]

    # Validate discount
    if discount_type == "percentage" and (discount_value < 0 or discount_value > 100):
        conn.close()
        return {"success": False, "error": "Percentage discount must be between 0 and 100"}, 400
    
    if discount_type == "fixed" and discount_value >= sale_price:
        conn.close()
        return {"success": False, "error": "Fixed discount cannot be greater than or equal to sale price"}, 400

    # Insert or update discount
    c.execute("""
        INSERT OR REPLACE INTO product_discounts 
        (product_id, discount_type, discount_value, is_active, vendor_id)
        VALUES (?, ?, ?, 1, ?)
    """, (product_id, discount_type, discount_value, vendor_id))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Discount applied successfully"}

@app.route('/erp/discounts/remove', methods=["POST"])
def remove_discount():
    if "vendor" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    email = session["vendor"]
    data = request.get_json()
    product_id = data.get("product_id")
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Remove discount
    c.execute("DELETE FROM product_discounts WHERE product_id = ? AND vendor_id = ?", (product_id, vendor_id))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Discount removed successfully"}

@app.route('/erp/discounts/blanket', methods=["POST"])
def apply_blanket_discount():
    if "vendor" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    email = session["vendor"]
    data = request.get_json()
    
    discount_type = data.get("discount_type")
    discount_value = float(data.get("discount_value", 0))
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Validate discount
    if discount_type == "percentage" and (discount_value < 0 or discount_value > 100):
        conn.close()
        return {"success": False, "error": "Percentage discount must be between 0 and 100"}, 400

    # Insert or update blanket discount
    c.execute("""
        INSERT OR REPLACE INTO vendor_blanket_discounts 
        (vendor_id, discount_type, discount_value, is_active)
        VALUES (?, ?, ?, 1)
    """, (vendor_id, discount_type, discount_value))

    # Apply blanket discount to all products without individual discounts
    if discount_type == "percentage":
        c.execute("""
            INSERT OR REPLACE INTO product_discounts (product_id, discount_type, discount_value, is_active, vendor_id)
            SELECT p.id, ?, ?, 1, ?
            FROM products p
            LEFT JOIN product_discounts pd ON p.id = pd.product_id
            WHERE p.vendor_id = ? AND pd.product_id IS NULL
        """, (discount_type, discount_value, vendor_id, vendor_id))
    else:  # fixed discount
        c.execute("""
            INSERT OR REPLACE INTO product_discounts (product_id, discount_type, discount_value, is_active, vendor_id)
            SELECT p.id, ?, ?, 1, ?
            FROM products p
            LEFT JOIN product_discounts pd ON p.id = pd.product_id
            WHERE p.vendor_id = ? AND pd.product_id IS NULL AND p.sale_price > ?
        """, (discount_type, discount_value, vendor_id, vendor_id, discount_value))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Blanket discount applied successfully"}

@app.route('/erp/discounts/blanket/remove', methods=["POST"])
def remove_blanket_discount():
    if "vendor" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    email = session["vendor"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Remove blanket discount
    c.execute("DELETE FROM vendor_blanket_discounts WHERE vendor_id = ?", (vendor_id,))
    
    # Remove all product discounts
    c.execute("DELETE FROM product_discounts WHERE vendor_id = ?", (vendor_id,))

    conn.commit()
    conn.close()

    return {"success": True, "message": "All discounts removed successfully"}

# ---- CRM ROUTES ----

@app.route('/erp/crm')
def crm_dashboard():
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
        return render_template("crm_dashboard.html", stats={}, recent_interactions=[])

    vendor_id = vendor_result[0]

    # Get CRM statistics
    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id = ?", (vendor_id,))
    total_customers = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id = ? AND customer_status = 'prospect'", (vendor_id,))
    total_prospects = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_opportunities WHERE vendor_id = ? AND stage NOT IN ('closed_won', 'closed_lost')", (vendor_id,))
    active_opportunities = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(expected_value), 0) FROM crm_opportunities WHERE vendor_id = ? AND stage NOT IN ('closed_won', 'closed_lost')", (vendor_id,))
    pipeline_value = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_tasks WHERE vendor_id = ? AND status = 'pending' AND due_date <= date('now', '+7 days')", (vendor_id,))
    upcoming_tasks = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_offline_data WHERE vendor_id = ? AND invited_status = 'pending'", (vendor_id,))
    offline_leads = c.fetchone()[0] or 0

    stats = {
        'total_customers': total_customers,
        'total_prospects': total_prospects,
        'active_opportunities': active_opportunities,
        'pipeline_value': pipeline_value,
        'upcoming_tasks': upcoming_tasks,
        'offline_leads': offline_leads
    }

    # Get recent interactions
    c.execute("""
        SELECT ci.interaction_type, ci.description, ci.interaction_date, 
               cc.first_name, cc.last_name, ci.outcome
        FROM crm_interactions ci
        JOIN crm_customers cc ON ci.customer_id = cc.id
        WHERE ci.vendor_id = ?
        ORDER BY ci.interaction_date DESC
        LIMIT 10
    """, (vendor_id,))
    recent_interactions = c.fetchall()

    conn.close()
    return render_template("crm_dashboard.html", stats=stats, recent_interactions=recent_interactions)

@app.route('/erp/crm/customers')
def crm_customers():
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
        return render_template("crm_customers.html", customers=[])

    vendor_id = vendor_result[0]

    # Get all customers for this vendor
    c.execute("""
        SELECT cc.*, 
               COUNT(DISTINCT cp.id) as pet_count,
               COUNT(DISTINCT ci.id) as interaction_count,
               MAX(ci.interaction_date) as last_interaction
        FROM crm_customers cc
        LEFT JOIN crm_pets cp ON cc.id = cp.customer_id
        LEFT JOIN crm_interactions ci ON cc.id = ci.customer_id
        WHERE cc.vendor_id = ?
        GROUP BY cc.id
        ORDER BY cc.created_at DESC
    """, (vendor_id,))
    customers = c.fetchall()

    conn.close()
    return render_template("crm_customers.html", customers=customers)

@app.route('/erp/crm/customer/<int:customer_id>')
def crm_customer_detail(customer_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID and verify access
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return "Vendor not found", 404

    vendor_id = vendor_result[0]

    # Get customer details
    c.execute("SELECT * FROM crm_customers WHERE id = ? AND vendor_id = ?", (customer_id, vendor_id))
    customer = c.fetchone()
    if not customer:
        conn.close()
        return "Customer not found", 404

    # Get customer's pets
    c.execute("SELECT * FROM crm_pets WHERE customer_id = ?", (customer_id,))
    pets = c.fetchall()

    # Get interaction history
    c.execute("""
        SELECT * FROM crm_interactions 
        WHERE customer_id = ? 
        ORDER BY interaction_date DESC
    """, (customer_id,))
    interactions = c.fetchall()

    # Get opportunities
    c.execute("SELECT * FROM crm_opportunities WHERE customer_id = ?", (customer_id,))
    opportunities = c.fetchall()

    # Get purchase history from existing orders
    c.execute("""
        SELECT o.id, o.total_amount, o.status, o.order_date,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_email = ? AND o.vendor_id = ?
        GROUP BY o.id
        ORDER BY o.order_date DESC
    """, (customer[3], vendor_id))  # customer[3] is user_email
    purchase_history = c.fetchall()

    conn.close()
    return render_template("crm_customer_detail.html", 
                         customer=customer, 
                         pets=pets, 
                         interactions=interactions, 
                         opportunities=opportunities,
                         purchase_history=purchase_history)

@app.route('/erp/crm/customer/add', methods=["GET", "POST"])
def add_crm_customer():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    
    if request.method == "POST":
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            conn.close()
            flash("Vendor not found")
            return redirect(url_for("crm_customers"))

        vendor_id = vendor_result[0]

        # Get form data
        customer_data = {
            'customer_type': request.form.get("customer_type", "online"),
            'user_email': request.form.get("user_email"),
            'first_name': request.form.get("first_name"),
            'last_name': request.form.get("last_name"),
            'phone': request.form.get("phone"),
            'secondary_phone': request.form.get("secondary_phone"),
            'address': request.form.get("address"),
            'city': request.form.get("city"),
            'state': request.form.get("state"),
            'pincode': request.form.get("pincode"),
            'customer_source': request.form.get("customer_source"),
            'customer_status': request.form.get("customer_status", "active"),
            'lifecycle_stage': request.form.get("lifecycle_stage", "new"),
            'notes': request.form.get("notes"),
            'preferred_contact_method': request.form.get("preferred_contact_method", "email")
        }

        # Insert customer
        c.execute("""
            INSERT INTO crm_customers 
            (vendor_id, customer_type, user_email, first_name, last_name, phone, secondary_phone, 
             address, city, state, pincode, customer_source, customer_status, lifecycle_stage, 
             notes, preferred_contact_method, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, customer_data['customer_type'], customer_data['user_email'], 
              customer_data['first_name'], customer_data['last_name'], customer_data['phone'],
              customer_data['secondary_phone'], customer_data['address'], customer_data['city'],
              customer_data['state'], customer_data['pincode'], customer_data['customer_source'],
              customer_data['customer_status'], customer_data['lifecycle_stage'], 
              customer_data['notes'], customer_data['preferred_contact_method'], email))

        customer_id = c.lastrowid

        # Add pet information if provided
        pet_name = request.form.get("pet_name")
        if pet_name:
            c.execute("""
                INSERT INTO crm_pets 
                (customer_id, pet_name, pet_type, breed, age, weight, gender, special_needs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_id, pet_name, request.form.get("pet_type"), 
                  request.form.get("breed"), request.form.get("age"),
                  request.form.get("weight"), request.form.get("gender"),
                  request.form.get("special_needs")))

        conn.commit()
        conn.close()

        flash("Customer added successfully!")
        return redirect(url_for("crm_customer_detail", customer_id=customer_id))

    return render_template("add_crm_customer.html")

@app.route('/erp/crm/offline-data')
def crm_offline_data():
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
        return render_template("crm_offline_data.html", offline_data=[])

    vendor_id = vendor_result[0]

    # Get all offline data for this vendor
    c.execute("""
        SELECT * FROM crm_offline_data 
        WHERE vendor_id = ? 
        ORDER BY collection_date DESC
    """, (vendor_id,))
    offline_data = c.fetchall()

    conn.close()
    return render_template("crm_offline_data.html", offline_data=offline_data)

@app.route('/erp/crm/offline-data/add', methods=["GET", "POST"])
def add_offline_data():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    
    if request.method == "POST":
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            conn.close()
            flash("Vendor not found")
            return redirect(url_for("crm_offline_data"))

        vendor_id = vendor_result[0]

        # Insert offline data
        c.execute("""
            INSERT INTO crm_offline_data 
            (vendor_id, collected_by, first_name, last_name, phone, email, address, city,
             pet_name, pet_type, service_interest, notes, collection_method, follow_up_priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, email, request.form.get("first_name"), request.form.get("last_name"),
              request.form.get("phone"), request.form.get("email"), request.form.get("address"),
              request.form.get("city"), request.form.get("pet_name"), request.form.get("pet_type"),
              request.form.get("service_interest"), request.form.get("notes"),
              request.form.get("collection_method"), request.form.get("follow_up_priority")))

        conn.commit()
        conn.close()

        flash("Offline customer data added successfully!")
        return redirect(url_for("crm_offline_data"))

    return render_template("add_offline_data.html")

@app.route('/erp/crm/offline-data/invite/<int:data_id>', methods=["POST"])
def invite_offline_customer(data_id):
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Get offline data
    c.execute("SELECT * FROM crm_offline_data WHERE id = ? AND vendor_id = ?", (data_id, vendor_id))
    offline_data = c.fetchone()
    if not offline_data:
        conn.close()
        return {"error": "Data not found"}, 404

    # Update invitation status
    c.execute("""
        UPDATE crm_offline_data 
        SET invited_status = 'invited', invitation_sent_date = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data_id,))

    # Add to CRM customers if they have an email
    if offline_data[5]:  # email field
        # Check if customer already exists
        c.execute("SELECT id FROM crm_customers WHERE user_email = ? AND vendor_id = ?", 
                 (offline_data[5], vendor_id))
        existing = c.fetchone()
        
        if not existing:
            c.execute("""
                INSERT INTO crm_customers 
                (vendor_id, customer_type, user_email, first_name, last_name, phone, address, city,
                 customer_source, customer_status, lifecycle_stage, notes, assigned_to)
                VALUES (?, 'offline', ?, ?, ?, ?, ?, ?, 'offline_collection', 'prospect', 'lead', ?, ?)
            """, (vendor_id, offline_data[5], offline_data[3], offline_data[4], offline_data[6],
                  offline_data[7], offline_data[8], f"Offline collection: {offline_data[12]}", email))

    conn.commit()
    conn.close()

    # In a real application, you would send an email/SMS invitation here
    flash(f"Invitation sent to {offline_data[3]} {offline_data[4] or ''}")
    return {"success": True}

@app.route('/erp/crm/interactions')
def crm_interactions():
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
        return render_template("crm_interactions.html", interactions=[])

    vendor_id = vendor_result[0]

    # Get all interactions for this vendor
    c.execute("""
        SELECT ci.*, cc.first_name, cc.last_name, cc.customer_type
        FROM crm_interactions ci
        JOIN crm_customers cc ON ci.customer_id = cc.id
        WHERE ci.vendor_id = ?
        ORDER BY ci.interaction_date DESC
        LIMIT 100
    """, (vendor_id,))
    interactions = c.fetchall()

    conn.close()
    return render_template("crm_interactions.html", interactions=interactions)

@app.route('/erp/crm/interaction/add', methods=["GET", "POST"])
def add_interaction():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    
    if request.method == "POST":
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            conn.close()
            flash("Vendor not found")
            return redirect(url_for("crm_interactions"))

        vendor_id = vendor_result[0]

        # Insert interaction
        c.execute("""
            INSERT INTO crm_interactions 
            (customer_id, vendor_id, interaction_type, direction, subject, description, 
             outcome, follow_up_required, follow_up_date, duration_minutes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (request.form.get("customer_id"), vendor_id, request.form.get("interaction_type"),
              request.form.get("direction"), request.form.get("subject"), 
              request.form.get("description"), request.form.get("outcome"),
              1 if request.form.get("follow_up_required") else 0,
              request.form.get("follow_up_date"), request.form.get("duration_minutes"), email))

        # Update customer's last contact date
        c.execute("""
            UPDATE crm_customers 
            SET last_contact_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request.form.get("customer_id"),))

        conn.commit()
        conn.close()

        flash("Interaction logged successfully!")
        return redirect(url_for("crm_interactions"))

    # Get customers for dropdown
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if vendor_result:
        vendor_id = vendor_result[0]
        c.execute("""
            SELECT id, first_name, last_name, user_email 
            FROM crm_customers 
            WHERE vendor_id = ? 
            ORDER BY first_name
        """, (vendor_id,))
        customers = c.fetchall()
    else:
        customers = []
    
    conn.close()
    return render_template("add_interaction.html", customers=customers)

# Sync existing users to CRM
@app.route('/erp/crm/sync-existing-customers', methods=["POST"])
def sync_existing_customers():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"error": "Vendor not found"}, 404

    vendor_id = vendor_result[0]

    # Get existing orders and bookings to sync customers
    c.execute("""
        SELECT DISTINCT user_email, SUM(total_amount) as total_spent, COUNT(*) as order_count
        FROM orders 
        WHERE vendor_id = ? AND user_email IS NOT NULL AND user_email != ''
        GROUP BY user_email
    """, (vendor_id,))
    order_customers = c.fetchall()

    c.execute("""
        SELECT DISTINCT user_email, COUNT(*) as booking_count
        FROM bookings 
        WHERE vendor_id = ? AND user_email IS NOT NULL AND user_email != ''
        GROUP BY user_email
    """, (vendor_id,))
    booking_customers = c.fetchall()

    synced_count = 0

    # Sync order customers
    for customer in order_customers:
        user_email = customer[0]
        total_spent = customer[1]
        order_count = customer[2]

        # Check if already exists in CRM
        c.execute("SELECT id FROM crm_customers WHERE user_email = ? AND vendor_id = ?", 
                 (user_email, vendor_id))
        existing = c.fetchone()

        if not existing:
            # Extract name from email (fallback)
            name_part = user_email.split('@')[0]
            first_name = name_part.replace('.', ' ').replace('_', ' ').title()

            c.execute("""
                INSERT INTO crm_customers 
                (vendor_id, customer_type, user_email, first_name, customer_source, 
                 customer_status, lifecycle_stage, total_spent, total_orders, 
                 avg_order_value, assigned_to)
                VALUES (?, 'online', ?, ?, 'marketplace', 'active', 'customer', ?, ?, ?, ?)
            """, (vendor_id, user_email, first_name, total_spent, order_count, 
                  total_spent / order_count if order_count > 0 else 0, email))
            synced_count += 1
        else:
            # Update existing customer data
            c.execute("""
                UPDATE crm_customers 
                SET total_spent = ?, total_orders = ?, avg_order_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (total_spent, order_count, total_spent / order_count if order_count > 0 else 0, existing[0]))

    conn.commit()
    conn.close()

    return {"success": True, "synced_count": synced_count}

@app.route('/ngo/register-stray', methods=["GET", "POST"])
def register_stray():
    """Register a new stray dog"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    if request.method == "POST":
        import secrets
        import hashlib
        
        ngo_id = session["ngo_id"]
        ngo_email = session["ngo"]
        
        # Generate unique stray UID and QR code
        stray_uid = f"STR-{secrets.token_hex(3).upper()}-2024"
        qr_code = f"QRSTR{secrets.token_hex(6).upper()}"
        
        # Get location data
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        location_address = request.form.get("location_address", "")
        
        # Handle photo upload
        photo_url = ""
        file = request.files.get("photo")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = str(int(datetime.now().timestamp()))
            filename = f"stray_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            photo_url = "/" + filepath
        else:
            flash("Photo is required for stray registration")
            return redirect(url_for("register_stray"))
        
        # Get form data
        stray_data = {
            'breed_type': request.form.get("breed_type"),
            'gender': request.form.get("gender"),
            'age_estimation': request.form.get("age_estimation"),
            'fur_color': request.form.get("fur_color"),
            'distinctive_marks': request.form.get("distinctive_marks"),
            'temperament': request.form.get("temperament", "Unknown")
        }
        
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        try:
            # Insert stray dog
            c.execute("""
                INSERT INTO stray_dogs 
                (stray_uid, qr_code, ngo_id, registered_by_email, photo_url, location_latitude, 
                 location_longitude, location_address, breed_type, gender, age_estimation, 
                 fur_color, distinctive_marks, temperament)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stray_uid, qr_code, ngo_id, ngo_email, photo_url, latitude, longitude,
                  location_address, stray_data['breed_type'], stray_data['gender'], 
                  stray_data['age_estimation'], stray_data['fur_color'], 
                  stray_data['distinctive_marks'], stray_data['temperament']))
            
            stray_id = c.lastrowid
            
            # Update NGO statistics
            c.execute("UPDATE ngo_partners SET total_strays_registered = total_strays_registered + 1 WHERE id = ?", (ngo_id,))
            
            conn.commit()
            conn.close()
            
            flash(f"Stray dog registered successfully! UID: {stray_uid}")
            return redirect(url_for("ngo_dashboard"))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f"Error registering stray: {str(e)}")
    
    return render_template("register_stray.html")

@app.route('/ngo/add-vaccination', methods=["GET", "POST"])
def add_vaccination():
    """Add vaccination record for a stray"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    if request.method == "POST":
        ngo_id = session["ngo_id"]
        signature_key = session["ngo_signature_key"]
        
        stray_uid = request.form.get("stray_uid")
        
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        # Get stray ID
        c.execute("SELECT id FROM stray_dogs WHERE stray_uid = ? AND ngo_id = ?", (stray_uid, ngo_id))
        stray_result = c.fetchone()
        
        if not stray_result:
            flash("Stray not found or you don't have permission to update this stray")
            return redirect(url_for("add_vaccination"))
        
        stray_id = stray_result[0]
        
        # Handle vaccination photo upload
        vaccination_photo_url = ""
        file = request.files.get("vaccination_photo")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = str(int(datetime.now().timestamp()))
            filename = f"vaccination_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            vaccination_photo_url = "/" + filepath
            
            # Generate image hash for duplicate detection
            with open(filepath, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
        else:
            flash("Vaccination photo is required")
            return redirect(url_for("add_vaccination"))
        
        # Handle certificate upload
        certificate_url = ""
        cert_file = request.files.get("certificate")
        if cert_file and cert_file.filename:
            filename = secure_filename(cert_file.filename)
            timestamp = str(int(datetime.now().timestamp()))
            filename = f"certificate_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cert_file.save(filepath)
            certificate_url = "/" + filepath
        
        # Get vaccination data
        vaccination_data = {
            'vaccine_name': request.form.get("vaccine_name"),
            'vaccine_batch_number': request.form.get("vaccine_batch_number"),
            'vaccine_expiration_date': request.form.get("vaccine_expiration_date"),
            'vaccinator_name': request.form.get("vaccinator_name"),
            'vaccinator_contact': request.form.get("vaccinator_contact"),
            'vaccinator_license': request.form.get("vaccinator_license"),
            'vaccination_date': request.form.get("vaccination_date"),
            'vaccination_cost': float(request.form.get("vaccination_cost", 0)),
            'additional_notes': request.form.get("additional_notes", "")
        }
        
        # Generate digital signature
        signature_data = f"{stray_uid}_{vaccination_data['vaccine_name']}_{vaccination_data['vaccination_date']}_{signature_key}"
        digital_signature = hashlib.sha256(signature_data.encode()).hexdigest()
        signature_timestamp = datetime.now().isoformat()
        
        try:
            # Check for duplicate images
            c.execute("SELECT id FROM stray_vaccinations WHERE image_hash = ?", (image_hash,))
            if c.fetchone():
                c.execute("""
                    INSERT INTO stray_audit_logs (vaccination_id, audit_type, audit_result, audit_details, audited_by)
                    VALUES (?, 'image_verification', 'flagged', 'Duplicate image detected', 'system')
                """, (None,))
                flash("Warning: This vaccination image appears to be a duplicate. Entry flagged for review.")
            
            # Insert vaccination record
            c.execute("""
                INSERT INTO stray_vaccinations 
                (stray_id, ngo_id, vaccination_photo_url, certificate_url, vaccine_name, 
                 vaccine_batch_number, vaccine_expiration_date, vaccinator_name, vaccinator_contact,
                 vaccinator_license, digital_signature, signature_timestamp, vaccination_date,
                 vaccination_cost, additional_notes, image_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stray_id, ngo_id, vaccination_photo_url, certificate_url, 
                  vaccination_data['vaccine_name'], vaccination_data['vaccine_batch_number'],
                  vaccination_data['vaccine_expiration_date'], vaccination_data['vaccinator_name'],
                  vaccination_data['vaccinator_contact'], vaccination_data['vaccinator_license'],
                  digital_signature, signature_timestamp, vaccination_data['vaccination_date'],
                  vaccination_data['vaccination_cost'], vaccination_data['additional_notes'], image_hash))
            
            # Update stray vaccination count
            c.execute("""
                UPDATE stray_dogs 
                SET total_vaccinations = total_vaccinations + 1, last_vaccination_date = ?
                WHERE id = ?
            """, (vaccination_data['vaccination_date'], stray_id))
            
            # Update NGO statistics
            c.execute("UPDATE ngo_partners SET total_vaccinations = total_vaccinations + 1 WHERE id = ?", (ngo_id,))
            
            # Add expense record
            c.execute("""
                INSERT INTO stray_expenses (stray_id, ngo_id, expense_type, amount, description, expense_date, created_by)
                VALUES (?, ?, 'Vaccination', ?, ?, ?, ?)
            """, (stray_id, ngo_id, vaccination_data['vaccination_cost'], 
                  f"Vaccination: {vaccination_data['vaccine_name']}", 
                  vaccination_data['vaccination_date'], session["ngo"]))
            
            conn.commit()
            conn.close()
            
            flash(f"Vaccination recorded successfully with digital signature!")
            return redirect(url_for("ngo_dashboard"))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f"Error recording vaccination: {str(e)}")
    
    # Get strays for dropdown
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT stray_uid, breed_type FROM stray_dogs WHERE ngo_id = ? AND current_status = 'Active'", (session["ngo_id"],))
    strays = c.fetchall()
    conn.close()
    
    return render_template("add_vaccination.html", strays=strays)

@app.route('/api/citizen-report', methods=["POST"])
def citizen_report():
    """API endpoint for citizen reports"""
    data = request.get_json()
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    try:
        # Get stray ID if provided
        stray_id = None
        if data.get('stray_uid'):
            c.execute("SELECT id FROM stray_dogs WHERE stray_uid = ?", (data['stray_uid'],))
            stray_result = c.fetchone()
            if stray_result:
                stray_id = stray_result[0]
        
        # Insert citizen report
        c.execute("""
            INSERT INTO citizen_reports 
            (stray_id, reporter_email, report_type, description, priority_level)
            VALUES (?, ?, ?, ?, ?)
        """, (stray_id, data.get('reporter_email'), data['report_type'], 
              data['description'], 'medium'))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Report submitted successfully"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}, 500

@app.route('/ngo/logout')
def ngo_logout():
    """NGO logout"""
    session.pop("ngo", None)
    session.pop("ngo_id", None)
    session.pop("ngo_name", None)
    session.pop("ngo_type", None)
    session.pop("ngo_signature_key", None)
    return redirect(url_for("stray_tracker_home"))

# Run app
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
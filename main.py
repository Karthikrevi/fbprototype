from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, abort
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

# Import WhatsApp routes and module manager
from whatsapp_routes import whatsapp_bp
from module_manager import ModuleManager, require_module

# Import new utilities
from database_utils import db_connection, get_vendor_id, is_user_logged_in, get_vendor_stats
from error_handlers import setup_error_handlers, log_error, handle_database_error
from vendor_services import VendorServiceManager

# Import email verification utilities
from encryption import encrypt_data, decrypt_data
from email_verification import generate_email_token, confirm_email_token, send_verification_email
encrypted_email = encrypt_data('user@example.com')
original_email = decrypt_data(encrypted_email)

# FurrVet runs as a separate application

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

    # User activity logging table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')

    # Error logging table
    c.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            user_email TEXT,
            additional_data TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0
        )
    ''')

    # Performance metrics table
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            vendor_id INTEGER,
            measurement_date TEXT DEFAULT CURRENT_TIMESTAMP,
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

    # Vendor Services Management
    c.execute('''
        CREATE TABLE IF NOT EXISTS vendor_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            duration_minutes INTEGER DEFAULT 60,
            category TEXT DEFAULT 'General',
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
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

    # FurrVet tables are managed in the separate furrvet.db database

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

    # Vendor Time Slot Configuration
    c.execute('''
        CREATE TABLE IF NOT EXISTS vendor_time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            opening_time TEXT NOT NULL DEFAULT '09:00',
            closing_time TEXT NOT NULL DEFAULT '18:00',
            slot_duration INTEGER NOT NULL DEFAULT 30,
            lunch_break_start TEXT DEFAULT '13:00',
            lunch_break_end TEXT DEFAULT '14:00',
            max_groomers INTEGER NOT NULL DEFAULT 1,
            days_of_week TEXT NOT NULL DEFAULT 'mon,tue,wed,thu,fri,sat',
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # Time Slot Bookings Tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS time_slot_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            booking_date DATE NOT NULL,
            time_slot TEXT NOT NULL,
            current_bookings INTEGER DEFAULT 0,
            max_capacity INTEGER DEFAULT 1,
            is_available BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    # HR Management Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            position TEXT NOT NULL,
            base_salary REAL NOT NULL,
            hourly_rate REAL NOT NULL,
            join_date TEXT NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'terminated')),
            emergency_contact TEXT,
            address TEXT,
            skills TEXT,
            certifications TEXT,
            profile_image TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            work_date DATE NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            break_duration INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'present' CHECK(status IN ('present', 'absent', 'late', 'leave', 'half_day')),
            notes TEXT,
            approved_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            pay_period_start DATE NOT NULL,
            pay_period_end DATE NOT NULL,
            base_pay REAL NOT NULL,
            overtime_pay REAL DEFAULT 0,
            bonus REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            total_pay REAL NOT NULL,
            payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('pending', 'paid', 'cancelled')),
            payment_date TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            performance_month TEXT NOT NULL,
            services_completed INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0,
            customer_rating REAL DEFAULT 0,
            attendance_rate REAL DEFAULT 0,
            productivity_score REAL DEFAULT 0,
            bonus_earned REAL DEFAULT 0,
            feedback TEXT,
            reviewed_by INTEGER,
            review_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL CHECK(leave_type IN ('sick', 'vacation', 'personal', 'emergency', 'maternity', 'paternity')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_count INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            approved_by INTEGER,
            approval_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_revenue_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            booking_id INTEGER,
            sale_id INTEGER,
            service_type TEXT NOT NULL,
            revenue_amount REAL NOT NULL,
            commission_rate REAL DEFAULT 0,
            commission_amount REAL DEFAULT 0,
            transaction_date DATE NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (sale_id) REFERENCES sales_log(id)
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

    # FurrVet demo data is managed in the separate furrvet.py application

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

# FurrVet ERP Integration
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

    # Invoices/Billing
    c.execute('''
        CREATE TABLE IF NOT EXISTS furrvet_invoices (
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

    # Inventory/Pharmacy
    c.execute('''
        CREATE TABLE IF NOT EXISTS furrvet_inventory (
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

# Run the DB setup on startup
init_erp_db()
init_furrvet_db()

app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup error handlers
setup_error_handlers(app)

# Register i18n functions with Jinja2
app.jinja_env.globals.update(
    t=t,
    get_supported_languages=get_supported_languages,
    get_current_language=get_current_language,
    datetime=datetime
)

# Register JSON filter for templates
import json
app.jinja_env.filters['tojson'] = lambda obj: json.dumps(obj)

# Register WhatsApp blueprint
app.register_blueprint(whatsapp_bp)

# FurrVet ERP Integration
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
            pet_id```python
 INTEGER NOT NULL,
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

    # Invoices/Billing
    c.execute('''
        CREATE TABLE IF NOT EXISTS furrvet_invoices (
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

    # Inventory/Pharmacy
    c.execute('''
        CREATE TABLE IF NOT EXISTS furrvet_inventory (
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

# FurrVet authentication decorator
def furrvet_login_required(f):
    def decorated_function(*args, **kwargs):
        if 'furrvet_vet_id' not in session:
            return redirect(url_for('furrvet_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# FurrVet Routes
@app.route('/furrvet')
@app.route('/furrvet/')
def furrvet_home():
    if 'furrvet_vet_id' in session:
        return redirect(url_for('furrvet_dashboard'))
    return redirect(url_for('furrvet_login'))

@app.route('/furrvet/login', methods=['GET', 'POST'])
def furrvet_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('furrvet.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vets WHERE email=? AND password=? AND is_active=1", (email, password))
        vet = c.fetchone()
        conn.close()

        if vet:
            session['furrvet_vet_id'] = vet[0]
            session['furrvet_vet_name'] = vet[1]
            session['furrvet_vet_email'] = vet[2]
            session['furrvet_clinic_name'] = vet[7]
            return redirect(url_for('furrvet_dashboard'))
        else:
            flash('Invalid FurrVet credentials')

    return render_template('furrvet/furrvet_login.html')

@app.route('/furrvet/logout')
def furrvet_logout():
    session.pop('furrvet_vet_id', None)
    session.pop('furrvet_vet_name', None)
    session.pop('furrvet_vet_email', None)
    session.pop('furrvet_clinic_name', None)
    return redirect(url_for('furrvet_login'))

@app.route('/furrvet/dashboard')
@furrvet_login_required
def furrvet_dashboard():
    vet_id = session['furrvet_vet_id']
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
        SELECT COALESCE(SUM(total_amount), 0) FROM furrvet_invoices 
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

    return render_template('furrvet/furrvet_dashboard.html', 
                         stats=stats, 
                         recent_appointments=recent_appointments,
                         vet_name=session['furrvet_vet_name'],
                         clinic_name=session['furrvet_clinic_name'])

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
        phone = request.form.get("phone")
        password = request.form.get("password")
        consent_given = request.form.get("consent") == "on"

        # Validation
        if not email or not password:
            flash("Email and password are required.")
            return render_template("register_new.html")

        if not consent_given:
            flash("You must consent to data processing to create an account.")
            return render_template("register_new.html")

        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return render_template("register_new.html")

        import re
        if not re.search(r'[A-Z]', password):
            flash("Password must contain at least one uppercase letter.")
            return render_template("register_new.html")

        if not re.search(r'[a-z]', password):
            flash("Password must contain at least one lowercase letter.")
            return render_template("register_new.html")

        if not re.search(r'\d', password):
            flash("Password must contain at least one number.")
            return render_template("register_new.html")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash("Password must contain at least one special character.")
            return render_template("register_new.html")

        # Import encryption and security functions
        from encryption import encrypt_data
        from werkzeug.security import generate_password_hash

        # Encrypt PII data
        encrypted_email = encrypt_data(email)
        encrypted_phone = encrypt_data(phone) if phone else None

        if encrypted_email is None:
            flash("Encryption system error. Please try again.")
            return render_template("register_new.html")

        # Hash password
        password_hash = generate_password_hash(password)

        # Save to users database
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()

            # Check if user already exists (by encrypted email comparison)
            c.execute("SELECT id FROM users WHERE email = ?", (encrypted_email,))
            if c.fetchone():
                flash("User already exists with this email.")
                conn.close()
                return render_template("register_new.html")

            # Insert new user
            c.execute("""
                INSERT INTO users (
                    email, phone, password_hash, consent_given, consent_date,
                    data_processing_consent, marketing_consent, consent_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                encrypted_email, encrypted_phone, password_hash, consent_given,
                datetime.now().isoformat(), True, False, "1.0"
            ))

            user_id = c.lastrowid

            # Log consent for audit trail
            c.execute("""
                INSERT INTO user_consent_log (
                    user_id, consent_type, consent_given, consent_version,
                    ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, "registration", consent_given, "1.0",
                request.environ.get('REMOTE_ADDR', ''),
                request.environ.get('HTTP_USER_AGENT', '')
            ))

            # Log data processing activity for GDPR Article 30
            c.execute("""
                INSERT INTO data_processing_log (
                    user_id, activity_type, data_category, purpose, legal_basis
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, "registration", "contact_data", 
                "Account creation and service provision", "consent"
            ))

            # Generate email verification token
            token = generate_email_token(email)
            verification_url = url_for('verify_email', token=token, _external=True)

            # Send verification email
            send_verification_email(email, verification_url)

            conn.commit()
            conn.close()

            flash("Registration successful! Please check your email to verify your account.")
            return redirect(url_for("login"))

        except sqlite3.Error as e:
            flash(f"Database error: {str(e)}")
            return render_template("register_new.html")
        except Exception as e:
            flash(f"Registration failed: {str(e)}")
            return render_template("register_new.html")

    return render_template("register_new.html")

# Email Verification Route
@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = confirm_email_token(token)
    except:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        # Encrypt email for database lookup
        from encryption import encrypt_data
        encrypted_email = encrypt_data(email)

        if encrypted_email is None:
            flash("System error. Please try again.")
            return render_template("login.html")

        # Update user's verified_at timestamp
        c.execute("UPDATE users SET verified_at = ? WHERE email = ?", (datetime.now().isoformat(), encrypted_email))
        conn.commit()
        conn.close()

        flash('Your email has been successfully verified! You can now log in.', 'success')
    except sqlite3.Error as e:
        flash(f"Database error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"Email verification failed: {str(e)}", 'danger')

    return redirect(url_for('login'))

# Login
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Please enter both email and password.")
            return render_template("login.html")

        # Import required functions
        from encryption import encrypt_data
        from werkzeug.security import check_password_hash

        # Encrypt the provided email to match against database
        encrypted_email = encrypt_data(email)

        if encrypted_email is None:
            flash("System error. Please try again.")
            return render_template("login.html")

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()

            # Find user by encrypted email
            c.execute("SELECT id, password_hash, verified_at FROM users WHERE email = ?", (encrypted_email,))
            user = c.fetchone()

            if user:
                user_id, stored_password_hash, verified_at = user

                # Verify password using werkzeug
                if check_password_hash(stored_password_hash, password):
                    if not verified_at:
                        flash("Please verify your email before logging in.")
                        return render_template("login.html")

                    # Update last_accessed timestamp
                    c.execute("""
                        UPDATE users 
                        SET last_accessed = ? 
                        WHERE id = ?
                    """, (datetime.now().isoformat(), user_id))

                    # Log data processing activity for GDPR Article 30
                    c.execute("""
                        INSERT INTO data_processing_log (
                            user_id, activity_type, data_category, purpose, legal_basis
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        user_id, "login", "authentication_data", 
                        "User authentication and session management", "legitimate_interest"
                    ))

                    conn.commit()
                    conn.close()

                    # Set session (store original email for convenience)
                    session["user"] = email
                    session["user_id"] = user_id

                    flash("Login successful!")
                    return redirect(url_for("dashboard"))
                else:
                    # Log failed login attempt
                    c.execute("""
                        UPDATE users 
                        SET failed_login_attempts = COALESCE(failed_login_attempts, 0) + 1
                        WHERE id = ?
                    """, (user_id,))
                    conn.commit()
                    conn.close()

                    flash("Invalid email or password.")
                    return render_template("login.html")
            else:
                conn.close()
                flash("Invalid email or password.")
                return render_template("login.html")

        except sqlite3.Error as e:
            flash(f"Database error: {str(e)}")
            return render_template("login.html")
        except Exception as e:
            flash(f"Login failed: {str(e)}")
            return render_template("login.html")

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

    # Get all vendors that provide grooming/boarding services
    # Removed strict city matching and online requirements for testing
    c.execute("""
        SELECT id, name, email, password, category, city, phone, bio, image_url, latitude, longitude, is_online, account_status, break_start_date, break_end_date, break_reason, address, state, pincode
        FROM vendors 
        WHERE (account_status IS NULL OR account_status = 'active')
        ORDER BY name
    """)
    db_vendors = c.fetchall()

    print(f"Found {len(db_vendors)} vendors in database")  # Debug log

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
            "latitude": vendor[9] or 8.5241,  # Default to Trivandrum coordinates
            "longitude": vendor[10] or 76.9366,
            "is_online": vendor[11],
            "address": vendor[16] or "",
            "state": vendor[17] or "",
            "pincode": vendor[18] or ""
        }
        vendors.append(vendor_data)

    print(f"Returning {len(vendors)} vendors to template")  # Debug log
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
            "services": [
                {
                    "name": "Full Grooming Package",
                    "description": "Complete grooming service including bath, brush, nail trim, and styling",
                    "duration": 120,
                    "price": 45.00,
                    "available_slots": ["09:00", "11:00", "14:00", "16:00"]
                },
                {
                    "name": "Basic Bath & Brush",
                    "description": "Simple bath and brush service for regular maintenance",
                    "duration": 60,
                    "price": 25.00,
                    "available_slots": ["10:00", "12:00", "15:00", "17:00"]
                },
                {
                    "name": "Nail Trimming",
                    "description": "Professional nail trimming service",
                    "duration": 30,
                    "price": 15.00,
                    "available_slots": ["09:30", "13:30", "16:30"]
                },
                {
                    "name": "Flea Treatment",
                    "description": "Comprehensive flea treatment and prevention",
                    "duration": 45,
                    "price": 35.00,
                    "available_slots": ["10:30", "14:30"]
                }
            ],
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

        # Get full vendor information with proper field names
        c.execute("""
            SELECT id, name, email, password, category, city, phone, bio, image_url, 
                   latitude, longitude, is_online, account_status, break_start_date, 
                   break_end_date, break_reason, address, state, pincode
            FROM vendors WHERE id = ?
        """, (vendor_id,))
        data = c.fetchone()

        if data:
            vendor_id_db = data[0]
            vendor_name = data[1]
            vendor_bio = data[7]
            vendor_image = data[8]
            vendor_city = data[5]
            vendor_is_online = data[11]
            vendor_category = data[4]

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

            # Check if vendor has products for marketplace
            c.execute("SELECT COUNT(*) FROM products WHERE vendor_id = ? AND quantity > 0", (vendor_id_db,))
            has_products = c.fetchone()[0] > 0

            # Get services from database
            c.execute("""
                SELECT service_name, description, price, duration_minutes, category
                FROM vendor_services 
                WHERE vendor_id = ? AND is_active = 1
                ORDER BY service_name
            """, (vendor_id_db,))

            services_data = c.fetchall()

            if services_data:
                services = []
                for service in services_data:
                    # Generate time slots based on service duration
                    if service[3] <= 60:  # Short services
                        available_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
                    elif service[3] <= 240:  # Medium services
                        available_slots = ["09:00", "11:00", "14:00", "16:00"]
                    else:  # Long services (boarding, etc.)
                        available_slots = ["18:00"]

                    services.append({
                        "name": service[0],
                        "description": service[1] or "Professional pet care service",
                        "duration": service[3],
                        "price": service[2],
                        "available_slots": available_slots
                    })
            else:
                # Fallback services based on category
                services = []
                if vendor_category and "groom" in vendor_category.lower():
                    services = [
                        {
                            "name": "Basic Grooming",
                            "description": "Professional pet grooming service",
                            "duration": 60,
                            "price": 30.00,
                            "available_slots": ["09:00", "11:00", "14:00", "16:00"]
                        },
                        {
                            "name": "Full Grooming Package",
                            "description": "Complete grooming service with bath, brush, and styling",
                            "duration": 90,
                            "price": 45.00,
                            "available_slots": ["09:00", "11:00", "14:00", "16:00"]
                        }
                    ]
                elif vendor_category and "boarding" in vendor_category.lower():
                    services = [
                        {
                            "name": "Day Boarding",
                            "description": "Safe day care for your pet",
                            "duration": 480,
                            "price": 25.00,
                            "available_slots": ["08:00", "09:00"]
                        },
                        {
                            "name": "Overnight Boarding",
                            "description": "Overnight pet boarding service",
"duration": 1440,
                            "price": 40.00,
                            "available_slots": ["18:00"]
                        }
                    ]
                else:
                    services = [
                        {
                            "name": "Pet Care Service",
                            "description": "General pet care consultation",
                            "duration": 60,
                            "price": 30.00,
                            "available_slots": ["09:00", "11:00", "14:00", "16:00"]
                        }
                    ]

            vendor = {
                "id": vendor_id_db,
                "name": vendor_name or "Pet Care Provider",
                "description": vendor_bio or "Trusted pet care provider.",
                "image": vendor_image or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=600&h=400&fit=crop=face",
                "city": vendor_city or "Unknown",
                "is_online": vendor_is_online,
                "category": vendor_category or "General",
                "rating": avg_rating,
                "level": level,
                "xp": xp,
                "total_reviews": total_reviews,
                "success_rate": success_rate,
                "services": services,
                "has_products": has_products,
                "booking_url": f"/vendor/{vendor_id_db}/book",
                "market_url": f"/marketplace/vendor/{vendor_id_db}"
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
        species = request.form.get("species")
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
            "species": species,
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
        pets[pet_index]["species"] = request.form.get("species")
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

@app.route('/vet/portal')
def furrwings_vet_portal():
    """FurrWings Vet Portal - Enhanced document management interface"""
    if "vet" not in session:
        return redirect(url_for("vet_login"))

    return render_template("furrwings_vet_portal.html")

@app.route('/vet/pet-profile/<int:pet_id>')
def vet_pet_profile(pet_id):
    """Individual pet profile for detailed document management"""
    if "vet" not in session:
        return redirect(url_for("vet_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get pet documents status
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

    pet_info = {
        'id': pet_id,
        'name': f'Pet {pet_id}' if pet_id != 1 else 'Luna',
        'breed': 'Golden Retriever',
        'owner': 'John Smith',
        'owner_email': 'john@example.com',
        'travel_destination': 'USA → India',
        'departure_date': 'Jan 15, 2024',
        'doc_status': doc_status
    }

    conn.close()
    return render_template("vet_pet_profile.html", pet=pet_info, vet_name=session["vet_name"])

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
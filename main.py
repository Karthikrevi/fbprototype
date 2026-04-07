from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, abort, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from replit_db_shim import db
import os
import json
from werkzeug.utils import secure_filename
from math import radians, cos, sin, asin, sqrt
import sqlite3
from datetime import datetime, timedelta
import hashlib
from typing import Optional
from i18n import i18n, t, get_supported_languages, get_current_language
import jwt as pyjwt
from functools import wraps

# Import WhatsApp routes and module manager
from whatsapp_routes import whatsapp_bp
from module_manager import ModuleManager, require_module

# Import new utilities
from database_utils import db_connection, get_vendor_id, is_user_logged_in, get_vendor_stats
from error_handlers import setup_error_handlers, log_error, handle_database_error
from vendor_services import VendorServiceManager

ISO_4217_CURRENCIES = {
    "AED": {"symbol": "د.إ", "name": "UAE Dirham"},
    "AFN": {"symbol": "؋", "name": "Afghan Afghani"},
    "ALL": {"symbol": "L", "name": "Albanian Lek"},
    "AMD": {"symbol": "֏", "name": "Armenian Dram"},
    "ANG": {"symbol": "ƒ", "name": "Netherlands Antillean Guilder"},
    "AOA": {"symbol": "Kz", "name": "Angolan Kwanza"},
    "ARS": {"symbol": "$", "name": "Argentine Peso"},
    "AUD": {"symbol": "A$", "name": "Australian Dollar"},
    "AWG": {"symbol": "ƒ", "name": "Aruban Florin"},
    "AZN": {"symbol": "₼", "name": "Azerbaijani Manat"},
    "BAM": {"symbol": "KM", "name": "Bosnia-Herzegovina Convertible Mark"},
    "BBD": {"symbol": "Bds$", "name": "Barbadian Dollar"},
    "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
    "BGN": {"symbol": "лв", "name": "Bulgarian Lev"},
    "BHD": {"symbol": ".د.ب", "name": "Bahraini Dinar"},
    "BIF": {"symbol": "FBu", "name": "Burundian Franc"},
    "BMD": {"symbol": "$", "name": "Bermudian Dollar"},
    "BND": {"symbol": "B$", "name": "Brunei Dollar"},
    "BOB": {"symbol": "Bs.", "name": "Bolivian Boliviano"},
    "BRL": {"symbol": "R$", "name": "Brazilian Real"},
    "BSD": {"symbol": "$", "name": "Bahamian Dollar"},
    "BTN": {"symbol": "Nu.", "name": "Bhutanese Ngultrum"},
    "BWP": {"symbol": "P", "name": "Botswanan Pula"},
    "BYN": {"symbol": "Br", "name": "Belarusian Ruble"},
    "BZD": {"symbol": "BZ$", "name": "Belize Dollar"},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar"},
    "CDF": {"symbol": "FC", "name": "Congolese Franc"},
    "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
    "CLP": {"symbol": "$", "name": "Chilean Peso"},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan"},
    "COP": {"symbol": "$", "name": "Colombian Peso"},
    "CRC": {"symbol": "₡", "name": "Costa Rican Colón"},
    "CUP": {"symbol": "₱", "name": "Cuban Peso"},
    "CVE": {"symbol": "$", "name": "Cape Verdean Escudo"},
    "CZK": {"symbol": "Kč", "name": "Czech Koruna"},
    "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
    "DKK": {"symbol": "kr", "name": "Danish Krone"},
    "DOP": {"symbol": "RD$", "name": "Dominican Peso"},
    "DZD": {"symbol": "د.ج", "name": "Algerian Dinar"},
    "EGP": {"symbol": "E£", "name": "Egyptian Pound"},
    "ERN": {"symbol": "Nfk", "name": "Eritrean Nakfa"},
    "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "FJD": {"symbol": "FJ$", "name": "Fijian Dollar"},
    "FKP": {"symbol": "£", "name": "Falkland Islands Pound"},
    "GBP": {"symbol": "£", "name": "British Pound Sterling"},
    "GEL": {"symbol": "₾", "name": "Georgian Lari"},
    "GHS": {"symbol": "GH₵", "name": "Ghanaian Cedi"},
    "GIP": {"symbol": "£", "name": "Gibraltar Pound"},
    "GMD": {"symbol": "D", "name": "Gambian Dalasi"},
    "GNF": {"symbol": "FG", "name": "Guinean Franc"},
    "GTQ": {"symbol": "Q", "name": "Guatemalan Quetzal"},
    "GYD": {"symbol": "GY$", "name": "Guyanaese Dollar"},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar"},
    "HNL": {"symbol": "L", "name": "Honduran Lempira"},
    "HRK": {"symbol": "kn", "name": "Croatian Kuna"},
    "HTG": {"symbol": "G", "name": "Haitian Gourde"},
    "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
    "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah"},
    "ILS": {"symbol": "₪", "name": "Israeli New Shekel"},
    "INR": {"symbol": "₹", "name": "Indian Rupee"},
    "IQD": {"symbol": "ع.د", "name": "Iraqi Dinar"},
    "IRR": {"symbol": "﷼", "name": "Iranian Rial"},
    "ISK": {"symbol": "kr", "name": "Icelandic Króna"},
    "JMD": {"symbol": "J$", "name": "Jamaican Dollar"},
    "JOD": {"symbol": "JD", "name": "Jordanian Dinar"},
    "JPY": {"symbol": "¥", "name": "Japanese Yen"},
    "KES": {"symbol": "KSh", "name": "Kenyan Shilling"},
    "KGS": {"symbol": "лв", "name": "Kyrgystani Som"},
    "KHR": {"symbol": "៛", "name": "Cambodian Riel"},
    "KMF": {"symbol": "CF", "name": "Comorian Franc"},
    "KPW": {"symbol": "₩", "name": "North Korean Won"},
    "KRW": {"symbol": "₩", "name": "South Korean Won"},
    "KWD": {"symbol": "د.ك", "name": "Kuwaiti Dinar"},
    "KYD": {"symbol": "CI$", "name": "Cayman Islands Dollar"},
    "KZT": {"symbol": "₸", "name": "Kazakhstani Tenge"},
    "LAK": {"symbol": "₭", "name": "Laotian Kip"},
    "LBP": {"symbol": "L£", "name": "Lebanese Pound"},
    "LKR": {"symbol": "Rs", "name": "Sri Lankan Rupee"},
    "LRD": {"symbol": "L$", "name": "Liberian Dollar"},
    "LSL": {"symbol": "L", "name": "Lesotho Loti"},
    "LYD": {"symbol": "ل.د", "name": "Libyan Dinar"},
    "MAD": {"symbol": "MAD", "name": "Moroccan Dirham"},
    "MDL": {"symbol": "L", "name": "Moldovan Leu"},
    "MGA": {"symbol": "Ar", "name": "Malagasy Ariary"},
    "MKD": {"symbol": "ден", "name": "Macedonian Denar"},
    "MMK": {"symbol": "K", "name": "Myanmar Kyat"},
    "MNT": {"symbol": "₮", "name": "Mongolian Tugrik"},
    "MOP": {"symbol": "MOP$", "name": "Macanese Pataca"},
    "MRU": {"symbol": "UM", "name": "Mauritanian Ouguiya"},
    "MUR": {"symbol": "₨", "name": "Mauritian Rupee"},
    "MVR": {"symbol": "Rf", "name": "Maldivian Rufiyaa"},
    "MWK": {"symbol": "MK", "name": "Malawian Kwacha"},
    "MXN": {"symbol": "Mex$", "name": "Mexican Peso"},
    "MYR": {"symbol": "RM", "name": "Malaysian Ringgit"},
    "MZN": {"symbol": "MT", "name": "Mozambican Metical"},
    "NAD": {"symbol": "N$", "name": "Namibian Dollar"},
    "NGN": {"symbol": "₦", "name": "Nigerian Naira"},
    "NIO": {"symbol": "C$", "name": "Nicaraguan Córdoba"},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
    "NPR": {"symbol": "₨", "name": "Nepalese Rupee"},
    "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar"},
    "OMR": {"symbol": "ر.ع.", "name": "Omani Rial"},
    "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
    "PEN": {"symbol": "S/.", "name": "Peruvian Sol"},
    "PGK": {"symbol": "K", "name": "Papua New Guinean Kina"},
    "PHP": {"symbol": "₱", "name": "Philippine Peso"},
    "PKR": {"symbol": "₨", "name": "Pakistani Rupee"},
    "PLN": {"symbol": "zł", "name": "Polish Zloty"},
    "PYG": {"symbol": "₲", "name": "Paraguayan Guarani"},
    "QAR": {"symbol": "ر.ق", "name": "Qatari Rial"},
    "RON": {"symbol": "lei", "name": "Romanian Leu"},
    "RSD": {"symbol": "din.", "name": "Serbian Dinar"},
    "RUB": {"symbol": "₽", "name": "Russian Ruble"},
    "RWF": {"symbol": "RF", "name": "Rwandan Franc"},
    "SAR": {"symbol": "ر.س", "name": "Saudi Riyal"},
    "SBD": {"symbol": "SI$", "name": "Solomon Islands Dollar"},
    "SCR": {"symbol": "₨", "name": "Seychellois Rupee"},
    "SDG": {"symbol": "ج.س.", "name": "Sudanese Pound"},
    "SEK": {"symbol": "kr", "name": "Swedish Krona"},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar"},
    "SHP": {"symbol": "£", "name": "Saint Helena Pound"},
    "SLE": {"symbol": "Le", "name": "Sierra Leonean Leone"},
    "SOS": {"symbol": "Sh", "name": "Somali Shilling"},
    "SRD": {"symbol": "Sr$", "name": "Surinamese Dollar"},
    "SSP": {"symbol": "£", "name": "South Sudanese Pound"},
    "STN": {"symbol": "Db", "name": "São Tomé and Príncipe Dobra"},
    "SYP": {"symbol": "£S", "name": "Syrian Pound"},
    "SZL": {"symbol": "E", "name": "Swazi Lilangeni"},
    "THB": {"symbol": "฿", "name": "Thai Baht"},
    "TJS": {"symbol": "SM", "name": "Tajikistani Somoni"},
    "TMT": {"symbol": "T", "name": "Turkmenistani Manat"},
    "TND": {"symbol": "د.ت", "name": "Tunisian Dinar"},
    "TOP": {"symbol": "T$", "name": "Tongan Paʻanga"},
    "TRY": {"symbol": "₺", "name": "Turkish Lira"},
    "TTD": {"symbol": "TT$", "name": "Trinidad & Tobago Dollar"},
    "TWD": {"symbol": "NT$", "name": "New Taiwan Dollar"},
    "TZS": {"symbol": "TSh", "name": "Tanzanian Shilling"},
    "UAH": {"symbol": "₴", "name": "Ukrainian Hryvnia"},
    "UGX": {"symbol": "USh", "name": "Ugandan Shilling"},
    "USD": {"symbol": "$", "name": "US Dollar"},
    "UYU": {"symbol": "$U", "name": "Uruguayan Peso"},
    "UZS": {"symbol": "soʻm", "name": "Uzbekistani Som"},
    "VES": {"symbol": "Bs.S", "name": "Venezuelan Bolívar Soberano"},
    "VND": {"symbol": "₫", "name": "Vietnamese Dong"},
    "VUV": {"symbol": "VT", "name": "Vanuatu Vatu"},
    "WST": {"symbol": "WS$", "name": "Samoan Tala"},
    "XAF": {"symbol": "FCFA", "name": "Central African CFA Franc"},
    "XCD": {"symbol": "EC$", "name": "East Caribbean Dollar"},
    "XOF": {"symbol": "CFA", "name": "West African CFA Franc"},
    "XPF": {"symbol": "₣", "name": "CFP Franc"},
    "YER": {"symbol": "﷼", "name": "Yemeni Rial"},
    "ZAR": {"symbol": "R", "name": "South African Rand"},
    "ZMW": {"symbol": "ZK", "name": "Zambian Kwacha"},
    "ZWL": {"symbol": "Z$", "name": "Zimbabwean Dollar"},
}


def get_vendor_currency(vendor_id):
    try:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT currency_symbol FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result and result[0] else '₹'
    except Exception:
        return '₹'


def get_vendor_id_from_email(email):
    try:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def geocode_location(query):
    import urllib.request
    import urllib.parse
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "FurrButler/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", query)
    except Exception:
        pass
    return None, None, None


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
        pass

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN booking_radius_km REAL DEFAULT 10.0")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE vendors ADD COLUMN delivery_radius_km REAL DEFAULT 5.0")
    except sqlite3.OperationalError:
        pass

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
        pass

    try:
        c.execute("ALTER TABLE ledger_entries ADD COLUMN entry_source TEXT DEFAULT 'auto'")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE expenses ADD COLUMN receipt_url TEXT")
    except sqlite3.OperationalError:
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            category TEXT,
            monthly_budget REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS fixed_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            asset_name TEXT,
            purchase_value REAL,
            current_value REAL,
            purchase_date TEXT,
            asset_type TEXT,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS capital_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            entry_type TEXT,
            amount REAL,
            description TEXT,
            entry_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS payable_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            payee_name TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            amount_paid REAL DEFAULT 0,
            balance_due REAL,
            due_date TEXT,
            category TEXT,
            status TEXT DEFAULT 'unpaid'
                CHECK(status IN ('unpaid','partial','paid')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS receivable_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            payer_name TEXT,
            payer_email TEXT,
            description TEXT,
            amount REAL NOT NULL,
            amount_received REAL DEFAULT 0,
            balance_due REAL,
            due_date TEXT,
            status TEXT DEFAULT 'unpaid'
                CHECK(status IN ('unpaid','partial','paid')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            entry_type TEXT CHECK(entry_type IN ('payable','receivable')),
            entry_id INTEGER,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL
                CHECK(payment_method IN ('Cash','Bank Transfer','UPI','Cheque','Card','Credit Note','Other')),
            payment_date TEXT NOT NULL,
            reference_number TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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
        CREATE TABLE IF NOT EXISTS restock_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            product_id INTEGER,
            quantity_added INTEGER,
            unit_cost REAL,
            barcode TEXT,
            entry_method TEXT,
            restock_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
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

    c.execute("PRAGMA table_info(settings_vendor)")
    sv_columns = [col[1] for col in c.fetchall()]
    if 'standard_delivery_price' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN standard_delivery_price REAL DEFAULT 2.99")
    if 'express_delivery_price' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN express_delivery_price REAL DEFAULT 5.99")
    if 'same_day_delivery_price' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN same_day_delivery_price REAL DEFAULT 12.99")
    if 'free_delivery_threshold' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN free_delivery_threshold REAL DEFAULT 50.00")
    if 'currency' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN currency TEXT DEFAULT 'INR'")
    if 'currency_symbol' not in sv_columns:
        c.execute("ALTER TABLE settings_vendor ADD COLUMN currency_symbol TEXT DEFAULT '₹'")

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

    try:
        c.execute("ALTER TABLE crm_customers ADD COLUMN marketing_opt_out INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

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

    # Research Database Tables for Government and Research Purposes
    c.execute('''
        CREATE TABLE IF NOT EXISTS research_pet_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            research_id TEXT UNIQUE NOT NULL,
            anonymized_pet_data TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age_group TEXT,
            health_conditions TEXT,
            vaccination_history TEXT,
            travel_history TEXT,
            geographic_region TEXT,
            registration_source TEXT,
            data_collection_date TEXT DEFAULT CURRENT_TIMESTAMP,
            consent_given BOOLEAN DEFAULT 0,
            research_purpose TEXT,
            data_retention_period INTEGER DEFAULT 2555, -- 7 years in days
            anonymization_level TEXT DEFAULT 'high'
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS research_health_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_category TEXT NOT NULL,
            species TEXT NOT NULL,
            geographic_region TEXT,
            time_period TEXT NOT NULL,
            health_condition TEXT,
            frequency_count INTEGER DEFAULT 0,
            percentage_affected REAL DEFAULT 0.0,
            severity_level TEXT,
            vaccination_correlation TEXT,
            environmental_factors TEXT,
            calculated_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS research_vaccination_efficacy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vaccine_name TEXT NOT NULL,
            species TEXT NOT NULL,
            batch_number TEXT,
            manufacturer TEXT,
            administration_date TEXT,
            geographic_region TEXT,
            efficacy_rate REAL DEFAULT 0.0,
            adverse_reactions_count INTEGER DEFAULT 0,
            follow_up_period INTEGER DEFAULT 365,
            breakthrough_infections INTEGER DEFAULT 0,
            study_period_start TEXT,
            study_period_end TEXT,
            sample_size INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS research_travel_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_country TEXT NOT NULL,
            destination_country TEXT NOT NULL,
            species TEXT NOT NULL,
            travel_month INTEGER,
            travel_year INTEGER,
            quarantine_duration INTEGER DEFAULT 0,
            health_complications BOOLEAN DEFAULT 0,
            documentation_issues BOOLEAN DEFAULT 0,
            travel_cost_range TEXT,
            success_rate REAL DEFAULT 100.0,
            common_delays TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS government_compliance_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            reporting_period TEXT NOT NULL,
            total_pets_registered INTEGER DEFAULT 0,
            total_vaccinations INTEGER DEFAULT 0,
            disease_outbreaks INTEGER DEFAULT 0,
            quarantine_violations INTEGER DEFAULT 0,
            documentation_compliance_rate REAL DEFAULT 100.0,
            cross_border_movements INTEGER DEFAULT 0,
            health_certificate_issues INTEGER DEFAULT 0,
            regulatory_changes TEXT,
            submitted_to_authority TEXT,
            submission_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS research_data_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_organization TEXT NOT NULL,
            requester_contact TEXT NOT NULL,
            research_purpose TEXT NOT NULL,
            data_fields_requested TEXT NOT NULL,
            ethical_approval_number TEXT,
            request_date TEXT DEFAULT CURRENT_TIMESTAMP,
            approval_status TEXT DEFAULT 'pending',
            approved_by TEXT,
            approval_date TEXT,
            data_access_period INTEGER DEFAULT 90,
            anonymization_required BOOLEAN DEFAULT 1,
            data_sharing_agreement TEXT
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

    # Add employee_id column to bookings table
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN employee_id INTEGER REFERENCES employees(id)")
    except:
        pass

    # Add rating/certification columns to employees table
    for col_sql in [
        "ALTER TABLE employees ADD COLUMN avg_overall_rating REAL DEFAULT 0",
        "ALTER TABLE employees ADD COLUMN total_reviews INTEGER DEFAULT 0",
        "ALTER TABLE employees ADD COLUMN is_certified BOOLEAN DEFAULT 0",
        "ALTER TABLE employees ADD COLUMN is_groomer_of_month BOOLEAN DEFAULT 0",
    ]:
        try:
            c.execute(col_sql)
        except:
            pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            reviewer_email TEXT NOT NULL,
            overall_rating INTEGER CHECK(overall_rating >= 1 AND overall_rating <= 5),
            service_quality INTEGER CHECK(service_quality >= 1 AND service_quality <= 5),
            punctuality INTEGER CHECK(punctuality >= 1 AND punctuality <= 5),
            handling_of_pet INTEGER CHECK(handling_of_pet >= 1 AND handling_of_pet <= 5),
            review_text TEXT,
            would_book_again BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS certified_groomers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER UNIQUE NOT NULL,
            certified_date TEXT,
            is_active BOOLEAN DEFAULT 1,
            suspended_date TEXT,
            suspension_reason TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS groomer_of_month (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            total_reviews INTEGER,
            avg_rating REAL,
            would_book_again_pct REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

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

def init_furrvet_gdpr_table():
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS furrvet_gdpr_consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vet_id INTEGER,
            medical_processing_consent BOOLEAN,
            retention_acknowledged BOOLEAN,
            referral_sharing_consent BOOLEAN,
            research_consent BOOLEAN,
            consent_date TEXT,
            consent_version TEXT DEFAULT '1.0',
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Run the DB setup on startup
init_erp_db()
init_furrvet_db()
init_furrvet_gdpr_table()

app = Flask(__name__)
app.secret_key = 'furrbutler_secret_key'
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'furrbutler_jwt_secret_change_in_prod')
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup error handlers
setup_error_handlers(app)

# Register i18n functions with Jinja2
def get_portal_dashboard():
    if session.get('vendor'):
        return '/erp/dashboard'
    elif session.get('furrvet_vet_id'):
        return '/furrvet/dashboard'
    elif session.get('vet'):
        return '/vet/dashboard'
    elif session.get('handler'):
        return '/handler/dashboard'
    elif session.get('ngo'):
        return '/ngo/dashboard'
    elif session.get('master_admin'):
        return '/master/admin/dashboard'
    elif session.get('user'):
        return '/dashboard'
    else:
        return '/dashboard'

app.jinja_env.globals.update(
    t=t,
    get_supported_languages=get_supported_languages,
    get_current_language=get_current_language,
    datetime=datetime,
    get_vendor_currency=get_vendor_currency,
    get_vendor_id_from_email=get_vendor_id_from_email,
    get_portal_dashboard=get_portal_dashboard
)

@app.context_processor
def inject_vendor_currency():
    now_date = datetime.now().strftime("%Y-%m-%d")
    if 'vendor' in session:
        vid = get_vendor_id_from_email(session['vendor'])
        if vid:
            return {'vendor_currency': get_vendor_currency(vid), 'vendor_id': vid, 'now_date': now_date}
    return {'vendor_currency': '₹', 'now_date': now_date}

# Register JSON filter for templates
import json
app.jinja_env.filters['tojson'] = lambda obj: json.dumps(obj)

# Register WhatsApp blueprint
app.register_blueprint(whatsapp_bp)

# FurrVet ERP Integration (duplicate function definition removed)
# FurrVet authentication decorator
def furrvet_login_required(f):
    def decorated_function(*args, **kwargs):
        if 'furrvet_vet_id' not in session:
            return redirect(url_for('furrvet_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# React Native Web App
@app.route('/app')
def react_app():
    dist_path = os.path.join(
        os.path.dirname(__file__),
        'mobile', 'dist')
    return send_from_directory(dist_path, 'index.html')

@app.route('/_expo/<path:path>')
def react_static_expo(path):
    dist_path = os.path.join(
        os.path.dirname(__file__),
        'mobile', 'dist', '_expo')
    return send_from_directory(dist_path, path)

@app.route('/assets/<path:path>')
def react_static_assets(path):
    dist_path = os.path.join(
        os.path.dirname(__file__),
        'mobile', 'dist', 'assets')
    return send_from_directory(dist_path, path)

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
        password = request.form.get("password")
        gdpr_consent = request.form.get("gdpr_consent")

        if not email or not password:
            return "Please enter both email and password."

        if not gdpr_consent:
            return "You must agree to the Privacy Policy and Terms of Service to register."

        if f"user:{email}" in db:
            return "User already exists. Try logging in."

        db[f"user:{email}"] = {
            "email": email,
            "password": password,
            "gdpr_consents": {
                "privacy_policy": {"accepted": True, "timestamp": datetime.now().isoformat(), "version": "1.0"},
                "terms_of_service": {"accepted": True, "timestamp": datetime.now().isoformat(), "version": "1.0"}
            }
        }

        return redirect(url_for("login"))
    return render_template("register_new.html")

# Login
@app.route('/login', methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    if session.get("vendor"):
        return redirect(url_for("erp_dashboard"))
    if session.get("furrvet_vet_id"):
        return redirect(url_for("furrvet_dashboard"))
    if session.get("vet"):
        return redirect(url_for("vet_dashboard"))
    if session.get("handler"):
        return redirect(url_for("handler_dashboard"))
    if session.get("ngo"):
        return redirect(url_for("ngo_dashboard"))
    if session.get("isolation"):
        return redirect(url_for("isolation_dashboard"))
    if session.get("master_admin"):
        return redirect(url_for("master_admin_dashboard"))

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

        gdpr_consent = request.form.get("gdpr_consent")

        if not email or not password or not name or not category:
            return "Missing required fields."

        if not gdpr_consent:
            return "You must agree to the Privacy Policy and Terms of Service to register."

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
@app.route('/groomers')
@app.route('/services/groomers')
def groomers():
    if "user" not in session:
        return redirect(url_for("login"))

    search_lat = None
    search_lon = None
    location_name = None

    location_query = request.args.get("location") or request.args.get("city")
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query
    elif session.get("location"):
        loc = session["location"]
        search_lat = loc.get("lat")
        search_lon = loc.get("lon")
        location_name = loc.get("name", "Your location")

    vendors = []
    if search_lat is not None and search_lon is not None:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""
            SELECT id, name, email, password, category, city, phone, bio, image_url,
                   latitude, longitude, is_online, account_status, break_start_date,
                   break_end_date, break_reason, address, state, pincode, booking_radius_km
            FROM vendors
            WHERE (account_status IS NULL OR account_status = 'active')
        """)
        db_vendors = c.fetchall()
        conn.close()

        for vendor in db_vendors:
            v_lat = vendor[9]
            v_lon = vendor[10]
            if v_lat is None or v_lon is None:
                continue
            radius = vendor[19] or 10.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vendors.append({
                    "id": vendor[0],
                    "name": vendor[1],
                    "description": vendor[7] or "Professional pet grooming services.",
                    "image": vendor[8] or "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
                    "rating": 5,
                    "level": 10,
                    "xp": 1500,
                    "city": vendor[5] or "Unknown",
                    "latitude": v_lat,
                    "longitude": v_lon,
                    "is_online": vendor[11],
                    "address": vendor[16] or "",
                    "state": vendor[17] or "",
                    "pincode": vendor[18] or "",
                    "distance": round(dist, 1)
                })
        vendors.sort(key=lambda v: v["distance"])

    return render_template("groomers.html", vendors=vendors,
                           location_name=location_name,
                           has_searched=bool(location_query or session.get("location")))

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

        return render_template("vendor_profile.html", vendor=vendor, reviews=reviews, groomers=[])

    if request.method == "POST":
        # Handle review submission for database vendors
        user_email = session["user"]
        rating = int(request.form.get("rating", 5))
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

            groomers = []
            try:
                c2 = conn.cursor()
                c2.execute("""SELECT id, name, position, avg_overall_rating, total_reviews, is_certified, is_groomer_of_month
                    FROM employees WHERE vendor_id=? AND status='active' AND total_reviews > 0 ORDER BY avg_overall_rating DESC""", (vendor_id_db,))
                for g in c2.fetchall():
                    groomers.append({'id': g[0], 'name': g[1], 'position': g[2], 'avg_rating': g[3] or 0, 
                        'total_reviews': g[4] or 0, 'is_certified': g[5], 'is_groomer_of_month': g[6]})
            except:
                pass

            conn.close()
            return render_template("vendor_profile.html", vendor=vendor, reviews=reviews, groomers=groomers)
        else:
            conn.close()
            return render_template("vendor_placeholder.html", vendor_name="Unknown Vendor")
    except Exception as e:
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
        
        # Get microchip, vaccine and health cert status
        c.execute("""
            SELECT doc_type, filename, status, upload_time, is_signed, doc_hash, signature_timestamp
            FROM passport_documents 
            WHERE pet_id = ? AND doc_type IN ('microchip', 'vaccine', 'health_cert') AND uploaded_by_role = 'vet'
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
    
    if doc_type not in ['microchip', 'vaccine', 'health_cert']:
        flash("Vets can only upload microchip, vaccine, and health certificate documents")
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
    from datetime import date
    return render_template("handler_dashboard.html", pets=pets, handler_name=session["handler_name"], date=date)

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
    from datetime import date
    return render_template("isolation_dashboard.html", bookings=bookings, center_name=session["isolation_name"], date=date)

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

    flash(f"{media_type.title() if media_type else 'Media'} uploaded successfully!")
    return redirect(url_for("isolation_dashboard"))

@app.route('/furrwings/dashboard')
def furrwings_dashboard():
    """FurrWings organized dashboard with tabular data views"""
    if "user" not in session and "vendor" not in session and "vet" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get statistics
    c.execute("SELECT COUNT(*) FROM passport_documents")
    total_pets = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM passport_documents WHERE status = 'approved'")
    completed_passports = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM passport_documents WHERE status = 'pending'")
    pending_documents = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM pet_bookings WHERE status IN ('pending', 'approved', 'in_progress')")
    active_bookings = c.fetchone()[0] or 0

    stats = {
        'total_pets': total_pets,
        'completed_passports': completed_passports,
        'pending_documents': pending_documents,
        'active_bookings': active_bookings
    }

    # Get pets data (simulated - would come from actual pet registry)
    pets_data = [
        {
            'id': 1,
            'name': 'Luna',
            'species': 'Dog',
            'breed': 'Golden Retriever',
            'owner_name': 'John Smith',
            'passport_status': 'approved',
            'destination': 'USA',
            'created_at': '2024-01-15'
        },
        {
            'id': 2,
            'name': 'Max',
            'species': 'Cat',
            'breed': 'Persian',
            'owner_name': 'Sarah Johnson',
            'passport_status': 'pending',
            'destination': 'UK',
            'created_at': '2024-01-20'
        }
    ]

    # Get documents data
    c.execute("""
        SELECT pd.id, 'Pet ' || pd.pet_id as pet_name, pd.doc_type, pd.uploaded_by_role, 
               pd.status, pd.upload_time, pd.filename, NULL as expiry_date
        FROM passport_documents pd
        ORDER BY pd.upload_time DESC
        LIMIT 50
    """)
    documents_data = [
        {
            'id': row[0],
            'pet_name': row[1],
            'doc_type': row[2],
            'uploaded_by_role': row[3],
            'status': row[4],
            'upload_time': row[5],
            'filename': row[6],
            'expiry_date': row[7]
        } for row in c.fetchall()
    ]

    # Get bookings data (simulated)
    bookings_data = [
        {
            'id': 1,
            'pet_name': 'Luna',
            'service_type': 'vaccination',
            'provider_name': 'Dr. Sarah Vet',
            'appointment_date': '2024-02-01',
            'appointment_time': '10:00',
            'status': 'confirmed',
            'created_at': '2024-01-25'
        }
    ]

    # Get vets data
    c.execute("""
        SELECT v.id, v.name, v.license_number, v.clinic_name, v.city, v.is_active,
               COUNT(pd.id) as documents_signed
        FROM vets v
        LEFT JOIN passport_documents pd ON pd.vet_id = v.id
        GROUP BY v.id
        ORDER BY v.name
    """)
    vets_data = [
        {
            'id': row[0],
            'name': row[1],
            'license_number': row[2],
            'clinic_name': row[3],
            'city': row[4],
            'is_active': row[5],
            'documents_signed': row[6]
        } for row in c.fetchall()
    ]

    # Get handlers data
    c.execute("""
        SELECT h.id, h.name, h.company_name, h.license_number, h.city, h.is_active,
               COUNT(pd.id) as documents_processed
        FROM handlers h
        LEFT JOIN passport_documents pd ON pd.uploaded_by_role = 'handler'
        GROUP BY h.id
        ORDER BY h.name
    """)
    handlers_data = [
        {
            'id': row[0],
            'name': row[1],
            'company_name': row[2],
            'license_number': row[3],
            'city': row[4],
            'is_active': row[5],
            'documents_processed': row[6]
        } for row in c.fetchall()
    ]

    conn.close()

    return render_template('furrwings_dashboard.html',
                         stats=stats,
                         pets_data=pets_data,
                         documents_data=documents_data,
                         bookings_data=bookings_data,
                         vets_data=vets_data,
                         handlers_data=handlers_data)

@app.route('/research/dashboard')
def research_dashboard():
    """Research database dashboard for government and research purposes - ADMIN ONLY"""
    if "master_admin" not in session:
        return redirect(url_for("master_admin_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Collect anonymized pet data for research
    populate_research_data(c)

    # Get research statistics
    c.execute("SELECT COUNT(*) FROM research_pet_registry")
    total_research_records = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(DISTINCT species) FROM research_pet_registry")
    species_tracked = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(DISTINCT geographic_region) FROM research_pet_registry")
    regions_covered = c.fetchone()[0] or 0

    # Get health trends
    c.execute("""
        SELECT trend_category, species, health_condition, frequency_count, percentage_affected
        FROM research_health_trends
        ORDER BY frequency_count DESC
        LIMIT 10
    """)
    health_trends = c.fetchall()

    # Get vaccination efficacy data
    c.execute("""
        SELECT vaccine_name, species, efficacy_rate, adverse_reactions_count, sample_size
        FROM research_vaccination_efficacy
        ORDER BY sample_size DESC
        LIMIT 10
    """)
    vaccination_data = c.fetchall()

    # Auto-populate research data from system (anonymized)
    auto_populate_research_data(c)
    
    conn.close()

    return render_template('research_dashboard.html',
                         total_records=total_research_records,
                         species_tracked=species_tracked,
                         regions_covered=regions_covered,
                         health_trends=health_trends,
                         vaccination_data=vaccination_data)

def auto_populate_research_data(cursor):
    """Automatically populate research data from system activity"""
    import random
    
    # Count existing research records
    cursor.execute("SELECT COUNT(*) FROM research_pet_registry")
    existing_records = cursor.fetchone()[0] or 0
    
    # If we have less than 50 records, generate some demo data
    if existing_records < 50:
        species_data = [
            ('Dog', 'excellent', True, 'adult'),
            ('Cat', 'good', True, 'young'),
            ('Dog', 'fair', False, 'senior'),
            ('Cat', 'excellent', True, 'adult'),
            ('Bird', 'good', True, 'young')
        ]
        
        regions = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']
        
        for species, health, vaccinated, age in species_data:
            import hashlib
            research_id = hashlib.md5(f"auto_{species}_{random.randint(1000,9999)}".encode()).hexdigest()[:12]
            region = random.choice(regions)
            
            anonymized_data = {
                'species': species,
                'health_status': health,
                'vaccination_complete': vaccinated,
                'age_group': age
            }
            
            cursor.execute("""
                INSERT OR IGNORE INTO research_pet_registry 
                (research_id, anonymized_pet_data, species, age_group, geographic_region, 
                 registration_source, consent_given, data_collection_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (research_id, str(anonymized_data), species, age, region, 
                  'Auto_System', 1, datetime.now().strftime('%Y-%m-%d')))

def populate_research_data(cursor):
    """Populate research database with anonymized pet data - NO PERSONAL INFO"""
    import hashlib
    import random
    
    # Get anonymized pet data from various sources - NO PARENT INFO
    
    # From pet passport system (anonymized)
    cursor.execute("""
        SELECT COUNT(*) as pet_count, 'Passport System' as source
        FROM passport_documents 
        WHERE status = 'approved'
    """)
    passport_pets = cursor.fetchone()[0] or 0
    
    # Generate anonymized research entries
    species_list = ['Dog', 'Cat', 'Bird', 'Rabbit', 'Hamster']
    regions = ['North India', 'South India', 'West India', 'East India', 'Central India']
    
    for i in range(min(passport_pets, 100)):  # Limit to 100 entries for demo
        research_id = hashlib.md5(f"research_{i}_{random.randint(1000,9999)}".encode()).hexdigest()[:12]
        species = random.choice(species_list)
        region = random.choice(regions)
        
        # Create anonymized data with NO personal identifiers
        anonymized_data = {
            'species': species,
            'health_status': random.choice(['excellent', 'good', 'fair']),
            'vaccination_complete': random.choice([True, False]),
            'age_group': random.choice(['young', 'adult', 'senior'])
        }
        
        cursor.execute("""
            INSERT OR IGNORE INTO research_pet_registry 
            (research_id, anonymized_pet_data, species, age_group, geographic_region, 
             registration_source, consent_given, data_collection_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (research_id, str(anonymized_data), species, 
              anonymized_data['age_group'], region, 'FurrButler_System', 1, 
              datetime.now().strftime('%Y-%m-%d')))

def calculate_age_group(birthday):
    """Calculate age group from birthday"""
    from datetime import datetime, timedelta
    try:
        birth_date = datetime.strptime(birthday, '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365
        if age < 1:
            return 'Puppy/Kitten'
        elif age < 3:
            return 'Young'
        elif age < 8:
            return 'Adult'
        else:
            return 'Senior'
    except:
        return 'Unknown'

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
    if lat is not None and lon is not None:
        import urllib.request
        location_name = "Your location"
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "FurrButler/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                addr = data.get("address", {})
                location_name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or addr.get("county") or "Your location"
        except Exception:
            pass
        session["location"] = {"lat": lat, "lon": lon, "name": location_name}
    return '', 204

# Booking route for vendor services
@app.route('/vendor/<vendor_id>/book', methods=["GET", "POST"])
def book_vendor_service(vendor_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    
    # Get user's pets for selection
    pets = db.get(f"pets:{user_email}", [])

    # Handle demo vendor
    if vendor_id == "fluffy-paws":
        vendor_name = "Fluffy Paws Grooming"
        services = [
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
        ]

        if request.method == "POST":
            # Get booking data from checkout
            booking_data = request.get_json() if request.is_json else None
            
            if booking_data:
                # Process booking from checkout
                try:
                    conn = sqlite3.connect('erp.db')
                    c = conn.cursor()
                    
                    for booking in booking_data['bookings']:
                        pet = next((p for p in pets if p['name'] == booking['pet_name']), None)
                        if pet:
                            c.execute("""
                                INSERT INTO bookings (vendor_id, user_email, service, date, time, duration, status, pet_name, pet_parent_name, pet_parent_phone, status_details)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (0, user_email, booking['service'], booking['date'], booking['time'], 
                                  booking['duration'], "confirmed", pet['name'], pet.get('parent_name', ''), 
                                  pet.get('parent_phone', ''), booking.get('notes', '')))
                    
                    conn.commit()
                    conn.close()
                    
                    return {"success": True, "message": "Bookings confirmed successfully!"}
                    
                except Exception as e:
                    return {"success": False, "error": str(e)}, 400
            
            return {"success": False, "error": "Invalid booking data"}, 400

        return render_template("booking.html", vendor_name=vendor_name, services=services, vendor_id=vendor_id, pets=pets)

    # Handle database vendors
    try:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT id, name, category FROM vendors WHERE id = ?", (vendor_id,))
        vendor_data = c.fetchone()

        if vendor_data:
            vendor_name = vendor_data[1]
            category = vendor_data[2] or "General"
            
            # Get services from database
            c.execute("""
                SELECT service_name, description, price, duration_minutes, category
                FROM vendor_services 
                WHERE vendor_id = ? AND is_active = 1
                ORDER BY service_name
            """, (vendor_id,))
            
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
                if "groom" in category.lower():
                    services = [
                        {
                            "name": "Full Grooming",
                            "description": "Complete grooming package",
                            "duration": 90,
                            "price": 40.00,
                            "available_slots": ["09:00", "11:00", "14:00", "16:00"]
                        },
                        {
                            "name": "Basic Grooming",
                            "description": "Basic bath and brush",
                            "duration": 60,
                            "price": 25.00,
                            "available_slots": ["10:00", "12:00", "15:00"]
                        }
                    ]
                elif "boarding" in category.lower():
                    services = [
                        {
                            "name": "Overnight Boarding",
                            "description": "Safe overnight pet boarding",
                            "duration": 1440,  # 24 hours in minutes
                            "price": 35.00,
                            "available_slots": ["18:00"]
                        },
                        {
                            "name": "Day Care",
                            "description": "Day care services",
                            "duration": 480,  # 8 hours
                            "price": 20.00,
                            "available_slots": ["08:00", "09:00"]
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

            if request.method == "POST":
                # Handle checkout data
                booking_data = request.get_json() if request.is_json else None
                
                if booking_data:
                    # Process booking from checkout
                    try:
                        for booking in booking_data['bookings']:
                            pet = next((p for p in pets if p['name'] == booking['pet_name']), None)
                            if pet:
                                c.execute("""
                                    INSERT INTO bookings (vendor_id, user_email, service, date, time, duration, status, pet_name, pet_parent_name, pet_parent_phone, status_details)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (vendor_id, user_email, booking['service'], booking['date'], booking['time'], 
                                      booking['duration'], "confirmed", pet['name'], pet.get('parent_name', ''), 
                                      pet.get('parent_phone', ''), booking.get('notes', '')))
                        
                        conn.commit()
                        conn.close()
                        
                        return {"success": True, "message": "Bookings confirmed successfully!"}
                        
                    except Exception as e:
                        conn.close()
                        return {"success": False, "error": str(e)}, 400
                
                conn.close()
                return {"success": False, "error": "Invalid booking data"}, 400

            conn.close()
            return render_template("booking.html", vendor_name=vendor_name, services=services, vendor_id=vendor_id, pets=pets)
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
    rating = int(request.form.get("rating", 5))
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

@app.route('/erp-update-booking-status', methods=["POST"])
def erp_update_booking_status():
    """AJAX endpoint for updating booking status"""
    if "vendor" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    try:
        booking_id = request.form.get("booking_id")
        new_status = request.form.get("status")
        
        if not booking_id or not new_status:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        email = session["vendor"]
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
        vendor_result = c.fetchone()
        
        if not vendor_result:
            conn.close()
            return jsonify({"success": False, "message": "Vendor not found"}), 404

        vendor_id = vendor_result[0]

        # Update booking status
        c.execute("""
            UPDATE bookings 
            SET status = ?, status_details = ?
            WHERE id = ? AND vendor_id = ?
        """, (new_status, f"Status updated to {new_status}", booking_id, vendor_id))

        if c.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Booking not found or unauthorized"}), 404

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Booking status updated to {new_status}"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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
        SELECT b.id, b.service, b.date, b.time, b.duration, b.status, v.name as vendor_name, v.phone, 
               b.pet_name, b.pet_parent_name, b.pet_parent_phone, v.id as vendor_id,
               CASE 
                   WHEN b.vendor_id = 0 THEN 'Fluffy Paws Grooming'
                   ELSE v.name
               END as display_vendor_name,
               CASE 
                   WHEN b.vendor_id = 0 THEN '+91-9876543210'
                   ELSE v.phone
               END as display_phone
        FROM bookings b
        LEFT JOIN vendors v ON b.vendor_id = v.id
        WHERE b.user_email = ?
        ORDER BY b.date DESC, b.time DESC
    """, (user_email,))
    bookings_data = c.fetchall()

    # Process bookings to add estimated completion time
    bookings = []
    for booking in bookings_data:
        booking_dict = {
            'id': booking[0],
            'service': booking[1],
            'date': booking[2],
            'time': booking[3],
            'duration': booking[4] if booking[4] else 60,  # Default 60 minutes
            'status': booking[5],
            'vendor_name': booking[11],  # display_vendor_name
            'vendor_phone': booking[12],  # display_phone
            'pet_name': booking[8],
            'pet_parent_name': booking[9],
            'pet_parent_phone': booking[10],
            'vendor_id': booking[6] if booking[6] != 0 else 'fluffy-paws'
        }
        
        # Calculate estimated completion time
        if booking[3] and booking[4]:  # If time and duration exist
            try:
                from datetime import datetime, timedelta
                start_time = datetime.strptime(booking[3], "%H:%M")
                end_time = start_time + timedelta(minutes=booking[4])
                booking_dict['estimated_completion'] = end_time.strftime("%H:%M")
            except:
                booking_dict['estimated_completion'] = "TBD"
        else:
            booking_dict['estimated_completion'] = "TBD"
            
        bookings.append(booking_dict)

    conn.close()
    return render_template("my_bookings.html", bookings=bookings)

# Logout - only clear pet parent session keys
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---- MISSING NGO DASHBOARD ROUTES ----

@app.route('/ngo/manage-strays')
def ngo_manage_strays():
    """Manage all strays for NGO"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get all strays for this NGO
    c.execute("""
        SELECT id, stray_uid, photo_url, breed_type, gender, temperament, 
               current_status, verification_status, total_vaccinations, created_at,
               location_address
        FROM stray_dogs 
        WHERE ngo_id = ? 
        ORDER BY created_at DESC
    """, (ngo_id,))
    
    strays = c.fetchall()
    conn.close()
    
    return render_template("ngo_manage_strays.html", strays=strays)

@app.route('/ngo/expenses')
def ngo_expenses():
    """Track NGO expenses"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get all expenses for this NGO
    c.execute("""
        SELECT se.*, sd.stray_uid
        FROM stray_expenses se
        JOIN stray_dogs sd ON se.stray_id = sd.id
        WHERE se.ngo_id = ?
        ORDER BY se.expense_date DESC
    """, (ngo_id,))
    
    expenses = c.fetchall()
    
    # Get expense summary
    c.execute("""
        SELECT expense_type, SUM(amount) as total_amount, COUNT(*) as count
        FROM stray_expenses
        WHERE ngo_id = ? AND verification_status = 'approved'
        GROUP BY expense_type
    """, (ngo_id,))
    
    expense_summary = c.fetchall()
    
    conn.close()
    
    return render_template("ngo_expenses.html", expenses=expenses, expense_summary=expense_summary)

@app.route('/ngo/community-updates')
def ngo_community_updates():
    """Community updates for NGO"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get community updates for this NGO
    c.execute("""
        SELECT scu.*, sd.stray_uid
        FROM stray_community_updates scu
        JOIN stray_dogs sd ON scu.stray_id = sd.id
        WHERE scu.ngo_id = ?
        ORDER BY scu.created_at DESC
    """, (ngo_id,))
    
    updates = c.fetchall()
    conn.close()
    
    return render_template("ngo_community_updates.html", updates=updates)

@app.route('/ngo/reports')
def ngo_reports():
    """NGO reports and analytics"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    ngo_name = session["ngo_name"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get citizen reports for this NGO's strays
    c.execute("""
        SELECT cr.*, sd.stray_uid
        FROM citizen_reports cr
        JOIN stray_dogs sd ON cr.stray_id = sd.id
        WHERE sd.ngo_id = ?
        ORDER BY cr.created_at DESC
    """, (ngo_id,))
    
    citizen_reports = c.fetchall()
    
    # Get analytics data
    c.execute("""
        SELECT 
            COUNT(DISTINCT sd.id) as total_strays,
            COUNT(DISTINCT CASE WHEN sd.verification_status = 'verified' THEN sd.id END) as verified_strays,
            COUNT(DISTINCT sv.id) as total_vaccinations,
            COALESCE(SUM(se.amount), 0) as total_expenses
        FROM stray_dogs sd
        LEFT JOIN stray_vaccinations sv ON sd.id = sv.stray_id
        LEFT JOIN stray_expenses se ON sd.id = se.stray_id
        WHERE sd.ngo_id = ?
    """, (ngo_id,))
    
    analytics = c.fetchone()
    
    conn.close()
    
    return render_template("ngo_reports.html", 
                         citizen_reports=citizen_reports, 
                         analytics=analytics,
                         ngo_name=ngo_name)

@app.route('/ngo/stray/<int:stray_id>')
def ngo_stray_detail(stray_id):
    """View individual stray details for NGO"""
    if "ngo" not in session:
        return redirect(url_for("ngo_login"))

    ngo_id = session["ngo_id"]
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get stray details (verify NGO owns this stray)
    c.execute("""
        SELECT * FROM stray_dogs 
        WHERE id = ? AND ngo_id = ?
    """, (stray_id, ngo_id))
    
    stray = c.fetchone()
    if not stray:
        flash("Stray not found")
        return redirect(url_for("ngo_dashboard"))
    
    # Get vaccinations for this stray
    c.execute("""
        SELECT * FROM stray_vaccinations
        WHERE stray_id = ?
        ORDER BY vaccination_date DESC
    """, (stray_id,))
    vaccinations = c.fetchall()
    
    # Get expenses for this stray
    c.execute("""
        SELECT * FROM stray_expenses
        WHERE stray_id = ?
        ORDER BY expense_date DESC
    """, (stray_id,))
    expenses = c.fetchall()
    
    conn.close()
    
    return render_template("ngo_stray_detail.html", 
                         stray=stray, 
                         vaccinations=vaccinations, 
                         expenses=expenses)

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

@app.route('/api/citizen-report', methods=["POST"])
def submit_citizen_report():
    """API endpoint for citizens to report issues"""
    try:
        data = request.get_json()
        
        report_type = data.get("report_type")
        stray_uid = data.get("stray_uid")
        description = data.get("description")
        reporter_email = data.get("reporter_email")
        
        if not report_type or not description:
            return {"success": False, "error": "Missing required fields"}, 400
        
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        # Get stray ID from UID if provided
        stray_id = None
        if stray_uid:
            c.execute("SELECT id FROM stray_dogs WHERE stray_uid = ?", (stray_uid,))
            stray_result = c.fetchone()
            if stray_result:
                stray_id = stray_result[0]
        
        # Insert citizen report
        c.execute("""
            INSERT INTO citizen_reports 
            (stray_id, reporter_email, report_type, description, priority_level)
            VALUES (?, ?, ?, ?, ?)
        """, (stray_id, reporter_email, report_type, description, 
              'high' if report_type in ['suspicious_activity', 'false_information'] else 'medium'))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Report submitted successfully"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

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
        
        gdpr_consent = request.form.get("gdpr_consent")
        if not gdpr_consent:
            flash("You must agree to the Privacy Policy and Terms of Service to register.")
            return render_template("ngo_register.html")

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

@app.route('/ngo/logout')
def ngo_logout():
    """NGO logout"""
    session.pop("ngo", None)
    session.pop("ngo_id", None)
    session.pop("ngo_name", None)
    session.pop("ngo_type", None)
    session.pop("ngo_signature_key", None)
    flash("You have been logged out successfully")
    return redirect(url_for("ngo_login"))

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

# === FURRVET PATIENT MANAGEMENT ===
@app.route('/furrvet/patients')
def furrvet_patients():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    search = request.args.get('search', '')
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    if search:
        search_param = f'%{search}%'
        c.execute("""
            SELECT p.*, po.name as owner_name, po.phone as owner_phone
            FROM pets p
            JOIN pet_owners po ON p.owner_id = po.id
            WHERE p.name LIKE ? OR po.name LIKE ? OR p.microchip_id LIKE ?
            ORDER BY p.name
        """, (search_param, search_param, search_param))
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

@app.route('/furrvet/patients/<int:pet_id>')
def furrvet_patient_detail(pet_id):
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

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
        return redirect(url_for('furrvet_patients'))
    
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
    
    return render_template('furrvet/furrvet_patient_detail.html',
                         pet=pet,
                         medical_records=medical_records,
                         vaccinations=vaccinations,
                         upcoming_appointments=upcoming_appointments)

# === FURRVET APPOINTMENT MANAGEMENT ===
@app.route('/furrvet/appointments')
def furrvet_appointments():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    vet_id = session['furrvet_vet_id']
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
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

@app.route('/furrvet/appointments/new', methods=["GET", "POST"])
def furrvet_new_appointment():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    if request.method == "POST":
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
        return redirect(url_for('furrvet_appointments'))
    
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
    
    return render_template('furrvet/furrvet_new_appointment.html', pets=pets)

# === FURRVET BILLING & INVOICING ===
@app.route('/furrvet/billing')
def furrvet_billing():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT i.*, p.name as pet_name, po.name as owner_name
        FROM furrvet_invoices i
        JOIN pets p ON i.pet_id = p.id
        JOIN pet_owners po ON i.owner_id = po.id
        WHERE i.vet_id = ?
        ORDER BY i.invoice_date DESC
        LIMIT 50
    """, (vet_id,))
    
    invoices = c.fetchall()
    conn.close()
    
    return render_template('furrvet/furrvet_billing.html', invoices=invoices)

# === FURRVET INVENTORY MANAGEMENT ===
@app.route('/furrvet/inventory')
def furrvet_inventory():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Get low stock items
    c.execute("SELECT * FROM furrvet_inventory WHERE current_stock <= minimum_stock ORDER BY current_stock")
    low_stock_items = c.fetchall()
    
    # Get all inventory
    c.execute("SELECT * FROM furrvet_inventory ORDER BY item_name")
    all_items = c.fetchall()
    
    conn.close()
    
    return render_template('furrvet/furrvet_inventory.html', 
                         low_stock_items=low_stock_items, 
                         all_items=all_items)

# === FURRVET MEDICAL RECORDS ===
@app.route('/furrvet/medical-records')
def furrvet_medical_records():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

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

# === FURRVET LABORATORY & IMAGING ===
@app.route('/furrvet/laboratory')
def furrvet_laboratory():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Mock lab tests data since tables don't exist yet
    lab_tests = []
    imaging_records = []
    
    conn.close()
    
    return render_template('furrvet/furrvet_laboratory.html', 
                         lab_tests=lab_tests, 
                         imaging_records=imaging_records)

# === FURRVET REPORTS & ANALYTICS ===
@app.route('/furrvet/reports')
def furrvet_reports():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Financial summary
    c.execute("""
        SELECT 
            COUNT(*) as total_invoices,
            SUM(CASE WHEN payment_status = 'paid' THEN total_amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN payment_status = 'pending' THEN total_amount ELSE 0 END) as pending_amount
        FROM furrvet_invoices 
        WHERE vet_id = ? AND invoice_date >= date('now', '-30 days')
    """, (vet_id,))
    financial_summary = c.fetchone()
    
    # Appointment statistics
    c.execute("""
        SELECT 
            COUNT(*) as total_appointments,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_appointments,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_appointments
        FROM appointments 
        WHERE vet_id = ? AND appointment_date >= date('now', '-30 days')
    """, (vet_id,))
    appointment_stats = c.fetchone()
    
    # Patient statistics
    c.execute("SELECT COUNT(*) FROM pets")
    total_patients = c.fetchone()[0]
    
    # Popular services
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

# === FURRVET HOSPITALIZATION ===
@app.route('/furrvet/hospitalization')
def furrvet_hospitalization():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))

    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    
    # Mock hospitalization data since table doesn't exist yet
    hospitalizations = []
    
    conn.close()
    
    return render_template('furrvet/furrvet_hospitalization.html', hospitalizations=hospitalizations)


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

@app.route('/vet/logout')
def vet_logout():
    session.pop("vet", None)
    session.pop("vet_id", None)
    session.pop("vet_name", None)
    session.pop("vet_license", None)
    return redirect(url_for("vet_login"))

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

@app.route('/handler/logout')
def handler_logout():
    session.pop("handler", None)
    session.pop("handler_id", None)
    session.pop("handler_name", None)
    session.pop("handler_license", None)
    return redirect(url_for("handler_login"))

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

@app.route('/isolation/logout')
def isolation_logout():
    session.pop("isolation", None)
    session.pop("isolation_id", None)
    session.pop("isolation_name", None)
    session.pop("isolation_license", None)
    flash("You have been logged out successfully")
    return redirect(url_for("isolation_login"))

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
    if session.get("vendor"):
        return redirect(url_for("erp_dashboard"))
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

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
    c.execute("SELECT id, name, email, phone, bio, image_url, city, latitude, longitude, category, account_status, break_start_date, break_reason, address, state, pincode, booking_radius_km, delivery_radius_km FROM vendors WHERE email=?", (email,))
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

        try:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None
        except (ValueError, TypeError):
            lat = lng = None

        try:
            booking_radius = float(request.form.get("booking_radius_km", 10.0))
            booking_radius = max(1, min(500, booking_radius))
        except (ValueError, TypeError):
            booking_radius = 10.0

        try:
            delivery_radius = float(request.form.get("delivery_radius_km", 5.0))
            delivery_radius = max(1, min(500, delivery_radius))
        except (ValueError, TypeError):
            delivery_radius = 5.0

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
            SET name=?, phone=?, bio=?, image_url=?, address=?, city=?, state=?, pincode=?, category=?, latitude=?, longitude=?, booking_radius_km=?, delivery_radius_km=?
            WHERE email=?
        ''', (name, phone, bio, image_url, address, city, state, pincode, category, lat, lng, booking_radius, delivery_radius, email))

        conn.commit()
        conn.close()
        return redirect(url_for("erp_profile"))

    c.execute("SELECT name, email, phone, bio, image_url, city, latitude, longitude, category, booking_radius_km, delivery_radius_km FROM vendors WHERE email=?", (email,))
    vendor = c.fetchone()
    conn.close()

    return render_template("erp_profiles.html", vendor=vendor or ("", email, "", "", "", "", "", "", "", 10.0, 5.0))

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
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    vendor_id = v[0] if v else 0
    c.execute("SELECT b.* FROM bookings b JOIN vendors v ON b.vendor_id = v.id WHERE v.email=?", (email,))
    bookings = c.fetchall()
    c.execute("SELECT id, name FROM employees WHERE vendor_id=? AND status='active' ORDER BY name", (vendor_id,))
    active_employees = c.fetchall()
    conn.close()

    return render_template("erp_booking.html", bookings=bookings, active_employees=active_employees)

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

@app.route('/erp/time-slots', methods=["GET", "POST"])
def manage_time_slots():
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
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_result[0]

    if request.method == "POST":
        opening_time = request.form.get("opening_time")
        closing_time = request.form.get("closing_time")
        slot_duration = int(request.form.get("slot_duration", 30))
        lunch_break_start = request.form.get("lunch_break_start")
        lunch_break_end = request.form.get("lunch_break_end")
        max_groomers = int(request.form.get("max_groomers", 1))
        days_of_week = ','.join(request.form.getlist("days_of_week"))

        # Insert or update time slot settings
        c.execute("""
            INSERT OR REPLACE INTO vendor_time_slots 
            (vendor_id, opening_time, closing_time, slot_duration, lunch_break_start, 
             lunch_break_end, max_groomers, days_of_week, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, opening_time, closing_time, slot_duration, lunch_break_start,
              lunch_break_end, max_groomers, days_of_week, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        flash("Time slot settings updated successfully!")
        return redirect(url_for("manage_time_slots"))

    # Get current time slot settings
    c.execute("SELECT * FROM vendor_time_slots WHERE vendor_id = ?", (vendor_id,))
    time_slot_settings = c.fetchone()

    # Get upcoming bookings with time slots
    c.execute("""
        SELECT date, time, service, pet_name, pet_parent_name, status
        FROM bookings 
        WHERE vendor_id = ? AND date >= date('now')
        ORDER BY date, time
    """, (vendor_id,))
    upcoming_bookings = c.fetchall()

    # Get employees for HR management
    c.execute("""
        SELECT id, name, email, phone, position, base_salary, hourly_rate, status, join_date
        FROM employees 
        WHERE vendor_id = ? AND status = 'active'
        ORDER BY name
    """, (vendor_id,))
    employees = c.fetchall()

    # Get HR metrics
    hr_metrics = get_hr_metrics(vendor_id, c)

    conn.close()
    return render_template("manage_time_slots.html", 
                         time_slot_settings=time_slot_settings,
                         upcoming_bookings=upcoming_bookings,
                         employees=employees,
                         hr_metrics=hr_metrics)

def get_hr_metrics(vendor_id, cursor):
    """Get HR metrics for dashboard"""
    # Total employees
    cursor.execute("SELECT COUNT(*) FROM employees WHERE vendor_id = ? AND status = 'active'", (vendor_id,))
    total_employees = cursor.fetchone()[0]
    
    # Hours today
    cursor.execute("""
        SELECT COALESCE(SUM(total_hours), 0) FROM employee_timesheets 
        WHERE vendor_id = ? AND work_date = date('now')
    """, (vendor_id,))
    hours_today = cursor.fetchone()[0]
    
    # Monthly payroll
    cursor.execute("""
        SELECT COALESCE(SUM(base_salary), 0) FROM employees 
        WHERE vendor_id = ? AND status = 'active'
    """, (vendor_id,))
    monthly_payroll = cursor.fetchone()[0]
    
    # Productivity score (mock calculation)
    productivity = 87  # This would be calculated based on actual metrics
    
    return {
        'total_employees': total_employees,
        'hours_today': hours_today,
        'monthly_payroll': monthly_payroll,
        'productivity': productivity
    }

@app.route('/erp/hr/employees', methods=["GET", "POST"])
@require_module('hr_management')
def manage_employees():
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
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_result[0]

    if request.method == "POST":
        # Add new employee
        name = request.form.get("name")
        email_emp = request.form.get("email")
        phone = request.form.get("phone")
        position = request.form.get("position")
        base_salary = float(request.form.get("salary", 0))
        hourly_rate = float(request.form.get("hourly_rate", 0))
        join_date = request.form.get("join_date")

        c.execute("""
            INSERT INTO employees 
            (vendor_id, name, email, phone, position, base_salary, hourly_rate, join_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, name, email_emp, phone, position, base_salary, hourly_rate, join_date))

        conn.commit()
        flash("Employee added successfully!")
        return redirect(url_for("manage_employees"))

    # Get all employees
    c.execute("""
        SELECT id, name, email, phone, position, base_salary, hourly_rate, status, join_date
        FROM employees 
        WHERE vendor_id = ?
        ORDER BY name
    """, (vendor_id,))
    employees = c.fetchall()

    conn.close()
    return redirect(url_for("manage_leaves"))

@app.route('/erp/hr/timesheets', methods=["GET", "POST"])
def manage_timesheets():
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
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_result[0]

    if request.method == "POST":
        # Handle timesheet updates
        employee_id = request.form.get("employee_id")
        work_date = request.form.get("work_date")
        check_in = request.form.get("check_in_time")
        check_out = request.form.get("check_out_time")
        
        # Calculate total hours
        if check_in and check_out:
            check_in_time = datetime.strptime(check_in, "%H:%M")
            check_out_time = datetime.strptime(check_out, "%H:%M")
            total_hours = (check_out_time - check_in_time).total_seconds() / 3600
            
            c.execute("""
                INSERT OR REPLACE INTO employee_timesheets 
                (employee_id, vendor_id, work_date, check_in_time, check_out_time, total_hours)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (employee_id, vendor_id, work_date, check_in, check_out, total_hours))
            
            conn.commit()
            flash("Timesheet updated successfully!")

    # Get timesheet data for today
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        SELECT e.name, e.position, ts.check_in_time, ts.check_out_time, 
               ts.total_hours, ts.status, e.hourly_rate, e.id
        FROM employees e
        LEFT JOIN employee_timesheets ts ON e.id = ts.employee_id AND ts.work_date = ?
        WHERE e.vendor_id = ? AND e.status = 'active'
        ORDER BY e.name
    """, (today, vendor_id))
    
    timesheets = c.fetchall()

    conn.close()
    return render_template("manage_timesheets.html", timesheets=timesheets, today=today)

@app.route('/erp/hr/payroll')
def manage_payroll():
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
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_result[0]

    # Get current month's payroll data
    current_month = datetime.now().strftime("%Y-%m")
    
    c.execute("""
        SELECT e.id, e.name, e.position, e.base_salary, e.hourly_rate,
               COALESCE(SUM(ts.total_hours), 0) as total_hours,
               COALESCE(SUM(ts.overtime_hours), 0) as overtime_hours
        FROM employees e
        LEFT JOIN employee_timesheets ts ON e.id = ts.employee_id 
            AND strftime('%Y-%m', ts.work_date) = ?
        WHERE e.vendor_id = ? AND e.status = 'active'
        GROUP BY e.id
        ORDER BY e.name
    """, (current_month, vendor_id))
    
    payroll_data = c.fetchall()

    # Calculate payroll summary
    total_base_salaries = sum([emp[3] for emp in payroll_data])
    total_overtime = sum([emp[6] * emp[4] * 1.5 for emp in payroll_data])  # 1.5x rate for overtime
    total_payroll = total_base_salaries + total_overtime

    payroll_summary = {
        'total_base_salaries': total_base_salaries,
        'total_overtime': total_overtime,
        'total_payroll': total_payroll
    }

    conn.close()
    return render_template("manage_payroll.html", 
                         payroll_data=payroll_data,
                         payroll_summary=payroll_summary,
                         current_month=current_month)

@app.route('/erp/hr/employees/<int:employee_id>')
def employee_detail(employee_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = vendor_result[0]
    c.execute("SELECT * FROM employees WHERE id=? AND vendor_id=?", (employee_id, vendor_id))
    emp = c.fetchone()
    if not emp:
        conn.close()
        flash("Employee not found")
        return redirect(url_for("manage_employees"))
    col_names = [desc[0] for desc in c.description]
    employee = dict(zip(col_names, emp))
    c.execute("""SELECT leave_type, SUM(days_count) as total FROM employee_leaves 
        WHERE employee_id=? AND status='approved' AND strftime('%Y', start_date)=strftime('%Y','now')
        GROUP BY leave_type""", (employee_id,))
    leave_balance = c.fetchall()
    c.execute("""SELECT work_date, check_in_time, check_out_time, total_hours, status 
        FROM employee_timesheets WHERE employee_id=? AND strftime('%Y-%m', work_date)=strftime('%Y-%m','now')
        ORDER BY work_date DESC""", (employee_id,))
    attendance = c.fetchall()
    c.execute("""SELECT performance_month, services_completed, revenue_generated, customer_rating, 
        attendance_rate, productivity_score, bonus_earned, feedback
        FROM employee_performance WHERE employee_id=? ORDER BY performance_month DESC LIMIT 3""", (employee_id,))
    performance = c.fetchall()
    c.execute("""SELECT COALESCE(AVG(overall_rating),0), COUNT(*) FROM employee_reviews WHERE employee_id=?""", (employee_id,))
    review_stats = c.fetchone()
    conn.close()
    return render_template("employee_detail.html", employee=employee, leave_balance=leave_balance,
        attendance=attendance, performance=performance, avg_rating=review_stats[0], total_reviews=review_stats[1])

@app.route('/erp/hr/employees/<int:employee_id>/edit', methods=["GET","POST"])
def employee_edit(employee_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = vendor_result[0]
    if request.method == "POST":
        c.execute("""UPDATE employees SET name=?, email=?, phone=?, position=?, base_salary=?, hourly_rate=?,
            join_date=?, emergency_contact=?, address=?, skills=?, certifications=?, updated_at=?
            WHERE id=? AND vendor_id=?""",
            (request.form.get("name"), request.form.get("email"), request.form.get("phone"),
             request.form.get("position"), float(request.form.get("base_salary",0)),
             float(request.form.get("hourly_rate",0)), request.form.get("join_date"),
             request.form.get("emergency_contact"), request.form.get("address"),
             request.form.get("skills"), request.form.get("certifications"),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), employee_id, vendor_id))
        conn.commit()
        conn.close()
        flash("Employee updated successfully!")
        return redirect(url_for("employee_detail", employee_id=employee_id))
    c.execute("SELECT * FROM employees WHERE id=? AND vendor_id=?", (employee_id, vendor_id))
    emp = c.fetchone()
    if not emp:
        conn.close()
        flash("Employee not found")
        return redirect(url_for("manage_employees"))
    col_names = [desc[0] for desc in c.description]
    employee = dict(zip(col_names, emp))
    conn.close()
    return render_template("employee_edit.html", employee=employee)

@app.route('/erp/hr/leaves', methods=["GET","POST"])
def manage_leaves():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = vendor_result[0]
    if request.method == "POST":
        emp_id = request.form.get("employee_id")
        c.execute("SELECT id FROM employees WHERE id=? AND vendor_id=?", (emp_id, vendor_id))
        if not c.fetchone():
            conn.close()
            flash("Invalid employee.")
            return redirect(url_for("manage_leaves"))
        leave_type = request.form.get("leave_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        reason = request.form.get("reason")
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            days_count = (d2 - d1).days + 1
        except (ValueError, TypeError):
            conn.close()
            flash("Invalid date format.")
            return redirect(url_for("manage_leaves"))
        c.execute("""INSERT INTO employee_leaves (employee_id, vendor_id, leave_type, start_date, end_date, days_count, reason)
            VALUES (?,?,?,?,?,?,?)""", (emp_id, vendor_id, leave_type, start_date, end_date, days_count, reason))
        conn.commit()
        flash("Leave request submitted!")
        return redirect(url_for("manage_leaves"))
    c.execute("SELECT id, name FROM employees WHERE vendor_id=? AND status='active' ORDER BY name", (vendor_id,))
    employees = c.fetchall()
    c.execute("""SELECT el.id, e.name, el.leave_type, el.start_date, el.end_date, el.days_count, el.reason, el.status
        FROM employee_leaves el JOIN employees e ON el.employee_id=e.id
        WHERE el.vendor_id=? AND el.status='pending' ORDER BY el.created_at DESC""", (vendor_id,))
    pending = c.fetchall()
    c.execute("""SELECT el.id, e.name, el.leave_type, el.start_date, el.end_date, el.days_count, el.reason, el.status, el.approval_date
        FROM employee_leaves el JOIN employees e ON el.employee_id=e.id
        WHERE el.vendor_id=? AND el.status!='pending' ORDER BY el.created_at DESC LIMIT 50""", (vendor_id,))
    history = c.fetchall()
    conn.close()
    return render_template("employee_leaves.html", employees=employees, pending=pending, history=history)

@app.route('/erp/hr/leaves/<int:leave_id>/approve', methods=["POST"])
def approve_leave(leave_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (session["vendor"],))
    v = c.fetchone()
    if v:
        c.execute("UPDATE employee_leaves SET status='approved', approval_date=? WHERE id=? AND vendor_id=?",
            (datetime.now().strftime("%Y-%m-%d"), leave_id, v[0]))
        conn.commit()
        flash("Leave approved!")
    conn.close()
    return redirect(url_for("manage_leaves"))

@app.route('/erp/hr/leaves/<int:leave_id>/reject', methods=["POST"])
def reject_leave(leave_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (session["vendor"],))
    v = c.fetchone()
    if v:
        c.execute("UPDATE employee_leaves SET status='rejected', approval_date=? WHERE id=? AND vendor_id=?",
            (datetime.now().strftime("%Y-%m-%d"), leave_id, v[0]))
        conn.commit()
        flash("Leave rejected.")
    conn.close()
    return redirect(url_for("manage_leaves"))

@app.route('/erp/hr/timesheets/save', methods=["POST"])
def save_timesheet():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    employee_id = request.form.get("employee_id")
    c.execute("SELECT id FROM employees WHERE id=? AND vendor_id=?", (employee_id, vendor_id))
    if not c.fetchone():
        conn.close()
        flash("Invalid employee.")
        return redirect(url_for("manage_timesheets"))
    work_date = request.form.get("work_date")
    check_in = request.form.get("check_in_time")
    check_out = request.form.get("check_out_time")
    total_hours = 0
    try:
        if check_in and check_out:
            ci = datetime.strptime(check_in, "%H:%M")
            co = datetime.strptime(check_out, "%H:%M")
            total_hours = round((co - ci).total_seconds() / 3600, 2)
    except ValueError:
        conn.close()
        flash("Invalid time format.")
        return redirect(url_for("manage_timesheets"))
    c.execute("""INSERT OR REPLACE INTO employee_timesheets 
        (employee_id, vendor_id, work_date, check_in_time, check_out_time, total_hours)
        VALUES (?,?,?,?,?,?)""", (employee_id, vendor_id, work_date, check_in, check_out, total_hours))
    conn.commit()
    conn.close()
    flash("Timesheet saved!")
    return redirect(url_for("manage_timesheets"))

@app.route('/erp/hr/timesheets/mark-attendance', methods=["POST"])
def mark_all_attendance():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")
    c.execute("SELECT id FROM employees WHERE vendor_id=? AND status='active'", (vendor_id,))
    emps = c.fetchall()
    for emp in emps:
        c.execute("SELECT id FROM employee_timesheets WHERE employee_id=? AND work_date=?", (emp[0], today))
        if not c.fetchone():
            c.execute("""INSERT INTO employee_timesheets (employee_id, vendor_id, work_date, check_in_time, status)
                VALUES (?,?,?,?,'present')""", (emp[0], vendor_id, today, now_time))
    conn.commit()
    conn.close()
    flash("Attendance marked for all employees!")
    return redirect(url_for("manage_timesheets"))

@app.route('/erp/hr/payroll/pay/<int:employee_id>', methods=["POST"])
def pay_employee(employee_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    month = request.form.get("month", datetime.now().strftime("%Y-%m"))
    bonus = float(request.form.get("bonus", 0))
    deductions = float(request.form.get("deductions", 0))
    c.execute("SELECT base_salary, hourly_rate FROM employees WHERE id=? AND vendor_id=?", (employee_id, vendor_id))
    emp = c.fetchone()
    if not emp:
        conn.close()
        flash("Employee not found")
        return redirect(url_for("manage_payroll"))
    base_salary = emp[0]
    c.execute("""SELECT COALESCE(SUM(overtime_hours),0) FROM employee_timesheets 
        WHERE employee_id=? AND strftime('%Y-%m', work_date)=?""", (employee_id, month))
    overtime = c.fetchone()[0]
    overtime_pay = overtime * emp[1] * 1.5
    total_pay = base_salary + overtime_pay + bonus - deductions
    pay_start = f"{month}-01"
    import calendar
    y, m = int(month.split('-')[0]), int(month.split('-')[1])
    pay_end = f"{month}-{calendar.monthrange(y, m)[1]}"
    c.execute("""INSERT INTO employee_payroll (employee_id, vendor_id, pay_period_start, pay_period_end,
        base_pay, overtime_pay, bonus, deductions, total_pay, payment_status, payment_date)
        VALUES (?,?,?,?,?,?,?,?,?,'paid',?)""",
        (employee_id, vendor_id, pay_start, pay_end, base_salary, overtime_pay, bonus, deductions, total_pay,
         datetime.now().strftime("%Y-%m-%d")))
    try:
        c.execute("""INSERT INTO general_ledger (vendor_id, date, account_name, account_type, debit, credit, description)
            VALUES (?,?,?,?,?,?,?)""", (vendor_id, datetime.now().strftime("%Y-%m-%d"), "Salaries Expense", "Expense", total_pay, 0, f"Salary payment for employee #{employee_id}"))
        c.execute("""INSERT INTO general_ledger (vendor_id, date, account_name, account_type, debit, credit, description)
            VALUES (?,?,?,?,?,?,?)""", (vendor_id, datetime.now().strftime("%Y-%m-%d"), "Cash/Bank", "Asset", 0, total_pay, f"Salary payment for employee #{employee_id}"))
    except:
        pass
    conn.commit()
    conn.close()
    flash("Employee paid successfully!")
    return redirect(url_for("manage_payroll"))

@app.route('/erp/hr/payroll/generate-payslips', methods=["POST"])
def generate_payslips():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    vendor_name = v[1]
    month = request.form.get("month", datetime.now().strftime("%Y-%m"))
    import calendar
    y, m_val = int(month.split('-')[0]), int(month.split('-')[1])
    pay_start = f"{month}-01"
    pay_end = f"{month}-{calendar.monthrange(y, m_val)[1]}"
    c.execute("""SELECT e.id, e.name, e.position, e.base_salary, e.hourly_rate,
        COALESCE(SUM(ts.overtime_hours),0) as ot_hours
        FROM employees e LEFT JOIN employee_timesheets ts ON e.id=ts.employee_id AND strftime('%Y-%m', ts.work_date)=?
        WHERE e.vendor_id=? AND e.status='active' GROUP BY e.id""", (month, vendor_id))
    employees = c.fetchall()
    payslips = []
    for emp in employees:
        ot_pay = emp[5] * emp[4] * 1.5
        c.execute("SELECT bonus, deductions FROM employee_payroll WHERE employee_id=? AND pay_period_start=? ORDER BY id DESC LIMIT 1",
            (emp[0], pay_start))
        existing = c.fetchone()
        bonus = existing[0] if existing else 0
        deductions = existing[1] if existing else 0
        total = emp[3] + ot_pay + bonus - deductions
        if not existing:
            c.execute("""INSERT INTO employee_payroll (employee_id, vendor_id, pay_period_start, pay_period_end,
                base_pay, overtime_pay, bonus, deductions, total_pay, payment_status)
                VALUES (?,?,?,?,?,?,?,?,?,'pending')""",
                (emp[0], vendor_id, pay_start, pay_end, emp[3], ot_pay, bonus, deductions, total))
        payslips.append({
            'name': emp[1], 'position': emp[2], 'base_salary': emp[3],
            'overtime_hours': emp[5], 'overtime_pay': ot_pay,
            'bonus': bonus, 'deductions': deductions, 'total_pay': total,
            'pay_period': f"{pay_start} to {pay_end}"
        })
    conn.commit()
    conn.close()
    return render_template("payslips.html", payslips=payslips, vendor_name=vendor_name, month=month)

@app.route('/erp/hr/performance/add', methods=["GET","POST"])
def add_performance_review():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    if request.method == "POST":
        emp_id = request.form.get("employee_id")
        c.execute("SELECT id FROM employees WHERE id=? AND vendor_id=?", (emp_id, vendor_id))
        if not c.fetchone():
            conn.close()
            flash("Invalid employee.")
            return redirect(url_for("add_performance_review"))
        perf_month = request.form.get("performance_month")
        try:
            services = int(request.form.get("services_completed", 0))
            revenue = float(request.form.get("revenue_generated", 0))
            rating = float(request.form.get("customer_rating", 0))
            attendance = float(request.form.get("attendance_rate", 0))
            bonus = float(request.form.get("bonus_earned", 0))
        except (ValueError, TypeError):
            conn.close()
            flash("Invalid numeric input.")
            return redirect(url_for("add_performance_review"))
        feedback = request.form.get("feedback", "")
        norm_services = min(services / 50 * 100, 100) if services > 0 else 0
        norm_revenue = min(revenue / 10000 * 100, 100) if revenue > 0 else 0
        norm_rating = rating * 20
        values = [norm_services, norm_revenue, norm_rating, attendance]
        productivity_score = round(sum(values) / len(values), 1)
        c.execute("""INSERT INTO employee_performance (employee_id, vendor_id, performance_month, services_completed,
            revenue_generated, customer_rating, attendance_rate, productivity_score, bonus_earned, feedback, review_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (emp_id, vendor_id, perf_month, services, revenue, rating, attendance, productivity_score, bonus, feedback,
             datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        flash("Performance review added!")
        return redirect(url_for("manage_time_slots"))
    c.execute("SELECT id, name FROM employees WHERE vendor_id=? AND status='active' ORDER BY name", (vendor_id,))
    employees = c.fetchall()
    conn.close()
    return render_template("performance_review_form.html", employees=employees)

def check_groomer_certification(employee_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT COALESCE(AVG(overall_rating),0), COUNT(*) FROM employee_reviews WHERE employee_id=?", (employee_id,))
    avg_rating, total = c.fetchone()
    if total < 50 or avg_rating < 4.8:
        conn.close()
        return False
    c.execute("SELECT COUNT(*) FROM employee_reviews WHERE employee_id=? AND would_book_again=1", (employee_id,))
    book_again = c.fetchone()[0]
    pct = (book_again / total * 100) if total > 0 else 0
    if pct < 85:
        conn.close()
        return False
    c.execute("SELECT join_date FROM employees WHERE id=?", (employee_id,))
    jd = c.fetchone()
    if jd and jd[0]:
        join_dt = datetime.strptime(jd[0], "%Y-%m-%d")
        if (datetime.now() - join_dt).days < 180:
            conn.close()
            return False
    conn.close()
    return True

def update_employee_review_stats(employee_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT COALESCE(AVG(overall_rating),0), COUNT(*) FROM employee_reviews WHERE employee_id=?", (employee_id,))
    avg_r, total_r = c.fetchone()
    is_cert = 1 if check_groomer_certification(employee_id) else 0
    c.execute("UPDATE employees SET avg_overall_rating=?, total_reviews=?, is_certified=? WHERE id=?",
        (round(avg_r, 2), total_r, is_cert, employee_id))
    if is_cert:
        c.execute("SELECT id FROM certified_groomers WHERE employee_id=?", (employee_id,))
        if not c.fetchone():
            c.execute("INSERT INTO certified_groomers (employee_id, certified_date, is_active) VALUES (?,?,1)",
                (employee_id, datetime.now().strftime("%Y-%m-%d")))
    else:
        c.execute("UPDATE certified_groomers SET is_active=0, suspended_date=? WHERE employee_id=? AND is_active=1",
            (datetime.now().strftime("%Y-%m-%d"), employee_id))
    conn.commit()
    conn.close()

def auto_crm_collection(vendor_id, booking):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    user_email = booking.get('user_email', '')
    pet_parent_name = booking.get('pet_parent_name', '')
    if not user_email:
        conn.close()
        return
    c.execute("SELECT id, total_orders FROM crm_customers WHERE vendor_id=? AND user_email=?", (vendor_id, user_email))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE crm_customers SET last_contact_date=?, total_orders=?, updated_at=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d"), existing[1]+1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), existing[0]))
    else:
        first_name = pet_parent_name.split()[0] if pet_parent_name else user_email.split('@')[0]
        c.execute("""INSERT INTO crm_customers (vendor_id, customer_type, user_email, first_name, customer_source, 
            lifecycle_stage, last_contact_date) VALUES (?,?,?,?,?,?,?)""",
            (vendor_id, 'online', user_email, first_name, 'booking', 'customer', datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

@app.route('/erp/bookings/done/<int:booking_id>', methods=["POST"])
def mark_booking_done(booking_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    vendor_name = v[1]
    c.execute("SELECT * FROM bookings WHERE id=? AND vendor_id=?", (booking_id, vendor_id))
    booking = c.fetchone()
    if not booking:
        conn.close()
        flash("Booking not found")
        return redirect(url_for("erp_bookings"))
    col_names = [desc[0] for desc in c.description]
    booking_dict = dict(zip(col_names, booking))
    c.execute("UPDATE bookings SET status='completed' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    try:
        customer_email = booking_dict.get('user_email', '')
        socketio.emit('booking_done', {
            'booking_id': booking_id,
            'message': f"Your pet is ready for pickup! {booking_dict.get('pet_name','')} has completed their {booking_dict.get('service','')} at {vendor_name}. Please come to collect them."
        }, room=customer_email)
        socketio.emit('review_prompt', {
            'booking_id': booking_id,
            'message': "How was your session? Rate your groomer!"
        }, room=customer_email)
    except:
        pass
    auto_crm_collection(vendor_id, booking_dict)
    flash("Booking marked as completed!")
    return redirect(url_for("erp_bookings"))

@app.route('/erp/bookings/extend/<int:booking_id>', methods=["POST"])
def extend_booking(booking_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    additional_time = int(request.form.get("additional_time", 30))
    c.execute("UPDATE bookings SET duration=COALESCE(duration,60)+? WHERE id=? AND vendor_id=?",
        (additional_time, booking_id, vendor_id))
    conn.commit()
    conn.close()
    try:
        note = request.form.get("note", "")
        conn2 = sqlite3.connect('erp.db')
        c2 = conn2.cursor()
        c2.execute("SELECT user_email FROM bookings WHERE id=?", (booking_id,))
        brow = c2.fetchone()
        conn2.close()
        customer_room = brow[0] if brow else ''
        socketio.emit('booking_extended', {
            'booking_id': booking_id,
            'message': f"Your booking has been extended by {additional_time} minutes. {note}"
        }, room=customer_room)
    except:
        pass
    flash("Booking extended!")
    return redirect(url_for("erp_bookings"))

@app.route('/erp/bookings/assign-staff/<int:booking_id>', methods=["POST"])
def assign_staff(booking_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    emp_id = request.form.get("employee_id")
    if emp_id:
        c.execute("SELECT id FROM employees WHERE id=? AND vendor_id=?", (emp_id, vendor_id))
        if not c.fetchone():
            conn.close()
            flash("Invalid employee.")
            return redirect(url_for("erp_bookings"))
    c.execute("UPDATE bookings SET employee_id=? WHERE id=? AND vendor_id=?", (emp_id, booking_id, vendor_id))
    conn.commit()
    conn.close()
    flash("Staff assigned!")
    return redirect(url_for("erp_bookings"))

@app.route('/booking/<int:booking_id>/review', methods=["GET","POST"])
def booking_review(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))
    user_email = session["user"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    booking = c.fetchone()
    if not booking:
        conn.close()
        flash("Booking not found")
        return redirect(url_for("my_bookings"))
    col_names = [desc[0] for desc in c.description]
    booking_dict = dict(zip(col_names, booking))
    if booking_dict.get('status') != 'completed':
        conn.close()
        flash("Reviews can only be submitted for completed bookings")
        return redirect(url_for("my_bookings"))
    if booking_dict.get('user_email') != user_email:
        conn.close()
        flash("You can only review your own bookings")
        return redirect(url_for("my_bookings"))
    c.execute("SELECT id FROM employee_reviews WHERE booking_id=?", (booking_id,))
    if c.fetchone():
        conn.close()
        flash("You have already reviewed this booking")
        return redirect(url_for("my_bookings"))
    if request.method == "POST":
        employee_id = booking_dict.get('employee_id')
        vendor_id = booking_dict.get('vendor_id')
        if not employee_id:
            conn.close()
            flash("No groomer was assigned to this booking")
            return redirect(url_for("my_bookings"))
        overall = int(request.form.get("overall_rating", 5))
        quality = int(request.form.get("service_quality", 5))
        punctuality = int(request.form.get("punctuality", 5))
        handling = int(request.form.get("handling_of_pet", 5))
        review_text = request.form.get("review_text", "")
        would_book = 1 if request.form.get("would_book_again") == "yes" else 0
        c.execute("""INSERT INTO employee_reviews (employee_id, booking_id, vendor_id, reviewer_email,
            overall_rating, service_quality, punctuality, handling_of_pet, review_text, would_book_again)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (employee_id, booking_id, vendor_id, user_email, overall, quality, punctuality, handling, review_text, would_book))
        try:
            c.execute("INSERT INTO reviews (vendor_id, user_email, rating, review_text, service_type) VALUES (?,?,?,?,?)",
                (vendor_id, user_email, overall, review_text, "Grooming"))
        except:
            pass
        conn.commit()
        conn.close()
        update_employee_review_stats(employee_id)
        flash("Thank you for your review!")
        return redirect(url_for("my_bookings"))
    conn.close()
    return render_template("booking_review.html", booking=booking_dict)

@app.route('/vendor/<int:vendor_id>/groomers')
def groomer_listing(vendor_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name, category, city FROM vendors WHERE id=?", (vendor_id,))
    vendor = c.fetchone()
    if not vendor:
        conn.close()
        return "Vendor not found", 404
    c.execute("""SELECT e.id, e.name, e.position, e.avg_overall_rating, e.total_reviews, e.is_certified, e.is_groomer_of_month,
        e.profile_image
        FROM employees e WHERE e.vendor_id=? AND e.status='active' ORDER BY e.avg_overall_rating DESC""", (vendor_id,))
    groomers_raw = c.fetchall()
    groomers = []
    for g in groomers_raw:
        c.execute("SELECT COALESCE(AVG(handling_of_pet),0) FROM employee_reviews WHERE employee_id=?", (g[0],))
        handling = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM employee_reviews WHERE employee_id=? AND would_book_again=1", (g[0],))
        book_again = c.fetchone()[0]
        pct = round(book_again / g[4] * 100, 1) if g[4] > 0 else 0
        c.execute("SELECT review_text FROM employee_reviews WHERE employee_id=? ORDER BY created_at DESC LIMIT 1", (g[0],))
        latest = c.fetchone()
        groomers.append({
            'id': g[0], 'name': g[1], 'position': g[2], 'avg_rating': g[3], 'total_reviews': g[4],
            'is_certified': g[5], 'is_groomer_of_month': g[6], 'handling_rating': round(handling, 1),
            'would_book_again_pct': pct, 'latest_review': latest[0] if latest else '',
            'profile_image': g[7]
        })
    conn.close()
    vendor_dict = {'id': vendor[0], 'name': vendor[1], 'category': vendor[2], 'city': vendor[3]}
    return render_template("groomer_listing.html", groomers=groomers, vendor=vendor_dict)

@app.route('/groomer/<int:employee_id>')
def groomer_profile(employee_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT e.*, v.name as vendor_name, v.city as vendor_city, v.id as vendor_id
        FROM employees e JOIN vendors v ON e.vendor_id=v.id WHERE e.id=?""", (employee_id,))
    emp = c.fetchone()
    if not emp:
        conn.close()
        return "Groomer not found", 404
    col_names = [desc[0] for desc in c.description]
    groomer = dict(zip(col_names, emp))
    c.execute("SELECT COALESCE(AVG(overall_rating),0), COALESCE(AVG(service_quality),0), COALESCE(AVG(punctuality),0), COALESCE(AVG(handling_of_pet),0), COUNT(*) FROM employee_reviews WHERE employee_id=?", (employee_id,))
    stats = c.fetchone()
    c.execute("SELECT COUNT(*) FROM employee_reviews WHERE employee_id=? AND would_book_again=1", (employee_id,))
    book_again = c.fetchone()[0]
    pct = round(book_again / stats[4] * 100, 1) if stats[4] > 0 else 0
    c.execute("SELECT overall_rating, review_text, created_at, would_book_again, reviewer_email FROM employee_reviews WHERE employee_id=? ORDER BY created_at DESC", (employee_id,))
    reviews = c.fetchall()
    c.execute("SELECT id FROM groomer_of_month WHERE employee_id=? AND month=?",
        (employee_id, datetime.now().strftime("%Y-%m")))
    is_gotm = c.fetchone() is not None
    conn.close()
    return render_template("groomer_profile.html", groomer=groomer, 
        avg_overall=round(stats[0],1), avg_quality=round(stats[1],1), avg_punctuality=round(stats[2],1),
        avg_handling=round(stats[3],1), total_reviews=stats[4], would_book_again_pct=pct,
        reviews=reviews, is_gotm=is_gotm)

@app.route('/erp/certifications/check', methods=["POST"])
def check_certification():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    employee_id = request.form.get("employee_id")
    if employee_id:
        c.execute("SELECT id FROM employees WHERE id=? AND vendor_id=?", (employee_id, vendor_id))
        if c.fetchone():
            update_employee_review_stats(int(employee_id))
            flash("Certification check completed!")
        else:
            flash("Invalid employee.")
    conn.close()
    return redirect(url_for("manage_time_slots"))

@app.route('/erp/hr/groomer-of-month/calculate', methods=["POST"])
def calculate_groomer_of_month():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    v = c.fetchone()
    if not v:
        conn.close()
        return redirect(url_for("erp_login"))
    vendor_id = v[0]
    current_month = datetime.now().strftime("%Y-%m")
    c.execute("UPDATE employees SET is_groomer_of_month=0 WHERE vendor_id=?", (vendor_id,))
    c.execute("""SELECT e.id, e.name, COUNT(er.id) as review_count, COALESCE(AVG(er.overall_rating),0) as avg_r
        FROM employees e LEFT JOIN employee_reviews er ON e.id=er.employee_id 
        AND strftime('%Y-%m', er.created_at)=?
        WHERE e.vendor_id=? AND e.status='active' GROUP BY e.id HAVING review_count > 0
        ORDER BY (review_count * 0.4 + avg_r * 0.6 * 10) DESC LIMIT 1""", (current_month, vendor_id))
    winner = c.fetchone()
    if winner:
        c.execute("SELECT COUNT(*) FROM employee_reviews WHERE employee_id=? AND would_book_again=1 AND strftime('%Y-%m',created_at)=?", (winner[0], current_month))
        ba = c.fetchone()[0]
        pct = round(ba / winner[2] * 100, 1) if winner[2] > 0 else 0
        c.execute("DELETE FROM groomer_of_month WHERE vendor_id=? AND month=?", (vendor_id, current_month))
        c.execute("INSERT INTO groomer_of_month (employee_id, vendor_id, month, total_reviews, avg_rating, would_book_again_pct) VALUES (?,?,?,?,?,?)",
            (winner[0], vendor_id, current_month, winner[2], winner[3], pct))
        c.execute("UPDATE employees SET is_groomer_of_month=1 WHERE id=?", (winner[0],))
        try:
            socketio.emit('groomer_of_month', {'employee_name': winner[1], 'month': current_month})
        except:
            pass
    conn.commit()
    conn.close()
    flash("Groomer of the Month calculated!")
    return redirect(url_for("manage_time_slots"))

@app.route('/api/hr-metrics')
def api_get_hr_metrics():
    """API endpoint for HR metrics"""
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

    # Get HR metrics
    hr_metrics = get_hr_metrics(vendor_id, c)
    
    conn.close()
    
    return {"success": True, "metrics": hr_metrics}

@app.route('/api/available-slots/<int:vendor_id>')
def get_available_slots(vendor_id):
    """API endpoint to get available time slots for a specific date"""
    date = request.args.get('date')
    if not date:
        return {"error": "Date parameter required"}, 400

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor time slot settings
    c.execute("SELECT * FROM vendor_time_slots WHERE vendor_id = ? AND is_active = 1", (vendor_id,))
    settings = c.fetchone()

    if not settings:
        # Default settings if none configured
        available_slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", 
                          "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]
    else:
        # Generate slots based on vendor settings
        available_slots = generate_time_slots(settings, date)

    # Check existing bookings for this date
    c.execute("""
        SELECT time, COUNT(*) as booking_count
        FROM bookings 
        WHERE vendor_id = ? AND date = ? AND status != 'cancelled'
        GROUP BY time
    """, (vendor_id, date))
    
    existing_bookings = dict(c.fetchall())
    max_capacity = settings[6] if settings else 1  # max_groomers

    # Filter out fully booked slots
    final_slots = []
    for slot in available_slots:
        current_bookings = existing_bookings.get(slot, 0)
        if current_bookings < max_capacity:
            final_slots.append({
                "time": slot,
                "available": True,
                "remaining_capacity": max_capacity - current_bookings
            })

    conn.close()
    return {"slots": final_slots}

def generate_time_slots(settings, date):
    """Generate time slots based on vendor settings"""
    from datetime import datetime, timedelta, timedelta
    
    # Parse settings
    opening_time = datetime.strptime(settings[2], "%H:%M").time()
    closing_time = datetime.strptime(settings[3], "%H:%M").time()
    slot_duration = settings[4]  # in minutes
    lunch_start = datetime.strptime(settings[5], "%H:%M").time() if settings[5] else None
    lunch_end = datetime.strptime(settings[6], "%H:%M").time() if settings[6] else None
    
    # Check if the date falls on an available day
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day_name = date_obj.strftime('%a').lower()
    available_days = settings[8].split(',') if settings[8] else []
    
    if day_name not in available_days:
        return []
    
    slots = []
    current_time = datetime.combine(date_obj.date(), opening_time)
    end_time = datetime.combine(date_obj.date(), closing_time)
    
    while current_time < end_time:
        slot_time = current_time.time()
        
        # Skip lunch break slots
        if lunch_start and lunch_end:
            if lunch_start <= slot_time < lunch_end:
                current_time += timedelta(minutes=slot_duration)
                continue
        
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=slot_duration)
    
    return slots

@app.route('/erp/logout')
def erp_logout():
    session.pop("vendor", None)
    session.pop("vendor_id", None)
    session.pop("vendor_name", None)
    return redirect(url_for("erp_login"))

# ---- CRM ROUTES ----

# Duplicate route removed - CRM dashboard is already defined above

# Duplicate crm_customers route removed - already defined above

# Duplicate add_crm_customer route removed - already defined above

# ---- MODULE MANAGEMENT ROUTES ----

@app.route('/erp/modules')
def module_management():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get vendor ID
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        return redirect(url_for("erp_login"))
    
    vendor_id = vendor_result[0]
    
    module_manager = ModuleManager()
    modules = module_manager.get_vendor_modules(vendor_id)
    
    # Calculate stats
    enabled_count = sum(1 for m in modules if m['is_enabled'])
    trial_count = sum(1 for m in modules if m['status'] == 'trial')
    total_monthly_cost = sum(m['monthly_price'] for m in modules if m['is_enabled'] and m['subscription_type'] != 'trial')
    total_modules = len(modules)
    
    # Category icons
    category_icons = {
        'core': 'home',
        'inventory': 'boxes',
        'crm': 'users',
        'hr': 'user-tie',
        'accounting': 'calculator',
        'communication': 'comments',
        'ai': 'robot',
        'furrwings': 'plane',
        'social': 'heart'
    }
    
    conn.close()
    
    return render_template("module_management.html", 
                         modules=modules,
                         enabled_count=enabled_count,
                         trial_count=trial_count,
                         total_monthly_cost=total_monthly_cost,
                         total_modules=total_modules,
                         category_icons=category_icons)

@app.route('/erp/modules/enable', methods=["POST"])
def enable_module():
    if "vendor" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    data = request.get_json()
    module_name = data.get('module_name')
    
    if not module_name:
        return {"success": False, "message": "Module name required"}, 400

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    conn.close()
    
    if not vendor_result:
        return {"success": False, "message": "Vendor not found"}, 404
    
    vendor_id = vendor_result[0]
    
    module_manager = ModuleManager()
    module_manager.enable_module(vendor_id, module_name)
    
    return {"success": True, "message": f"Module {module_name} enabled successfully"}

@app.route('/erp/modules/disable', methods=["POST"])
def disable_module():
    if "vendor" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    data = request.get_json()
    module_name = data.get('module_name')
    
    if not module_name:
        return {"success": False, "message": "Module name required"}, 400

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    conn.close()
    
    if not vendor_result:
        return {"success": False, "message": "Vendor not found"}, 404
    
    vendor_id = vendor_result[0]
    
    module_manager = ModuleManager()
    success = module_manager.disable_module(vendor_id, module_name)
    
    
    if success:
        return {"success": True, "message": f"Module {module_name} disabled successfully"}
    else:
        return {"success": False, "message": "Cannot disable core modules"}, 400

@app.route('/erp/modules/trial', methods=["POST"])
def start_module_trial():
    if "vendor" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    data = request.get_json()
    module_name = data.get('module_name')
    
    if not module_name:
        return {"success": False, "message": "Module name required"}, 400

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    conn.close()
    
    if not vendor_result:
        return {"success": False, "message": "Vendor not found"}, 404
    
    vendor_id = vendor_result[0]
    
    module_manager = ModuleManager()
    module_manager.start_trial(vendor_id, module_name, trial_days=14)
    
    return {"success": True, "message": f"14-day trial started for {module_name}"}

@app.route('/erp/modules/subscribe/<module_name>')
def module_subscription_page(module_name=None):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    # This would integrate with payment gateway (Razorpay, Stripe, etc.)
    # For now, show a placeholder subscription page
    return render_template("module_subscription.html", module_name=module_name)

@app.route('/erp/modules/subscribe')
def module_subscription_page_general():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    # Redirect to module management if no specific module
    return redirect(url_for("module_management"))

@app.route('/erp/settings')
def erp_settings():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    return render_template("erp_settings.html")

@app.route('/api/vendor-modules')
def get_vendor_modules():
    if "vendor" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
    vendor_result = c.fetchone()
    conn.close()
    
    if not vendor_result:
        return {"success": False, "message": "Vendor not found"}, 404
    
    vendor_id = vendor_result[0]
    
    module_manager = ModuleManager()
    modules = module_manager.get_vendor_modules(vendor_id)
    
    return {"success": True, "modules": modules}

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
@require_module('advanced_accounting')
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

@app.route('/erp/reports/pnl/export')
def pnl_export_csv():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("profit_loss"))
    vendor_id = result[0]
    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    revenue = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(sl.quantity * ib.unit_cost),0) FROM sales_log sl JOIN inventory_batches ib ON sl.product_id = ib.product_id WHERE sl.vendor_id=?", (vendor_id,))
    cogs = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    expenses = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(fee_amount),0) FROM platform_fees WHERE vendor_id=?", (vendor_id,))
    pf = c.fetchone()[0] or 0
    conn.close()
    gross = revenue - cogs
    net = gross - expenses - pf
    import io, csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Profit & Loss Statement"])
    w.writerow(["Item", "Amount"])
    w.writerow(["Revenue", round(revenue, 2)])
    w.writerow(["Cost of Goods Sold", round(cogs, 2)])
    w.writerow(["Gross Profit", round(gross, 2)])
    w.writerow(["Operating Expenses", round(expenses, 2)])
    w.writerow(["Platform Fees", round(pf, 2)])
    w.writerow(["Net Profit", round(net, 2)])
    from flask import Response
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=profit_and_loss.csv"})


@app.route('/erp/reports/ledger/export')
def ledger_export_csv():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("general_ledger"))
    vendor_id = result[0]
    c.execute("""SELECT timestamp, entry_type, account, description, amount, sub_category
                 FROM ledger_entries WHERE vendor_id=? ORDER BY id""", (vendor_id,))
    rows = c.fetchall()
    conn.close()
    import io, csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Type", "Account", "Sub-Category", "Description", "Debit", "Credit", "Running Balance"])
    running = 0
    for r in rows:
        d = r[4] if r[1] == 'debit' else 0
        cr = r[4] if r[1] == 'credit' else 0
        running += d - cr
        w.writerow([r[0], r[1], r[2], r[5] or '', r[3], round(d, 2), round(cr, 2), round(running, 2)])
    from flask import Response
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=general_ledger.csv"})


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
        action = request.form.get("action", "add_expense")

        if action == "set_budget":
            budget_category = request.form.get("budget_category")
            monthly_budget = float(request.form.get("monthly_budget", 0))
            if budget_category and monthly_budget > 0:
                c.execute("DELETE FROM expense_budgets WHERE vendor_id=? AND category=?", (vendor_id, budget_category))
                c.execute("INSERT INTO expense_budgets (vendor_id, category, monthly_budget) VALUES (?, ?, ?)",
                          (vendor_id, budget_category, monthly_budget))
                conn.commit()
            return redirect(url_for("manage_expenses"))

        category = request.form.get("category")
        amount = float(request.form.get("amount", 0))
        description = request.form.get("description")
        date = request.form.get("date")

        receipt_url = None
        receipt_file = request.files.get("receipt")
        if receipt_file and receipt_file.filename:
            import os
            upload_dir = os.path.join("static", "uploads", "receipts")
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{vendor_id}_{int(datetime.now().timestamp())}_{receipt_file.filename}"
            receipt_path = os.path.join(upload_dir, safe_name)
            receipt_file.save(receipt_path)
            receipt_url = "/" + receipt_path.replace("\\", "/")

        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date, receipt_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, category, amount, description, date, receipt_url))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source)
            VALUES (?, 'debit', 'Expenses', ?, ?, ?, 'auto')
        """, (vendor_id, amount, description, category))

        conn.commit()
        return redirect(url_for("manage_expenses"))

    c.execute("SELECT * FROM expenses WHERE vendor_id=? ORDER BY date DESC", (vendor_id,))
    expenses = c.fetchall()

    c.execute("SELECT category, monthly_budget FROM expense_budgets WHERE vendor_id=?", (vendor_id,))
    budgets = {row[0]: row[1] for row in c.fetchall()}

    categories = ['Rent', 'Utilities', 'Supplies', 'Equipment', 'Marketing', 'Insurance', 'Transport', 'Food', 'Veterinary', 'Other']
    budget_vs_actual = []
    for cat in categories:
        c.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE vendor_id=? AND category=? AND date >= date('now', 'start of month')
        """, (vendor_id, cat))
        actual = c.fetchone()[0] or 0
        budget = budgets.get(cat, 0)
        if budget > 0 or actual > 0:
            pct = (actual / budget * 100) if budget > 0 else 0
            budget_vs_actual.append({
                'category': cat,
                'budget': budget,
                'actual': actual,
                'percentage': min(pct, 100),
                'over': actual > budget if budget > 0 else False,
                'status': 'danger' if pct > 90 else ('warning' if pct > 70 else 'success')
            })

    conn.close()
    return render_template("manage_expenses.html", expenses=expenses, budgets=budgets, budget_vs_actual=budget_vs_actual)

@app.route('/erp/finance/journal-entry', methods=["GET", "POST"])
def journal_entry():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("journal_entry.html", entries=[])
    vendor_id = result[0]

    if request.method == "POST":
        entry_date = request.form.get("entry_date", datetime.now().strftime("%Y-%m-%d"))
        entry_type = request.form.get("entry_type", "debit")
        account = request.form.get("account")
        amount = float(request.form.get("amount", 0))
        description = request.form.get("description", "")
        sub_category = request.form.get("sub_category", "")
        reference = request.form.get("reference", "")

        if amount > 0 and account:
            desc_full = f"{description} [Ref: {reference}]" if reference else description
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, 'manual', ?)
            """, (vendor_id, entry_type, account, amount, desc_full, sub_category, entry_date))
            conn.commit()
            flash("Journal entry recorded successfully.")

        return redirect(url_for("journal_entry"))

    c.execute("""
        SELECT id, entry_type, account, amount, description, sub_category, timestamp, entry_source
        FROM ledger_entries WHERE vendor_id=?
        ORDER BY id DESC LIMIT 20
    """, (vendor_id,))
    entries = c.fetchall()
    conn.close()
    return render_template("journal_entry.html", entries=entries)


@app.route('/erp/finance/invoice/create', methods=["GET", "POST"])
def create_invoice():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("accounting_dashboard"))
    vendor_id = vendor_result[0]
    vendor_name = vendor_result[1] or "Vendor"

    c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    gst_result = c.fetchone()
    gst_rate = gst_result[0] if gst_result else 18.0

    if request.method == "POST":
        customer_email = request.form.get("customer_email", "")
        customer_name = request.form.get("customer_name", "")
        invoice_date = request.form.get("invoice_date", datetime.now().strftime("%Y-%m-%d"))
        due_date = request.form.get("due_date", "")
        notes = request.form.get("notes", "")
        payment_terms = request.form.get("payment_terms", "Due on receipt")

        descriptions = request.form.getlist("item_description[]")
        quantities = request.form.getlist("item_quantity[]")
        prices = request.form.getlist("item_price[]")

        subtotal = 0
        line_items = []
        for i in range(len(descriptions)):
            if descriptions[i] and quantities[i] and prices[i]:
                qty = int(quantities[i])
                price = float(prices[i])
                total = qty * price
                subtotal += total
                line_items.append({"description": descriptions[i], "quantity": qty, "unit_price": price, "total": total})

        gst_amount = subtotal * gst_rate / 100
        grand_total = subtotal + gst_amount

        c.execute("""
            INSERT INTO orders (user_email, vendor_id, total_amount, status, delivery_address, order_date)
            VALUES (?, ?, ?, 'invoice', ?, ?)
        """, (customer_email, vendor_id, grand_total, f"Invoice for {customer_name}", invoice_date))
        order_id = c.lastrowid

        for item in line_items:
            c.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, 0, ?, ?)
            """, (order_id, item["quantity"], item["unit_price"]))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
            VALUES (?, 'debit', 'Accounts Receivable', ?, ?, 'Invoice', 'auto', ?)
        """, (vendor_id, grand_total, f"Invoice #{order_id} - {customer_name}", invoice_date))

        conn.commit()

        invoice = {
            "id": order_id,
            "vendor_name": vendor_name,
            "customer_email": customer_email,
            "customer_name": customer_name,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "line_items": line_items,
            "subtotal": subtotal,
            "gst_rate": gst_rate,
            "gst_amount": gst_amount,
            "grand_total": grand_total,
            "notes": notes,
            "payment_terms": payment_terms
        }
        conn.close()
        return render_template("invoice_view.html", invoice=invoice)

    conn.close()
    return render_template("invoice_create.html", gst_rate=gst_rate, vendor_name=vendor_name)


@app.route('/erp/finance/gst-summary')
def gst_summary():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("gst_summary.html", data={})
    vendor_id = result[0]

    start_date = request.args.get("start_date", datetime.now().strftime("%Y-%m-01"))
    end_date = request.args.get("end_date", datetime.now().strftime("%Y-%m-%d"))
    export = request.args.get("export")

    c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    gst_result = c.fetchone()
    gst_rate = gst_result[0] if gst_result else 18.0

    c.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM sales_log
        WHERE vendor_id=? AND sale_date BETWEEN ? AND ?
    """, (vendor_id, start_date, end_date))
    total_sales = c.fetchone()[0] or 0

    gst_collected = total_sales * gst_rate / (100 + gst_rate)

    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE vendor_id=? AND date BETWEEN ? AND ?
    """, (vendor_id, start_date, end_date))
    total_expenses = c.fetchone()[0] or 0

    gst_paid = total_expenses * 18 / 118
    input_credit = gst_paid
    net_gst = gst_collected - input_credit

    c.execute("""
        SELECT 'Sale' as type, sale_date as date, 
               COALESCE(p.name, 'Product') as description,
               sl.total_amount as amount,
               sl.total_amount * ? / (100 + ?) as gst
        FROM sales_log sl
        LEFT JOIN products p ON sl.product_id = p.id
        WHERE sl.vendor_id=? AND sl.sale_date BETWEEN ? AND ?
        ORDER BY sl.sale_date DESC
    """, (gst_rate, gst_rate, vendor_id, start_date, end_date))
    sale_txns = [{"type": "Sale", "date": r[1], "description": r[2], "amount": r[3], "gst": round(r[4], 2)} for r in c.fetchall()]

    c.execute("""
        SELECT date, category, description, amount
        FROM expenses WHERE vendor_id=? AND date BETWEEN ? AND ?
        ORDER BY date DESC
    """, (vendor_id, start_date, end_date))
    expense_txns = [{"type": "Expense", "date": r[0], "description": f"{r[1]} - {r[2] or ''}", "amount": r[3], "gst": round(r[3] * 18 / 118, 2)} for r in c.fetchall()]

    transactions = sale_txns + expense_txns
    transactions.sort(key=lambda x: x["date"], reverse=True)

    conn.close()

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "total_sales": round(total_sales, 2),
        "gst_collected": round(gst_collected, 2),
        "total_expenses": round(total_expenses, 2),
        "gst_paid": round(gst_paid, 2),
        "input_credit": round(input_credit, 2),
        "net_gst": round(net_gst, 2),
        "gst_rate": gst_rate,
        "transactions": transactions
    }

    if export == "csv":
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["GST Summary Report", f"{start_date} to {end_date}"])
        writer.writerow([])
        writer.writerow(["Total Sales", total_sales])
        writer.writerow(["GST Collected", round(gst_collected, 2)])
        writer.writerow(["Total Expenses", total_expenses])
        writer.writerow(["GST Paid (Input Credit)", round(gst_paid, 2)])
        writer.writerow(["Net GST Payable", round(net_gst, 2)])
        writer.writerow([])
        writer.writerow(["Type", "Date", "Description", "Amount", "GST"])
        for t in transactions:
            writer.writerow([t["type"], t["date"], t["description"], t["amount"], t["gst"]])

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=gst_summary_{start_date}_{end_date}.csv"}
        )

    return render_template("gst_summary.html", data=data)


@app.route('/erp/finance/ca-package')
def ca_package():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("accounting_dashboard"))
    vendor_id = result[0]
    vendor_name = result[1] or "Vendor"

    c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    gst_result = c.fetchone()
    gst_rate = gst_result[0] if gst_result else 18.0

    now = datetime.now()
    month_start = now.strftime("%Y-%m-01")
    month_end = now.strftime("%Y-%m-%d")

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_revenue = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    total_expenses = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(fee_amount),0) FROM platform_fees WHERE vendor_id=?", (vendor_id,))
    platform_fees = c.fetchone()[0] or 0

    gross_profit = total_revenue - total_expenses
    net_profit = gross_profit - platform_fees

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date BETWEEN ? AND ?",
              (vendor_id, month_start, month_end))
    gst_total_sales = c.fetchone()[0] or 0
    gst_collected = gst_total_sales * gst_rate / (100 + gst_rate)

    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND date BETWEEN ? AND ?",
              (vendor_id, month_start, month_end))
    gst_total_expenses = c.fetchone()[0] or 0
    gst_paid = gst_total_expenses * 18 / 118
    input_tax_credit = gst_paid
    net_gst_payable = gst_collected - input_tax_credit

    cash_balance = total_revenue - total_expenses

    c.execute("SELECT COALESCE(SUM(quantity * buy_price),0) FROM products WHERE vendor_id=?", (vendor_id,))
    inventory_value = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM receivable_entries WHERE vendor_id=? AND status != 'paid'", (vendor_id,))
    accounts_receivable = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM payable_entries WHERE vendor_id=? AND status != 'paid'", (vendor_id,))
    accounts_payable = c.fetchone()[0] or 0

    total_assets = cash_balance + inventory_value + accounts_receivable
    total_liabilities = accounts_payable
    equity = total_assets - total_liabilities

    c.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_entries WHERE vendor_id=? AND entry_type='debit'", (vendor_id,))
    total_debits = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_entries WHERE vendor_id=? AND entry_type='credit'", (vendor_id,))
    total_credits = c.fetchone()[0] or 0

    c.execute("""SELECT timestamp, account, entry_type, amount, description
                 FROM ledger_entries WHERE vendor_id=? ORDER BY id DESC LIMIT 10""", (vendor_id,))
    last_transactions = [{"date": r[0], "account": r[1], "type": r[2], "amount": r[3], "description": r[4]} for r in c.fetchall()]

    c.execute("""SELECT category, SUM(amount) as total FROM expenses
                 WHERE vendor_id=? GROUP BY category ORDER BY total DESC LIMIT 5""", (vendor_id,))
    top_expenses = [{"category": r[0], "amount": r[1]} for r in c.fetchall()]

    c.execute("SELECT COUNT(*) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    sales_count = c.fetchone()[0] or 0

    c.execute("""SELECT p.name, SUM(sl.total_amount) as rev
                 FROM sales_log sl LEFT JOIN products p ON sl.product_id=p.id
                 WHERE sl.vendor_id=? GROUP BY sl.product_id ORDER BY rev DESC LIMIT 3""", (vendor_id,))
    top_products = [{"name": r[0] or "Product", "revenue": r[1]} for r in c.fetchall()]

    conn.close()

    data = {
        "vendor_name": vendor_name,
        "vendor_email": email,
        "generated": now.strftime("%d %b %Y, %I:%M %p"),
        "period": now.strftime("%B %Y"),
        "pnl": {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "platform_fees": round(platform_fees, 2),
            "gross_profit": round(gross_profit, 2),
            "net_profit": round(net_profit, 2),
        },
        "gst": {
            "total_sales": round(gst_total_sales, 2),
            "gst_collected": round(gst_collected, 2),
            "total_expenses": round(gst_total_expenses, 2),
            "gst_paid": round(gst_paid, 2),
            "input_tax_credit": round(input_tax_credit, 2),
            "net_gst_payable": round(net_gst_payable, 2),
        },
        "balance_sheet": {
            "cash": round(cash_balance, 2),
            "inventory": round(inventory_value, 2),
            "accounts_receivable": round(accounts_receivable, 2),
            "accounts_payable": round(accounts_payable, 2),
            "total_assets": round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "equity": round(equity, 2),
        },
        "ledger": {
            "total_debits": round(total_debits, 2),
            "total_credits": round(total_credits, 2),
            "last_transactions": last_transactions,
        },
        "top_expenses": top_expenses,
        "sales": {
            "count": sales_count,
            "total_revenue": round(total_revenue, 2),
            "top_products": top_products,
        },
    }
    return render_template("ca_package.html", data=data)


def _ca_get_vendor(session_obj):
    if "vendor" not in session_obj:
        return None, None, None
    email = session_obj["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return None, None, None
    return conn, c, result


@app.route('/erp/finance/ca-package/export/zip')
def ca_export_zip():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    import zipfile
    conn_result = _ca_get_vendor(session)
    conn, c, vendor_row = conn_result
    if not conn:
        flash("Vendor not found")
        return redirect(url_for("accounting_dashboard"))
    vendor_id = vendor_row[0]

    c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vendor_id,))
    gst_r = c.fetchone()
    gst_rate = gst_r[0] if gst_r else 18.0

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=?", (vendor_id,))
    total_revenue = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=?", (vendor_id,))
    total_expenses = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(fee_amount),0) FROM platform_fees WHERE vendor_id=?", (vendor_id,))
    platform_fees_val = c.fetchone()[0] or 0
    gross_profit = total_revenue - total_expenses
    net_profit = gross_profit - platform_fees_val

    now = datetime.now()
    ms = now.strftime("%Y-%m-01")
    me = now.strftime("%Y-%m-%d")
    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date BETWEEN ? AND ?", (vendor_id, ms, me))
    gst_sales = c.fetchone()[0] or 0
    gst_collected = gst_sales * gst_rate / (100 + gst_rate)
    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND date BETWEEN ? AND ?", (vendor_id, ms, me))
    gst_exp = c.fetchone()[0] or 0
    gst_paid = gst_exp * 18 / 118
    itc = gst_paid
    net_gst = gst_collected - itc

    cash_bal = total_revenue - total_expenses
    c.execute("SELECT COALESCE(SUM(quantity * buy_price),0) FROM products WHERE vendor_id=?", (vendor_id,))
    inv_val = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM receivable_entries WHERE vendor_id=? AND status != 'paid'", (vendor_id,))
    ar = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM payable_entries WHERE vendor_id=? AND status != 'paid'", (vendor_id,))
    ap = c.fetchone()[0] or 0
    total_assets = cash_bal + inv_val + ar
    total_liabilities = ap
    equity_val = total_assets - total_liabilities

    c.execute("SELECT timestamp, entry_type, account, description, amount FROM ledger_entries WHERE vendor_id=? ORDER BY id", (vendor_id,))
    ledger_rows = c.fetchall()

    c.execute("SELECT date, category, amount, description FROM expenses WHERE vendor_id=? ORDER BY date", (vendor_id,))
    expense_rows = c.fetchall()

    c.execute("""SELECT sl.sale_date, COALESCE(p.name,'Product'), sl.quantity, sl.unit_price, sl.total_amount, sl.customer_email
                 FROM sales_log sl LEFT JOIN products p ON sl.product_id=p.id WHERE sl.vendor_id=? ORDER BY sl.sale_date""", (vendor_id,))
    sales_rows = c.fetchall()
    conn.close()

    import io, csv
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Revenue","COGS","Gross Profit","Expenses","Platform Fees","Net Profit"])
        w.writerow([round(total_revenue,2), 0, round(gross_profit,2), round(total_expenses,2), round(platform_fees_val,2), round(net_profit,2)])
        zf.writestr("pnl.csv", buf.getvalue())

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Total Sales","GST Collected","Total Expenses","GST Paid","Input Tax Credit","Net GST Payable"])
        w.writerow([round(gst_sales,2), round(gst_collected,2), round(gst_exp,2), round(gst_paid,2), round(itc,2), round(net_gst,2)])
        zf.writestr("gst_summary.csv", buf.getvalue())

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Item","Value"])
        w.writerow(["Cash",round(cash_bal,2)])
        w.writerow(["Inventory",round(inv_val,2)])
        w.writerow(["Accounts Receivable",round(ar,2)])
        w.writerow(["Total Assets",round(total_assets,2)])
        w.writerow(["Accounts Payable",round(ap,2)])
        w.writerow(["Total Liabilities",round(total_liabilities,2)])
        w.writerow(["Equity",round(equity_val,2)])
        zf.writestr("balance_sheet.csv", buf.getvalue())

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Date","Type","Account","Description","Debit","Credit","Running Balance"])
        running = 0
        for r in ledger_rows:
            d = r[4] if r[1] == 'debit' else 0
            cr = r[4] if r[1] == 'credit' else 0
            running += d - cr
            w.writerow([r[0], r[1], r[2], r[3], round(d,2), round(cr,2), round(running,2)])
        zf.writestr("ledger.csv", buf.getvalue())

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Date","Category","Amount","Description"])
        for r in expense_rows:
            w.writerow([r[0], r[1], round(r[2],2), r[3]])
        zf.writestr("expenses.csv", buf.getvalue())

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Date","Product","Quantity","Unit Price","Total","Customer"])
        for r in sales_rows:
            w.writerow([r[0], r[1], r[2], round(r[3],2), round(r[4],2), r[5]])
        zf.writestr("sales.csv", buf.getvalue())

    mem.seek(0)
    from flask import Response
    return Response(mem.getvalue(), mimetype="application/zip",
                    headers={"Content-Disposition": "attachment;filename=furrbutler_ca_package.zip"})


def _ca_single_csv(csv_name, header, row_fn):
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    conn_result = _ca_get_vendor(session)
    conn, c, vendor_row = conn_result
    if not conn:
        flash("Vendor not found")
        return redirect(url_for("accounting_dashboard"))
    vendor_id = vendor_row[0]
    import io, csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    row_fn(c, vendor_id, w)
    conn.close()
    from flask import Response
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename={csv_name}"})


@app.route('/erp/finance/ca-package/export/pnl')
def ca_export_pnl():
    def write_rows(c, vid, w):
        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=?", (vid,))
        rev = c.fetchone()[0] or 0
        c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=?", (vid,))
        exp = c.fetchone()[0] or 0
        c.execute("SELECT COALESCE(SUM(fee_amount),0) FROM platform_fees WHERE vendor_id=?", (vid,))
        pf = c.fetchone()[0] or 0
        w.writerow([round(rev,2), 0, round(rev-exp,2), round(exp,2), round(pf,2), round(rev-exp-pf,2)])
    return _ca_single_csv("pnl.csv", ["Revenue","COGS","Gross Profit","Expenses","Platform Fees","Net Profit"], write_rows)


@app.route('/erp/finance/ca-package/export/gst')
def ca_export_gst():
    def write_rows(c, vid, w):
        c.execute("SELECT gst_rate FROM settings_vendor WHERE vendor_id=?", (vid,))
        gr = c.fetchone()
        gst_rate = gr[0] if gr else 18.0
        now = datetime.now()
        ms, me = now.strftime("%Y-%m-01"), now.strftime("%Y-%m-%d")
        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date BETWEEN ? AND ?", (vid, ms, me))
        ts = c.fetchone()[0] or 0
        gc = ts * gst_rate / (100 + gst_rate)
        c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND date BETWEEN ? AND ?", (vid, ms, me))
        te = c.fetchone()[0] or 0
        gp = te * 18 / 118
        w.writerow([round(ts,2), round(gc,2), round(te,2), round(gp,2), round(gp,2), round(gc-gp,2)])
    return _ca_single_csv("gst_summary.csv", ["Total Sales","GST Collected","Total Expenses","GST Paid","Input Tax Credit","Net GST Payable"], write_rows)


@app.route('/erp/finance/ca-package/export/balance-sheet')
def ca_export_balance_sheet():
    def write_rows(c, vid, w):
        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=?", (vid,))
        rev = c.fetchone()[0] or 0
        c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=?", (vid,))
        exp = c.fetchone()[0] or 0
        cash = rev - exp
        c.execute("SELECT COALESCE(SUM(quantity*buy_price),0) FROM products WHERE vendor_id=?", (vid,))
        inv = c.fetchone()[0] or 0
        c.execute("SELECT COALESCE(SUM(balance_due),0) FROM receivable_entries WHERE vendor_id=? AND status!='paid'", (vid,))
        ar = c.fetchone()[0] or 0
        c.execute("SELECT COALESCE(SUM(balance_due),0) FROM payable_entries WHERE vendor_id=? AND status!='paid'", (vid,))
        ap = c.fetchone()[0] or 0
        ta = cash + inv + ar
        tl = ap
        eq = ta - tl
        w.writerow(["Cash", round(cash,2)])
        w.writerow(["Inventory", round(inv,2)])
        w.writerow(["Accounts Receivable", round(ar,2)])
        w.writerow(["Total Assets", round(ta,2)])
        w.writerow(["Accounts Payable", round(ap,2)])
        w.writerow(["Total Liabilities", round(tl,2)])
        w.writerow(["Equity", round(eq,2)])
    return _ca_single_csv("balance_sheet.csv", ["Item","Value"], write_rows)


@app.route('/erp/finance/ca-package/export/ledger')
def ca_export_ledger():
    def write_rows(c, vid, w):
        c.execute("SELECT timestamp, entry_type, account, description, amount FROM ledger_entries WHERE vendor_id=? ORDER BY id", (vid,))
        running = 0
        for r in c.fetchall():
            d = r[4] if r[1] == 'debit' else 0
            cr = r[4] if r[1] == 'credit' else 0
            running += d - cr
            w.writerow([r[0], r[1], r[2], r[3], round(d,2), round(cr,2), round(running,2)])
    return _ca_single_csv("ledger.csv", ["Date","Type","Account","Description","Debit","Credit","Running Balance"], write_rows)


@app.route('/erp/finance/ca-package/export/expenses')
def ca_export_expenses():
    def write_rows(c, vid, w):
        c.execute("SELECT date, category, amount, description FROM expenses WHERE vendor_id=? ORDER BY date", (vid,))
        for r in c.fetchall():
            w.writerow([r[0], r[1], round(r[2],2), r[3]])
    return _ca_single_csv("expenses.csv", ["Date","Category","Amount","Description"], write_rows)


@app.route('/erp/finance/ca-package/export/sales')
def ca_export_sales():
    def write_rows(c, vid, w):
        c.execute("""SELECT sl.sale_date, COALESCE(p.name,'Product'), sl.quantity, sl.unit_price, sl.total_amount, sl.customer_email
                     FROM sales_log sl LEFT JOIN products p ON sl.product_id=p.id WHERE sl.vendor_id=? ORDER BY sl.sale_date""", (vid,))
        for r in c.fetchall():
            w.writerow([r[0], r[1], r[2], round(r[3],2), round(r[4],2), r[5]])
    return _ca_single_csv("sales.csv", ["Date","Product","Quantity","Unit Price","Total","Customer"], write_rows)


@app.route('/erp/reports/settings', methods=["GET", "POST"])
def accounting_settings():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()

    if result is None:
        conn.close()
        return render_template("accounting_settings.html", settings=None)

    vendor_id = result[0]

    if request.method == "POST":
        gst_rate = float(request.form.get("gst_rate", 18.0))
        razorpay_enabled = 1 if request.form.get("razorpay_enabled") else 0
        cod_enabled = 1 if request.form.get("cod_enabled") else 0
        auto_reports = 1 if request.form.get("auto_reports") else 0

        standard_delivery = float(request.form.get("standard_delivery_price", 2.99))
        express_delivery = float(request.form.get("express_delivery_price", 5.99))
        same_day_delivery = float(request.form.get("same_day_delivery_price", 12.99))
        free_delivery_threshold = float(request.form.get("free_delivery_threshold", 50.00))

        currency_code = (request.form.get("currency") or "INR").upper().strip()
        if currency_code not in ISO_4217_CURRENCIES:
            currency_code = "INR"
        currency_symbol = ISO_4217_CURRENCIES[currency_code]["symbol"]

        c.execute("SELECT setting_value FROM master_settings WHERE setting_name = 'platform_commission_rate'")
        platform_fee_result = c.fetchone()
        platform_fee = platform_fee_result[0] if platform_fee_result else 10.0

        c.execute("""
            INSERT OR REPLACE INTO settings_vendor 
            (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports, 
             standard_delivery_price, express_delivery_price, same_day_delivery_price, free_delivery_threshold,
             currency, currency_symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports,
              standard_delivery, express_delivery, same_day_delivery, free_delivery_threshold,
              currency_code, currency_symbol))

        conn.commit()
        flash("Settings updated successfully!")
        return redirect(url_for("accounting_settings"))

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
@require_module('advanced_inventory')
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

    search_lat = None
    search_lon = None
    location_name = None

    location_query = request.args.get("location") or request.args.get("city")
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query
    elif session.get("location"):
        loc = session["location"]
        search_lat = loc.get("lat")
        search_lon = loc.get("lon")
        location_name = loc.get("name", "Your location")

    vendors = []
    if search_lat is not None and search_lon is not None:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT v.id, v.name, v.email, v.password, v.category, v.city, v.phone, v.bio, v.image_url,
                   v.latitude, v.longitude, v.is_online, v.account_status, v.break_start_date, v.break_end_date,
                   v.break_reason, v.address, v.state, v.pincode, v.delivery_radius_km,
                   (SELECT COUNT(*) FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0) as product_count
            FROM vendors v
            WHERE EXISTS (
                SELECT 1 FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0
            )
            AND (
                v.is_online = 1
                OR NOT (LOWER(v.category) LIKE '%groom%' OR LOWER(v.category) LIKE '%salon%' OR LOWER(v.category) LIKE '%spa%' OR LOWER(v.category) LIKE '%boarding%')
            )
            AND (v.account_status IS NULL OR v.account_status = 'active')
        """)
        online_vendors = c.fetchall()
        conn.close()

        for vendor in online_vendors:
            v_lat = vendor[9]
            v_lon = vendor[10]
            if v_lat is None or v_lon is None:
                continue
            radius = vendor[19] or 5.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vendors.append({
                    "id": vendor[0],
                    "name": vendor[1],
                    "email": vendor[2],
                    "category": vendor[4],
                    "city": vendor[5],
                    "bio": vendor[7],
                    "image_url": vendor[8] or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400&h=400&fit=crop&crop=face",
                    "latitude": v_lat,
                    "longitude": v_lon,
                    "product_count": vendor[20],
                    "is_online": vendor[11],
                    "address": vendor[16] or "",
                    "state": vendor[17] or "",
                    "pincode": vendor[18] or "",
                    "distance": round(dist, 1)
                })
        vendors.sort(key=lambda v: v["distance"])

    return render_template("marketplace.html", vendors=vendors,
                           location_name=location_name,
                           has_searched=bool(location_query or session.get("location")))

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

@app.route('/checkout-booking')
def checkout_booking():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Get user's pets for the checkout
    user_email = session["user"]
    pets = db.get(f"pets:{user_email}", [])
    
    return render_template("checkout_booking.html", pets=pets)

@app.route('/process-booking-checkout', methods=["POST"])
def process_booking_checkout():
    if "user" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    user_email = session["user"]
    data = request.get_json()

    if not data or 'bookings' not in data:
        return {"success": False, "error": "No booking data provided"}, 400

    try:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        
        # Get user's pets
        pets = db.get(f"pets:{user_email}", [])
        
        booking_ids = []
        
        for booking in data['bookings']:
            # Find the pet
            pet = next((p for p in pets if p['name'] == booking['pet_name']), None)
            if not pet:
                continue
                
            vendor_id = booking.get('vendor_id', 0)
            if vendor_id == 'fluffy-paws':
                vendor_id = 0
            
            # Check time slot capacity before booking
            c.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE vendor_id = ? AND date = ? AND time = ? AND status != 'cancelled'
            """, (vendor_id, booking['date'], booking['time']))
            
            current_bookings = c.fetchone()[0]
            
            # Get vendor capacity
            c.execute("SELECT max_groomers FROM vendor_time_slots WHERE vendor_id = ?", (vendor_id,))
            capacity_result = c.fetchone()
            max_capacity = capacity_result[0] if capacity_result else 1
            
            if current_bookings >= max_capacity:
                return {"success": False, "error": f"Time slot {booking['time']} is fully booked"}, 400

            # Insert booking
            c.execute("""
                INSERT INTO bookings (vendor_id, user_email, service, date, time, duration, status, pet_name, pet_parent_name, pet_parent_phone, status_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vendor_id, user_email, booking['service'], booking['date'], booking['time'], 
                  booking['duration'], "confirmed", pet['name'], pet.get('parent_name', ''), 
                  pet.get('parent_phone', ''), booking.get('notes', '')))
            
            booking_ids.append(c.lastrowid)
        
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": f"Successfully booked {len(booking_ids)} services!",
            "booking_ids": booking_ids
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

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

    flash(f"Order #{order_id} status updated to {new_status.replace('_', ' ').title() if new_status else 'unknown'}")
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
@app.route('/admin/login', methods=["GET", "POST"])
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
    
    # Get FurrWings vets
    c.execute("""
        SELECT id, name, email, password, 'Veterinarian' as category, city, phone, 
               clinic_name as bio, is_active as is_online, 
               CASE WHEN is_active = 1 THEN 'active' ELSE 'deactivated' END as account_status,
               NULL as break_start_date, NULL as break_reason
        FROM vets 
        ORDER BY name
    """)
    vets = c.fetchall()
    
    # Get FurrWings handlers
    c.execute("""
        SELECT id, name, email, password, 'Pet Handler' as category, city, phone, 
               company_name as bio, is_active as is_online,
               CASE WHEN is_active = 1 THEN 'active' ELSE 'deactivated' END as account_status,
               NULL as break_start_date, NULL as break_reason
        FROM handlers 
        ORDER BY name
    """)
    handlers = c.fetchall()
    
    # Get FurrWings isolation centers
    c.execute("""
        SELECT id, name, email, password, 'Isolation Center' as category, city, phone, 
               center_name as bio, is_active as is_online,
               CASE WHEN is_active = 1 THEN 'active' ELSE 'deactivated' END as account_status,
               NULL as break_start_date, NULL as break_reason
        FROM isolation_centers 
        ORDER BY name
    """)
    isolation_centers = c.fetchall()

    # Combine all vendor types
    all_vendors = []
    
    # Process regular vendors
    for vendor in vendors:
        vendor_data = list(vendor) + ['Regular Vendor']  # Add vendor type
        all_vendors.append(vendor_data)
    
    # Process vets
    for vet in vets:
        vendor_data = list(vet) + ['FurrWings Vet']  # Add vendor type
        all_vendors.append(vendor_data)
    
    # Process handlers  
    for handler in handlers:
        vendor_data = list(handler) + ['FurrWings Handler']  # Add vendor type
        all_vendors.append(vendor_data)
    
    # Process isolation centers
    for center in isolation_centers:
        vendor_data = list(center) + ['FurrWings Isolation']  # Add vendor type
        all_vendors.append(vendor_data)

    # Get vendor statistics
    vendor_stats = []
    for vendor_data in all_vendors:
        vendor = vendor_data[:-1]  # Remove vendor type for processing
        vendor_type = vendor_data[-1]  # Get vendor type
        vendor_id = vendor[0]
        
        # Initialize default stats
        total_products = 0
        total_sales = 0
        total_bookings = 0
        avg_rating = 0
        
        # Get stats based on vendor type
        if vendor_type == 'Regular Vendor':
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
        
        elif vendor_type == 'FurrWings Vet':
            # Get vet-specific stats
            c.execute("SELECT COUNT(*) FROM vet_appointments WHERE vet_id = ?", (vendor_id,))
            total_bookings = c.fetchone()[0]
            
            c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM vet_invoices WHERE patient_id IN (SELECT id FROM vet_patients WHERE id IN (SELECT patient_id FROM vet_appointments WHERE vet_id = ?))", (vendor_id,))
            total_sales = c.fetchone()[0]
        
        elif vendor_type == 'FurrWings Handler':
            # Get handler-specific stats
            c.execute("SELECT COUNT(*) FROM handler_bookings WHERE handler_id = ?", (vendor_id,))
            total_bookings = c.fetchone()[0]
            
            c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM handler_bookings WHERE handler_id = ?", (vendor_id,))
            total_sales = c.fetchone()[0]
            
            c.execute("SELECT COALESCE(AVG(rating), 0) FROM handler_reviews WHERE handler_id = ?", (vendor_id,))
            avg_rating = c.fetchone()[0]
        
        elif vendor_type == 'FurrWings Isolation':
            # Get isolation center stats
            c.execute("SELECT COUNT(*) FROM pet_bookings WHERE center_id = ?", (vendor_id,))
            total_bookings = c.fetchone()[0]
        
        vendor_stats.append({
            'vendor': vendor,
            'vendor_type': vendor_type,
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
@app.route('/admin/logout')
def master_admin_logout():
    session.pop("master_admin", None)
    flash("You have been logged out successfully")
    return redirect(url_for("master_admin_login"))

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
        from datetime import datetime, timedelta, timedelta
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

@app.route('/erp/inventory/scan-barcode', methods=["GET", "POST"])
def scan_barcode():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    if request.method == "GET":
        return redirect(url_for("add_stock_page"))

    if request.is_json:
        barcode = request.json.get("barcode", "")
    else:
        barcode = request.form.get("barcode", "")
    if not barcode:
        return {"success": False, "error": "No barcode provided"}, 400

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return {"success": False, "error": "Vendor not found"}, 404
    vendor_id = vendor_result[0]

    c.execute("SELECT id, name, category, buy_price, sale_price, quantity, barcode FROM products WHERE vendor_id=? AND barcode=?", (vendor_id, barcode))
    product = c.fetchone()
    conn.close()

    if product:
        return {
            "success": True,
            "source": "local",
            "product": {
                "id": product[0],
                "name": product[1],
                "category": product[2] or "",
                "buy_price": product[3] or 0,
                "sale_price": product[4] or 0,
                "current_stock": product[5] or 0,
                "barcode": product[6]
            }
        }

    try:
        import urllib.request
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "FurrButler/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json
            data = json.loads(resp.read().decode())
            if data.get("status") == 1:
                p = data.get("product", {})
                return {
                    "success": True,
                    "source": "openfoodfacts",
                    "product": {
                        "name": p.get("product_name", "Unknown Product"),
                        "brand": p.get("brands", ""),
                        "category": p.get("categories", "").split(",")[0].strip() if p.get("categories") else "General",
                        "barcode": barcode
                    }
                }
    except Exception:
        pass

    return {"success": True, "source": "not_found", "barcode": barcode}


@app.route('/erp/inventory/add-stock', methods=["GET"])
def add_stock_page():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    products = []
    if vendor_result:
        vendor_id = vendor_result[0]
        c.execute("SELECT id, name, quantity, buy_price, barcode FROM products WHERE vendor_id=? ORDER BY name", (vendor_id,))
        products = c.fetchall()
    conn.close()
    return render_template("add_stock_form.html", products=products)


@app.route('/erp/inventory/add-stock', methods=["POST"])
def add_stock_submit():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    try:
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()
        if not vendor_result:
            flash("Vendor not found")
            conn.close()
            return redirect(url_for("add_stock_page"))
        vendor_id = vendor_result[0]

        entry_method = request.form.get("entry_method", "manual_entry")
        product_id = request.form.get("product_id")
        barcode = request.form.get("barcode", "")
        quantity = int(request.form.get("quantity", 0))
        unit_cost = float(request.form.get("unit_cost", 0))
        batch_name = request.form.get("batch_name", f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        notes = request.form.get("notes", "")

        if quantity <= 0 or unit_cost <= 0:
            flash("Invalid quantity or cost")
            return redirect(url_for("add_stock_page"))

        if product_id:
            product_id = int(product_id)
            c.execute("SELECT name FROM products WHERE id=? AND vendor_id=?", (product_id, vendor_id))
            prod = c.fetchone()
            if not prod:
                flash("Product not found")
                return redirect(url_for("add_stock_page"))
            product_name = prod[0]
        else:
            product_name = request.form.get("product_name", "Unnamed Product")
            category = request.form.get("category", "General")
            brand = request.form.get("brand", "")
            sale_price = float(request.form.get("sale_price", 0))
            if not barcode:
                barcode = f"FB{vendor_id}{int(datetime.now().timestamp())}"
            description = f"Brand: {brand}" if brand else ""

            c.execute("""
                INSERT INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, barcode)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (vendor_id, product_name, description, category, unit_cost, sale_price, barcode))
            product_id = c.lastrowid

        total_cost = quantity * unit_cost

        c.execute("""
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        """, (product_id, quantity, unit_cost, quantity))

        c.execute("""
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, batch_name, quantity, unit_cost, datetime.now().strftime("%Y-%m-%d")))

        c.execute("UPDATE products SET quantity = quantity + ?, buy_price = ? WHERE id = ?",
                  (quantity, unit_cost, product_id))

        c.execute("""
            INSERT INTO restock_log (vendor_id, product_id, quantity_added, unit_cost, barcode, entry_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, product_id, quantity, unit_cost, barcode, entry_method))

        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date)
            VALUES (?, 'Inventory', ?, ?, ?)
        """, (vendor_id, total_cost, f"Inventory purchase - {product_name} ({quantity} units)", datetime.now().strftime("%Y-%m-%d")))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'debit', 'Inventory', ?, ?, 'Inventory')
        """, (vendor_id, total_cost, f"Inventory Purchase - {product_name} ({quantity} units)"))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'credit', 'Cash', ?, ?, 'Inventory Purchase')
        """, (vendor_id, total_cost, f"Payment for Inventory - {product_name}"))

        conn.commit()
        conn.close()
        flash(f"Successfully added {quantity} units of {product_name} to inventory.")
        return redirect(url_for("inventory_management"))

    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f"Error adding inventory: {str(e)}")
        return redirect(url_for("add_stock_page"))


@app.route('/erp/inventory/restock/<int:item_id>', methods=["GET", "POST"])
def restock_item(item_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("inventory_management"))
    vendor_id = vendor_result[0]

    c.execute("SELECT id, name, quantity, buy_price, barcode FROM products WHERE id=? AND vendor_id=?", (item_id, vendor_id))
    product = c.fetchone()
    if not product:
        conn.close()
        flash("Product not found")
        return redirect(url_for("inventory_management"))

    if request.method == "GET":
        conn.close()
        product_info = {
            "id": product[0],
            "name": product[1],
            "current_stock": product[2] or 0,
            "buy_price": product[3] or 0,
            "barcode": product[4] or ""
        }
        return render_template("restock_item.html", product=product_info)

    quantity = int(request.form.get("quantity", 0))
    unit_cost = float(request.form.get("unit_cost", 0))
    batch_name = request.form.get("batch_name", f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    notes = request.form.get("notes", "")

    if quantity <= 0 or unit_cost <= 0:
        conn.close()
        flash("Quantity and unit cost must be greater than zero")
        return redirect(url_for("restock_item", item_id=item_id))

    try:
        c.execute("UPDATE products SET quantity = quantity + ?, buy_price = ? WHERE id = ?",
                  (quantity, unit_cost, item_id))

        c.execute("""
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        """, (item_id, quantity, unit_cost, quantity))

        c.execute("""
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, batch_name, quantity, unit_cost, datetime.now().strftime("%Y-%m-%d")))

        c.execute("""
            INSERT INTO restock_log (vendor_id, product_id, quantity_added, unit_cost, barcode, entry_method)
            VALUES (?, ?, ?, ?, ?, 'manual_entry')
        """, (vendor_id, item_id, quantity, unit_cost, product[4] or ""))

        total_cost = quantity * unit_cost
        c.execute("""
            INSERT INTO expenses (vendor_id, category, amount, description, date)
            VALUES (?, 'Inventory', ?, ?, ?)
        """, (vendor_id, total_cost, f"Restock - {product[1]} ({quantity} units)", datetime.now().strftime("%Y-%m-%d")))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'debit', 'Inventory', ?, ?, 'Inventory')
        """, (vendor_id, total_cost, f"Restock - {product[1]} ({quantity} units)"))

        c.execute("""
            INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
            VALUES (?, 'credit', 'Cash', ?, ?, 'Inventory Purchase')
        """, (vendor_id, total_cost, f"Payment for Restock - {product[1]}"))

        conn.commit()
        conn.close()
        flash(f"Successfully restocked {quantity} units of {product[1]}.")
        return redirect(url_for("inventory_management"))

    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f"Error restocking: {str(e)}")
        return redirect(url_for("restock_item", item_id=item_id))


@app.route('/erp/inventory/transfer/<int:item_id>')
def transfer_item(item_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    return render_template("transfer_stock_placeholder.html", item_id=item_id)


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

def forecast_demand(vendor_id, product_id, conn):
    import numpy as np
    c = conn.cursor()

    c.execute("SELECT name, quantity FROM products WHERE id=? AND vendor_id=?", (product_id, vendor_id))
    prod = c.fetchone()
    if not prod:
        return None
    product_name = prod[0]
    current_stock = prod[1] or 0

    c.execute("""
        SELECT strftime('%Y-%m', sale_date) as month,
               SUM(quantity) as units,
               SUM(total_amount) as revenue
        FROM sales_log
        WHERE vendor_id=? AND product_id=?
        AND sale_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', sale_date)
        ORDER BY month ASC
    """, (vendor_id, product_id))
    monthly_data = c.fetchall()

    result = {
        "product_id": product_id,
        "product_name": product_name,
        "current_stock": current_stock,
        "monthly_sales": [],
    }

    if len(monthly_data) < 2:
        result["status"] = "insufficient_data"
        return result

    months = [row[0] for row in monthly_data]
    units = [row[1] or 0 for row in monthly_data]
    revenue = [row[2] or 0 for row in monthly_data]

    result["monthly_sales"] = [{"month": m, "units": u, "revenue": r} for m, u, r in zip(months, units, revenue)]

    x = np.arange(len(units), dtype=float)
    y = np.array(units, dtype=float)
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    intercept = coeffs[1]

    residuals = y - (slope * x + intercept)
    std_err = float(np.std(residuals)) if len(residuals) > 0 else 0

    current_month_num = datetime.now().month
    seasonal_factor = 1.0
    seasonal_warning = None

    same_month_sales = []
    for row in monthly_data:
        m_num = int(row[0].split("-")[1])
        if m_num == current_month_num:
            same_month_sales.append(row[1] or 0)

    avg_monthly = float(np.mean(y))
    if same_month_sales and avg_monthly > 0:
        same_month_avg = float(np.mean(same_month_sales))
        seasonal_factor = same_month_avg / avg_monthly if avg_monthly > 0 else 1.0
        if seasonal_factor > 1.3:
            seasonal_warning = "high"
        elif seasonal_factor < 0.7:
            seasonal_warning = "low"

    n = len(units)
    forecasts = {}
    for days, label in [(30, "30_day"), (60, "60_day"), (90, "90_day")]:
        future_months = days / 30.0
        future_x = n - 1 + future_months
        predicted = max(0, (slope * future_x + intercept) * seasonal_factor)
        upper = max(0, predicted + 1.5 * std_err)
        lower = max(0, predicted - 1.5 * std_err)
        forecasts[label] = {
            "predicted": round(predicted, 1),
            "upper": round(upper, 1),
            "lower": round(lower, 1)
        }

    avg_daily_sales = avg_monthly / 30.0 if avg_monthly > 0 else 0
    days_until_stockout = round(current_stock / avg_daily_sales, 1) if avg_daily_sales > 0 else 999

    reorder_qty = max(0, round(forecasts["60_day"]["predicted"] * 2 - current_stock))

    if slope > 0.5:
        trend = "growing"
    elif slope < -0.5:
        trend = "declining"
    else:
        trend = "stable"

    if n >= 6:
        confidence = "high"
    elif n >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    c.execute("""
        SELECT COALESCE(SUM(quantity), 0) FROM sales_log
        WHERE vendor_id=? AND product_id=?
        AND sale_date >= date('now', '-60 days')
    """, (vendor_id, product_id))
    recent_sales = c.fetchone()[0] or 0
    is_dead_stock = recent_sales == 0

    result.update({
        "status": "ok",
        "forecasts": forecasts,
        "days_until_stockout": days_until_stockout,
        "reorder_qty": reorder_qty,
        "trend": trend,
        "confidence": confidence,
        "is_dead_stock": is_dead_stock,
        "seasonal_warning": seasonal_warning,
        "seasonal_factor": round(seasonal_factor, 2),
        "avg_daily_sales": round(avg_daily_sales, 2),
        "avg_monthly_sales": round(avg_monthly, 1),
        "slope": round(slope, 3),
    })
    return result


@app.route('/erp/inventory/forecast')
def inventory_forecast():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("inventory_management"))
    vendor_id = vendor_result[0]

    c.execute("SELECT id FROM products WHERE vendor_id=? ORDER BY name", (vendor_id,))
    product_ids = [row[0] for row in c.fetchall()]

    needs_reorder = []
    dead_stock = []
    no_data = []
    healthy = []

    for pid in product_ids:
        forecast = forecast_demand(vendor_id, pid, conn)
        if not forecast:
            continue
        if forecast.get("status") == "insufficient_data":
            no_data.append(forecast)
        elif forecast.get("is_dead_stock"):
            dead_stock.append(forecast)
        elif forecast.get("days_until_stockout", 999) <= 30:
            needs_reorder.append(forecast)
        else:
            healthy.append(forecast)

    needs_reorder.sort(key=lambda x: x.get("days_until_stockout", 999))
    healthy.sort(key=lambda x: x.get("days_until_stockout", 999))

    conn.close()
    return render_template("inventory_forecast.html",
                         needs_reorder=needs_reorder,
                         dead_stock=dead_stock,
                         no_data=no_data,
                         healthy=healthy,
                         total_products=len(product_ids),
                         reorder_count=len(needs_reorder),
                         dead_count=len(dead_stock),
                         nodata_count=len(no_data))


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
                             inventory_summary={'total_products': 0, 'total_units': 0, 'total_value': 0, 'turnover_rate': 0},
                             inventory_alerts=[],
                             inventory_items=[],
                             chart_data={'labels': [], 'revenue_data': [], 'units_data': []})

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

    # Calculate real turnover rate from sales data
    c.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM sales_log
        WHERE vendor_id = ? AND sale_date >= date('now', '-365 days')
    """, (vendor_id,))
    annual_sales = c.fetchone()[0] or 0
    total_value = inventory_summary['total_value']
    inventory_summary['turnover_rate'] = round(annual_sales / total_value, 1) if total_value > 0 else 0.0

    # Chart data from real monthly sales
    c.execute("""
        SELECT strftime('%Y-%m', sale_date) as month,
               SUM(total_amount) as revenue,
               SUM(quantity) as units
        FROM sales_log
        WHERE vendor_id = ?
        AND sale_date >= date('now', '-6 months')
        GROUP BY strftime('%Y-%m', sale_date)
        ORDER BY month ASC
    """, (vendor_id,))
    monthly_sales = c.fetchall()

    chart_data = {
        'labels': [row[0] for row in monthly_sales] if monthly_sales else [],
        'revenue_data': [round(row[1] or 0, 2) for row in monthly_sales] if monthly_sales else [],
        'units_data': [row[2] or 0 for row in monthly_sales] if monthly_sales else []
    }

    conn.close()
    return render_template("inventory_management.html",
                         inventory_summary=inventory_summary,
                         inventory_alerts=inventory_alerts,
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
        result = inventory_bot.process_query(query, vendor_email)
        
        if isinstance(result, dict):
            return {
                "response": result.get('response', 'No response generated.'),
                "intent": result.get('intent', 'processed'),
                "confidence": result.get('confidence', 0.8),
                "session_id": result.get('session_id', session_id or "default"),
                "log_id": result.get('log_id'),
                "data": result.get('data', {})
            }
        else:
            return {
                "response": str(result),
                "intent": "processed",
                "confidence": 0.8,
                "session_id": session_id or "default",
                "log_id": None
            }
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/erp/inventory-bot/feedback', methods=["POST"])
def inventory_bot_feedback():
    if "vendor" not in session:
        return {"error": "Unauthorized"}, 401
    
    vendor_email = session["vendor"]
    data = request.get_json()
    log_id = data.get("log_id")
    feedback = data.get("feedback")
    
    if log_id is None or feedback is None:
        return {"error": "log_id and feedback are required"}, 400
    
    try:
        if hasattr(inventory_bot, 'smart_bot'):
            inventory_bot.smart_bot.logger.update_feedback(log_id, feedback, vendor_email=vendor_email)
            return {"success": True}
        else:
            return {"success": False, "error": "Smart bot not available"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/erp/inventory-bot/analytics')
def inventory_bot_analytics():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    
    vendor_email = session["vendor"]
    try:
        if hasattr(inventory_bot, 'smart_bot'):
            analytics = inventory_bot.smart_bot.get_analytics_dashboard(vendor_email=vendor_email)
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

# ---- VENDOR SERVICE MANAGEMENT ROUTES ----

@app.route('/erp/services')
def vendor_services():
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
        return render_template("vendor_services.html", services=[])

    vendor_id = vendor_result[0]

    # Get all services for this vendor
    c.execute("""
        SELECT id, service_name, description, price, duration_minutes, category, is_active, created_at
        FROM vendor_services 
        WHERE vendor_id = ?
        ORDER BY service_name
    """, (vendor_id,))
    
    services = c.fetchall()
    conn.close()

    return render_template("vendor_services.html", services=services)

@app.route('/erp/services/add', methods=["GET", "POST"])
def add_vendor_service():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    if request.method == "POST":
        email = session["vendor"]
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()

        # Get vendor ID
        c.execute("SELECT id FROM vendors WHERE email=?", (email,))
        vendor_result = c.fetchone()

        if not vendor_result:
            conn.close()
            flash("Vendor not found")
            return redirect(url_for("vendor_services"))

        vendor_id = vendor_result[0]

        # Get form data
        service_name = request.form.get("service_name")
        description = request.form.get("description", "")
        price = float(request.form.get("price", 0))
        duration_minutes = int(request.form.get("duration_minutes", 60))
        category = request.form.get("category", "General")

        if not service_name or price <= 0:
            flash("Service name and valid price are required")
            return redirect(url_for("add_vendor_service"))

        # Insert new service
        c.execute("""
            INSERT INTO vendor_services (vendor_id, service_name, description, price, duration_minutes, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, service_name, description, price, duration_minutes, category))

        conn.commit()
        conn.close()

        flash(f"Service '{service_name}' added successfully!")
        return redirect(url_for("vendor_services"))

    return render_template("add_vendor_service.html")

@app.route('/erp/services/edit/<int:service_id>', methods=["GET", "POST"])
def edit_vendor_service(service_id):
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
        return redirect(url_for("vendor_services"))

    vendor_id = vendor_result[0]

    if request.method == "POST":
        # Update service
        service_name = request.form.get("service_name")
        description = request.form.get("description", "")
        price = float(request.form.get("price", 0))
        duration_minutes = int(request.form.get("duration_minutes", 60))
        category = request.form.get("category", "General")
        is_active = 1 if request.form.get("is_active") else 0

        c.execute("""
            UPDATE vendor_services 
            SET service_name=?, description=?, price=?, duration_minutes=?, category=?, is_active=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND vendor_id=?
        """, (service_name, description, price, duration_minutes, category, is_active, service_id, vendor_id))

        conn.commit()
        conn.close()

        flash("Service updated successfully!")
        return redirect(url_for("vendor_services"))

    # Get service details
    c.execute("""
        SELECT id, service_name, description, price, duration_minutes, category, is_active
        FROM vendor_services 
        WHERE id=? AND vendor_id=?
    """, (service_id, vendor_id))
    
    service = c.fetchone()
    conn.close()

    if not service:
        flash("Service not found")
        return redirect(url_for("vendor_services"))

    return render_template("edit_vendor_service.html", service=service)

@app.route('/erp/services/delete/<int:service_id>', methods=["POST"])
def delete_vendor_service(service_id):
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
        return redirect(url_for("vendor_services"))

    vendor_id = vendor_result[0]

    # Delete service
    c.execute("DELETE FROM vendor_services WHERE id=? AND vendor_id=?", (service_id, vendor_id))
    conn.commit()
    conn.close()

    flash("Service deleted successfully!")
    return redirect(url_for("vendor_services"))

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
    }, to=f'conversation_{conversation_id}')
    
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

@app.route('/erp/finance/accounts-receivable', methods=["GET", "POST"])
def accounts_receivable():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("accounts_receivable.html", receivables=[], ar_summary={}, payments=[])

    vendor_id = result["id"]

    if request.method == "POST":
        payer_name = request.form.get("payer_name", "")
        payer_email = request.form.get("payer_email", "")
        description = request.form.get("description", "")
        amount = float(request.form.get("amount", 0))
        due_date = request.form.get("due_date", "")

        if payer_name and amount > 0:
            c.execute("""
                INSERT INTO receivable_entries (vendor_id, payer_name, payer_email, description, amount, balance_due, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vendor_id, payer_name, payer_email, description, amount, amount, due_date))

            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
                VALUES (?, 'debit', 'Accounts Receivable', ?, ?, 'Invoice', 'auto', ?)
            """, (vendor_id, amount, f"AR: {payer_name} - {description}", due_date or datetime.now().strftime("%Y-%m-%d")))

            conn.commit()
        return redirect(url_for("accounts_receivable"))

    c.execute("SELECT * FROM receivable_entries WHERE vendor_id=? ORDER BY created_at DESC", (vendor_id,))
    receivables = c.fetchall()

    c.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN status != 'paid' THEN balance_due ELSE 0 END), 0) as total_outstanding,
            COUNT(CASE WHEN status != 'paid' THEN 1 END) as unpaid_count,
            COUNT(CASE WHEN status != 'paid' AND due_date < date('now') AND due_date != '' THEN 1 END) as overdue_count
        FROM receivable_entries WHERE vendor_id=?
    """, (vendor_id,))
    ar_summary = c.fetchone()

    c.execute("""
        SELECT pr.*, re.payer_name FROM payment_records pr
        LEFT JOIN receivable_entries re ON pr.entry_id = re.id
        WHERE pr.vendor_id=? AND pr.entry_type='receivable'
        ORDER BY pr.created_at DESC LIMIT 20
    """, (vendor_id,))
    payments = c.fetchall()

    conn.close()
    return render_template("accounts_receivable.html",
                         receivables=receivables,
                         ar_summary=ar_summary,
                         payments=payments)


@app.route('/erp/finance/receivable/pay/<int:entry_id>', methods=["POST"])
def receivable_pay(entry_id):
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect(url_for("accounts_receivable"))
    vendor_id = result[0]

    c.execute("SELECT amount, amount_received, balance_due FROM receivable_entries WHERE id=? AND vendor_id=?", (entry_id, vendor_id))
    entry = c.fetchone()
    if not entry:
        conn.close()
        return redirect(url_for("accounts_receivable"))

    pay_amount = float(request.form.get("amount", 0))
    payment_method = request.form.get("payment_method", "Cash")
    payment_date = request.form.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
    reference_number = request.form.get("reference_number", "")
    notes = request.form.get("notes", "")

    if pay_amount <= 0:
        conn.close()
        return redirect(url_for("accounts_receivable"))

    new_received = (entry[1] or 0) + pay_amount
    new_balance = entry[0] - new_received
    if new_balance < 0:
        new_balance = 0
    new_status = "paid" if new_balance == 0 else "partial"

    c.execute("INSERT INTO payment_records (vendor_id, entry_type, entry_id, amount, payment_method, payment_date, reference_number, notes) VALUES (?, 'receivable', ?, ?, ?, ?, ?, ?)",
              (vendor_id, entry_id, pay_amount, payment_method, payment_date, reference_number, notes))

    c.execute("UPDATE receivable_entries SET amount_received=?, balance_due=?, status=? WHERE id=? AND vendor_id=?",
              (new_received, new_balance, new_status, entry_id, vendor_id))

    cash_account = "Bank" if payment_method in ("Bank Transfer", "Cheque") else "Cash"
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
        VALUES (?, 'debit', ?, ?, ?, 'Payment Received', 'auto', ?)
    """, (vendor_id, cash_account, pay_amount, f"Payment received via {payment_method} [Ref: {reference_number}]", payment_date))
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
        VALUES (?, 'credit', 'Accounts Receivable', ?, ?, 'Payment Received', 'auto', ?)
    """, (vendor_id, pay_amount, f"AR payment received via {payment_method} [Ref: {reference_number}]", payment_date))

    conn.commit()
    conn.close()
    return redirect(url_for("accounts_receivable"))


@app.route('/erp/finance/accounts-payable', methods=["GET", "POST"])
def accounts_payable():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return render_template("accounts_payable.html", payables=[], ap_summary={}, payments=[])

    vendor_id = result["id"]

    if request.method == "POST":
        payee_name = request.form.get("payee_name", "")
        description = request.form.get("description", "")
        amount = float(request.form.get("amount", 0))
        due_date = request.form.get("due_date", "")
        category = request.form.get("category", "Other")

        if payee_name and amount > 0:
            c.execute("""
                INSERT INTO payable_entries (vendor_id, payee_name, description, amount, balance_due, due_date, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vendor_id, payee_name, description, amount, amount, due_date, category))

            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
                VALUES (?, 'debit', 'Accounts Payable', ?, ?, 'Bill', 'auto', ?)
            """, (vendor_id, amount, f"AP: {payee_name} - {description}", due_date or datetime.now().strftime("%Y-%m-%d")))

            conn.commit()
        return redirect(url_for("accounts_payable"))

    c.execute("SELECT * FROM payable_entries WHERE vendor_id=? ORDER BY created_at DESC", (vendor_id,))
    payables = c.fetchall()

    c.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN status != 'paid' THEN balance_due ELSE 0 END), 0) as total_outstanding,
            COUNT(CASE WHEN status != 'paid' THEN 1 END) as unpaid_count,
            COUNT(CASE WHEN status != 'paid' AND due_date < date('now') AND due_date != '' THEN 1 END) as overdue_count
        FROM payable_entries WHERE vendor_id=?
    """, (vendor_id,))
    ap_summary = c.fetchone()

    c.execute("""
        SELECT pr.*, pe.payee_name FROM payment_records pr
        LEFT JOIN payable_entries pe ON pr.entry_id = pe.id
        WHERE pr.vendor_id=? AND pr.entry_type='payable'
        ORDER BY pr.created_at DESC LIMIT 20
    """, (vendor_id,))
    payments = c.fetchall()

    conn.close()
    return render_template("accounts_payable.html",
                         payables=payables,
                         ap_summary=ap_summary,
                         payments=payments)


@app.route('/erp/finance/payable/pay/<int:entry_id>', methods=["POST"])
def payable_pay(entry_id):
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect(url_for("accounts_payable"))
    vendor_id = result[0]

    c.execute("SELECT amount, amount_paid, balance_due FROM payable_entries WHERE id=? AND vendor_id=?", (entry_id, vendor_id))
    entry = c.fetchone()
    if not entry:
        conn.close()
        return redirect(url_for("accounts_payable"))

    pay_amount = float(request.form.get("amount", 0))
    payment_method = request.form.get("payment_method", "Cash")
    payment_date = request.form.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
    reference_number = request.form.get("reference_number", "")
    notes = request.form.get("notes", "")

    if pay_amount <= 0:
        conn.close()
        return redirect(url_for("accounts_payable"))

    new_paid = (entry[1] or 0) + pay_amount
    new_balance = entry[0] - new_paid
    if new_balance < 0:
        new_balance = 0
    new_status = "paid" if new_balance == 0 else "partial"

    c.execute("INSERT INTO payment_records (vendor_id, entry_type, entry_id, amount, payment_method, payment_date, reference_number, notes) VALUES (?, 'payable', ?, ?, ?, ?, ?, ?)",
              (vendor_id, entry_id, pay_amount, payment_method, payment_date, reference_number, notes))

    c.execute("UPDATE payable_entries SET amount_paid=?, balance_due=?, status=? WHERE id=? AND vendor_id=?",
              (new_paid, new_balance, new_status, entry_id, vendor_id))

    cash_account = "Bank" if payment_method in ("Bank Transfer", "Cheque") else "Cash"
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
        VALUES (?, 'debit', 'Accounts Payable', ?, ?, 'Payment Made', 'auto', ?)
    """, (vendor_id, pay_amount, f"AP payment via {payment_method} [Ref: {reference_number}]", payment_date))
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category, entry_source, timestamp)
        VALUES (?, 'credit', ?, ?, ?, 'Payment Made', 'auto', ?)
    """, (vendor_id, cash_account, pay_amount, f"Payment to payable via {payment_method} [Ref: {reference_number}]", payment_date))

    conn.commit()
    conn.close()
    return redirect(url_for("accounts_payable"))

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

    # Fixed Assets from fixed_assets table
    c.execute("SELECT COALESCE(SUM(current_value), 0) FROM fixed_assets WHERE vendor_id=?", (vendor_id,))
    fixed_assets = c.fetchone()[0] or 0

    total_assets = current_assets + fixed_assets

    # Accounts Payable from ledger
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM ledger_entries
        WHERE vendor_id=? AND account='Accounts Payable' AND entry_type='credit'
        AND (sub_category IS NULL OR sub_category != 'Long Term')
    """, (vendor_id,))
    ap_credits = c.fetchone()[0] or 0
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM ledger_entries
        WHERE vendor_id=? AND account='Accounts Payable' AND entry_type='debit'
        AND (sub_category IS NULL OR sub_category != 'Long Term')
    """, (vendor_id,))
    ap_debits = c.fetchone()[0] or 0
    accounts_payable = ap_credits - ap_debits

    current_liabilities = accounts_payable

    # Long-term Debt from ledger
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM ledger_entries
        WHERE vendor_id=? AND account='Accounts Payable' AND sub_category='Long Term' AND entry_type='credit'
    """, (vendor_id,))
    lt_credits = c.fetchone()[0] or 0
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM ledger_entries
        WHERE vendor_id=? AND account='Accounts Payable' AND sub_category='Long Term' AND entry_type='debit'
    """, (vendor_id,))
    lt_debits = c.fetchone()[0] or 0
    long_term_debt = lt_credits - lt_debits

    total_liabilities = current_liabilities + long_term_debt

    # Owner's Equity from capital_accounts
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_accounts WHERE vendor_id=?", (vendor_id,))
    owner_equity = c.fetchone()[0] or 0

    retained_earnings = total_assets - total_liabilities - owner_equity
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

    # Investing Activities from fixed_assets purchases this period
    c.execute("""
        SELECT COALESCE(SUM(purchase_value), 0) FROM fixed_assets
        WHERE vendor_id=? AND purchase_date >= date('now', '-30 days')
    """, (vendor_id,))
    equipment_purchases = c.fetchone()[0] or 0
    investing_cash_flow = -equipment_purchases

    # Financing Activities from capital_accounts this period
    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM capital_accounts
        WHERE vendor_id=? AND entry_date >= date('now', '-30 days')
    """, (vendor_id,))
    financing_cash_flow = c.fetchone()[0] or 0

    net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow

    # Beginning cash = all-time sales - all-time expenses - all-time asset purchases + all-time capital, minus this period
    c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_log WHERE vendor_id=? AND sale_date < date('now', '-30 days')", (vendor_id,))
    prior_sales = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE vendor_id=? AND date < date('now', '-30 days')", (vendor_id,))
    prior_expenses = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(purchase_value), 0) FROM fixed_assets WHERE vendor_id=? AND purchase_date < date('now', '-30 days')", (vendor_id,))
    prior_assets = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_accounts WHERE vendor_id=? AND entry_date < date('now', '-30 days')", (vendor_id,))
    prior_capital = c.fetchone()[0] or 0
    beginning_cash = prior_sales - prior_expenses - prior_assets + prior_capital

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
        'beginning_cash': beginning_cash,
        'ending_cash': beginning_cash + net_cash_flow
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


@app.route('/erp/finance/board-report')
def board_report():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id, name, city, category FROM vendors WHERE email=?", (email,))
    vendor_row = c.fetchone()
    if not vendor_row:
        conn.close()
        return redirect(url_for("erp_dashboard"))

    vendor_id = vendor_row[0]
    vendor_name = vendor_row[1] or email
    vendor_city = vendor_row[2] or ""
    vendor_category = vendor_row[3] or ""

    from datetime import datetime, timedelta
    import calendar
    now = datetime.now()
    this_month_start = now.replace(day=1).strftime("%Y-%m-01")
    this_month_end = now.strftime("%Y-%m-%d 23:59:59")
    last_month_end = (now.replace(day=1) - timedelta(days=1))
    last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-01")
    last_month_end_str = last_month_end.strftime("%Y-%m-%d 23:59:59")
    current_month_name = now.strftime("%B")
    last_month_name = (now.replace(day=1) - timedelta(days=1)).strftime("%B")

    currency = get_vendor_currency(vendor_id)

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, this_month_start, this_month_end))
    revenue_this = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, last_month_start, last_month_end_str))
    revenue_last = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, this_month_start, this_month_end))
    expenses_this = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, last_month_start, last_month_end_str))
    expenses_last = c.fetchone()[0] or 0

    cogs_this = 0
    try:
        c.execute("SELECT COALESCE(SUM(s.quantity * p.buy_price),0) FROM sales_log s JOIN products p ON s.product_id=p.id WHERE s.vendor_id=? AND s.sale_date>=? AND s.sale_date<=?", (vendor_id, this_month_start, this_month_end))
        cogs_this = c.fetchone()[0] or 0
    except:
        pass
    cogs_last = 0
    try:
        c.execute("SELECT COALESCE(SUM(s.quantity * p.buy_price),0) FROM sales_log s JOIN products p ON s.product_id=p.id WHERE s.vendor_id=? AND s.sale_date>=? AND s.sale_date<=?", (vendor_id, last_month_start, last_month_end_str))
        cogs_last = c.fetchone()[0] or 0
    except:
        pass

    gross_this = revenue_this - cogs_this
    gross_last = revenue_last - cogs_last
    net_this = revenue_this - expenses_this
    net_last = revenue_last - expenses_last

    def pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / abs(previous)) * 100

    month_labels = []
    month_revenues = []
    for i in range(5, -1, -1):
        d_ref = now.replace(day=1) - timedelta(days=1)
        for _ in range(i):
            d_ref = d_ref.replace(day=1) - timedelta(days=1)
        m_start = d_ref.replace(day=1) if i > 0 else now.replace(day=1)
        m_name = m_start.strftime("%b %Y")
        m_start_str = m_start.strftime("%Y-%m-01")
        last_day = calendar.monthrange(m_start.year, m_start.month)[1]
        m_end_str = m_start.strftime(f"%Y-%m-{last_day:02d}") + " 23:59:59"
        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, m_start_str, m_end_str))
        month_labels.append(m_name)
        month_revenues.append(round(c.fetchone()[0] or 0, 2))

    c.execute("SELECT p.name, SUM(s.total_amount), SUM(s.quantity) FROM sales_log s JOIN products p ON s.product_id=p.id WHERE s.vendor_id=? AND s.sale_date>=? AND s.sale_date<=? GROUP BY p.name ORDER BY SUM(s.total_amount) DESC LIMIT 5", (vendor_id, this_month_start, this_month_end))
    top_products_raw = c.fetchall()
    top_products = []
    total_product_rev = revenue_this if revenue_this > 0 else 1
    top_products_total = 0
    for tp in top_products_raw:
        pct = (tp[1] / total_product_rev * 100) if total_product_rev > 0 else 0
        top_products.append((tp[0], tp[1], tp[2], round(pct, 1)))
        top_products_total += tp[1]
    top_products_pct = (top_products_total / total_product_rev * 100) if total_product_rev > 0 else 0

    c.execute("SELECT service, COUNT(*), 0, 0 FROM bookings WHERE vendor_id=? AND date>=? AND date<=? GROUP BY service ORDER BY COUNT(*) DESC LIMIT 3", (vendor_id, this_month_start, this_month_end))
    top_services = c.fetchall()
    top_services_list = []
    for ts in top_services:
        avg_val = 0
        total_val = 0
        top_services_list.append((ts[0], ts[1], avg_val, total_val))

    c.execute("SELECT category, SUM(amount) FROM expenses WHERE vendor_id=? AND date>=? AND date<=? GROUP BY category ORDER BY SUM(amount) DESC", (vendor_id, this_month_start, this_month_end))
    expense_categories = c.fetchall()

    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id=?", (vendor_id,))
    total_customers = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id=? AND created_at>=?", (vendor_id, this_month_start))
    new_customers = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, this_month_start, this_month_end))
    bookings_this = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, last_month_start, last_month_end_str))
    bookings_last = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, this_month_start, this_month_end))
    orders_this = c.fetchone()[0] or 0

    avg_order = (revenue_this / orders_this) if orders_this > 0 else 0

    c.execute("SELECT COALESCE(SUM(quantity * sale_price),0), COUNT(*) FROM products WHERE vendor_id=?", (vendor_id,))
    inv_row = c.fetchone()
    inventory_value = inv_row[0] or 0
    sku_count = inv_row[1] or 0

    c.execute("SELECT COUNT(*) FROM products WHERE vendor_id=? AND quantity<=5 AND quantity>0", (vendor_id,))
    low_stock = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM receivable_entries WHERE vendor_id=? AND status!='Paid'", (vendor_id,))
    outstanding_recv = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(balance_due),0) FROM payable_entries WHERE vendor_id=? AND status!='Paid'", (vendor_id,))
    outstanding_pay = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM employees WHERE vendor_id=? AND status='Active'", (vendor_id,))
    emp_count = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(base_salary),0) FROM employees WHERE vendor_id=? AND status='Active'", (vendor_id,))
    payroll_cost = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id=? AND date>? AND status IN ('confirmed','pending','Confirmed','Pending')", (vendor_id, now.strftime("%Y-%m-%d")))
    pending_bookings = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(AVG(rating),0) FROM reviews WHERE vendor_id=?", (vendor_id,))
    avg_rating = c.fetchone()[0] or 0

    cash_balance = revenue_this - expenses_this
    try:
        c.execute("SELECT COALESCE(SUM(CASE WHEN entry_type='debit' AND account='Cash/Bank' THEN amount ELSE 0 END) - SUM(CASE WHEN entry_type='credit' AND account='Cash/Bank' THEN amount ELSE 0 END),0) FROM ledger_entries WHERE vendor_id=?", (vendor_id,))
        cash_balance = c.fetchone()[0] or 0
    except:
        pass

    total_assets = cash_balance + outstanding_recv + inventory_value
    net_position = total_assets - outstanding_pay

    gross_margin = (gross_this / revenue_this * 100) if revenue_this > 0 else 0
    net_margin = (net_this / revenue_this * 100) if revenue_this > 0 else 0
    inv_turnover = (cogs_this / inventory_value) if inventory_value > 0 else 0

    conn.close()

    d = {
        'vendor_name': vendor_name,
        'vendor_city': vendor_city,
        'vendor_category': vendor_category,
        'currency': currency,
        'current_month_name': current_month_name,
        'last_month_name': last_month_name,
        'current_year': now.strftime("%Y"),
        'generated_at': now.strftime("%d %B %Y, %I:%M %p"),
        'generated_date': now.strftime("%d %B %Y"),
        'revenue_this_month': revenue_this,
        'revenue_last_month': revenue_last,
        'revenue_change_pct': pct_change(revenue_this, revenue_last),
        'expenses_this_month': expenses_this,
        'expenses_last_month': expenses_last,
        'expense_change_pct': pct_change(expenses_this, expenses_last),
        'gross_profit_this_month': gross_this,
        'gross_profit_last_month': gross_last,
        'gross_profit_change_pct': pct_change(gross_this, gross_last),
        'net_profit_this_month': net_this,
        'net_profit_last_month': net_last,
        'net_profit_change_pct': pct_change(net_this, net_last),
        'gross_margin_pct': gross_margin,
        'net_margin_pct': net_margin,
        'month_labels': month_labels,
        'month_revenues': month_revenues,
        'top_products': top_products,
        'top_products_total': top_products_total,
        'top_products_pct': round(top_products_pct, 1),
        'top_services': top_services_list,
        'total_bookings_this_month': bookings_this,
        'expense_categories': expense_categories,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'bookings_this_month': bookings_this,
        'bookings_last_month': bookings_last,
        'orders_this_month': orders_this,
        'avg_order_value': avg_order,
        'inventory_value': inventory_value,
        'sku_count': sku_count,
        'low_stock_count': low_stock,
        'outstanding_receivables': outstanding_recv,
        'outstanding_payables': outstanding_pay,
        'employee_count': emp_count,
        'payroll_cost': payroll_cost,
        'pending_bookings': pending_bookings,
        'avg_rating': avg_rating,
        'cash_balance': cash_balance,
        'total_assets': total_assets,
        'net_position': net_position,
        'inventory_turnover': inv_turnover,
    }

    return render_template("board_report.html", d=d)


@app.route('/erp/finance/budget', methods=["GET", "POST"])
def budget_planning():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect(url_for("erp_dashboard"))

    vendor_id = result[0]

    from datetime import datetime
    now = datetime.now()
    this_month_start = now.strftime("%Y-%m-01")
    this_month_end = now.strftime("%Y-%m-%d 23:59:59")

    budget_categories = [
        ("Inventory", "inventory"),
        ("Salaries", "salaries"),
        ("Rent", "rent"),
        ("Utilities", "utilities"),
        ("Marketing", "marketing"),
        ("Equipment", "equipment"),
        ("Maintenance", "maintenance"),
        ("Other", "other"),
    ]

    if request.method == "POST":
        revenue_target = float(request.form.get("revenue_target", 0) or 0)
        c.execute("INSERT OR REPLACE INTO expense_budgets (id, vendor_id, category, monthly_budget) VALUES ((SELECT id FROM expense_budgets WHERE vendor_id=? AND category='revenue_target'), ?, 'revenue_target', ?)", (vendor_id, vendor_id, revenue_target))

        for name, key in budget_categories:
            budget_val = float(request.form.get(f"budget_{key}", 0) or 0)
            c.execute("INSERT OR REPLACE INTO expense_budgets (id, vendor_id, category, monthly_budget) VALUES ((SELECT id FROM expense_budgets WHERE vendor_id=? AND category=?), ?, ?, ?)", (vendor_id, key, vendor_id, key, budget_val))

        conn.commit()
        conn.close()
        flash("All budgets saved successfully!")
        return redirect(url_for("budget_planning"))

    c.execute("SELECT category, monthly_budget FROM expense_budgets WHERE vendor_id=?", (vendor_id,))
    existing_budgets = {row[0]: row[1] for row in c.fetchall()}

    revenue_target = existing_budgets.get("revenue_target", 0)

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, this_month_start, this_month_end))
    actual_revenue = c.fetchone()[0] or 0

    categories = []
    total_budget = 0
    total_actual = 0
    for name, key in budget_categories:
        budget = existing_budgets.get(key, 0)
        c.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE vendor_id=? AND LOWER(category) LIKE ? AND date>=? AND date<=?", (vendor_id, f"%{key}%", this_month_start, this_month_end))
        actual = c.fetchone()[0] or 0
        variance = budget - actual
        categories.append({
            'name': name,
            'key': key,
            'budget': budget,
            'actual': actual,
            'variance': variance,
        })
        total_budget += budget
        total_actual += actual

    total_variance = total_budget - total_actual
    conn.close()

    return render_template("budget_planning.html",
        categories=categories,
        total_budget=total_budget,
        total_actual=total_actual,
        total_variance=total_variance,
        revenue_target=revenue_target,
        actual_revenue=actual_revenue)


@app.route('/erp/finance/kpi-dashboard')
def kpi_dashboard():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect(url_for("erp_dashboard"))

    vendor_id = result[0]
    currency = get_vendor_currency(vendor_id)

    c.execute("CREATE TABLE IF NOT EXISTS vendor_kpis (id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id INTEGER, kpi_name TEXT, kpi_target REAL, is_active BOOLEAN DEFAULT 1, display_order INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (vendor_id) REFERENCES vendors(id))")
    conn.commit()

    from datetime import datetime, timedelta
    now = datetime.now()
    this_month_start = now.strftime("%Y-%m-01")
    this_month_end = now.strftime("%Y-%m-%d 23:59:59")
    last_month_end = now.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-01")
    last_month_end_str = last_month_end.strftime("%Y-%m-%d 23:59:59")

    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, this_month_start, this_month_end))
    rev_this = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, last_month_start, last_month_end_str))
    rev_last = c.fetchone()[0] or 0

    c.execute("SELECT monthly_budget FROM expense_budgets WHERE vendor_id=? AND category='revenue_target'", (vendor_id,))
    rev_target_row = c.fetchone()
    rev_target = rev_target_row[0] if rev_target_row else rev_last * 1.1 if rev_last > 0 else 10000

    rev_growth = ((rev_this - rev_last) / abs(rev_last) * 100) if rev_last != 0 else (100 if rev_this > 0 else 0)

    cogs = 0
    try:
        c.execute("SELECT COALESCE(SUM(s.quantity * p.buy_price),0) FROM sales_log s JOIN products p ON s.product_id=p.id WHERE s.vendor_id=? AND s.sale_date>=? AND s.sale_date<=?", (vendor_id, this_month_start, this_month_end))
        cogs = c.fetchone()[0] or 0
    except:
        pass
    gross_margin = ((rev_this - cogs) / rev_this * 100) if rev_this > 0 else 0

    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id=? AND created_at>=?", (vendor_id, this_month_start))
    new_cust = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id=? AND created_at>=? AND created_at<=?", (vendor_id, last_month_start, last_month_end_str))
    new_cust_last = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, this_month_start, this_month_end))
    order_count = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM sales_log WHERE vendor_id=? AND sale_date>=? AND sale_date<=?", (vendor_id, last_month_start, last_month_end_str))
    order_count_last = c.fetchone()[0] or 0
    aov = rev_this / order_count if order_count > 0 else 0
    aov_last = rev_last / order_count_last if order_count_last > 0 else 0

    inv_value = 0
    try:
        c.execute("SELECT COALESCE(SUM(quantity * sale_price),0) FROM products WHERE vendor_id=?", (vendor_id,))
        inv_value = c.fetchone()[0] or 0
    except:
        pass
    inv_turnover = (cogs / inv_value) if inv_value > 0 else 0

    c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, this_month_start, this_month_end))
    bookings_this = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM bookings WHERE vendor_id=? AND date>=? AND date<=?", (vendor_id, last_month_start, last_month_end_str))
    bookings_last = c.fetchone()[0] or 0

    c.execute("SELECT COALESCE(AVG(rating),0) FROM reviews WHERE vendor_id=?", (vendor_id,))
    avg_rating = c.fetchone()[0] or 0

    total_products = 0
    dead_stock = 0
    try:
        c.execute("SELECT COUNT(*) FROM products WHERE vendor_id=?", (vendor_id,))
        total_products = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM products WHERE vendor_id=? AND id NOT IN (SELECT DISTINCT product_id FROM sales_log WHERE vendor_id=?)", (vendor_id, vendor_id))
        dead_stock = c.fetchone()[0] or 0
    except:
        pass
    dead_stock_pct = (dead_stock / total_products * 100) if total_products > 0 else 0

    staff_prod = 0
    try:
        c.execute("SELECT COALESCE(AVG(productivity_score),0) FROM employee_performance WHERE vendor_id=?", (vendor_id,))
        staff_prod = c.fetchone()[0] or 0
    except:
        pass

    def make_kpi(name, value, target, last_val, fmt, suffix=""):
        if target == 0:
            gap = 0
        else:
            gap = abs(value - target) / abs(target) * 100

        if fmt == "currency":
            dv = f"{currency}{value:,.2f}"
            dt = f"{currency}{target:,.2f}"
        elif fmt == "percentage":
            dv = f"{value:.1f}%"
            dt = f"{target:.1f}%"
        elif fmt == "decimal":
            dv = f"{value:.1f}{suffix}"
            dt = f"{target:.1f}{suffix}"
        else:
            dv = f"{int(value)}"
            dt = f"{int(target)}"

        if gap <= 10:
            status_class = "on-target"
            status_badge = "status-on-target"
            status_label = "On Target"
        elif gap <= 25:
            status_class = "at-risk"
            status_badge = "status-at-risk"
            status_label = "At Risk"
        else:
            status_class = "off-track"
            status_badge = "status-off-track"
            status_label = "Off Track"

        if value > last_val:
            trend_class = "trend-up"
            trend_icon = "&#9650;"
            trend_text = "Up"
        elif value < last_val:
            trend_class = "trend-down"
            trend_icon = "&#9660;"
            trend_text = "Down"
        else:
            trend_class = "trend-flat"
            trend_icon = "&#9644;"
            trend_text = "Flat"

        return {
            'name': name,
            'value': value,
            'display_value': dv,
            'display_target': dt,
            'status_class': status_class,
            'status_badge': status_badge,
            'status_label': status_label,
            'trend_class': trend_class,
            'trend_icon': trend_icon,
            'trend_text': trend_text,
        }

    gross_margin_last = ((rev_last - cogs) / rev_last * 100) if rev_last > 0 else 0

    kpis = [
        make_kpi("Monthly Revenue", rev_this, rev_target, rev_last, "currency"),
        make_kpi("Revenue Growth %", rev_growth, 10, 0, "percentage"),
        make_kpi("Gross Margin %", gross_margin, 40, gross_margin_last, "percentage"),
        make_kpi("New Customers This Month", new_cust, 10, new_cust_last, "number"),
        make_kpi("Average Order Value", aov, aov_last if aov_last > 0 else aov, aov_last, "currency"),
        make_kpi("Inventory Turnover Rate", inv_turnover, 2.0, 0, "decimal", "x"),
        make_kpi("Booking Count This Month", bookings_this, 20, bookings_last, "number"),
        make_kpi("Customer Rating Average", avg_rating, 4.5, avg_rating, "decimal", "/5"),
        make_kpi("Dead Stock Percentage", dead_stock_pct, 10, dead_stock_pct, "percentage"),
        make_kpi("Staff Productivity Score", staff_prod, 80, staff_prod, "number"),
    ]

    on_target = sum(1 for k in kpis if k['status_class'] == 'on-target')
    health_pct = int((on_target / len(kpis)) * 100) if kpis else 0

    c.execute("SELECT id, kpi_name, kpi_target FROM vendor_kpis WHERE vendor_id=? AND is_active=1 ORDER BY display_order", (vendor_id,))
    custom_kpis = [{'id': r[0], 'kpi_name': r[1], 'kpi_target': r[2]} for r in c.fetchall()]

    all_additional = [
        "Return on Investment", "Customer Lifetime Value", "Repeat Customer Rate",
        "Employee Attendance Rate", "Revenue per Employee", "Cost per Acquisition",
        "Refund Rate", "On-Time Delivery Rate", "Social Media Followers", "WhatsApp Response Rate"
    ]
    active_names = {ck['kpi_name'] for ck in custom_kpis}
    available_kpis = [k for k in all_additional if k not in active_names]

    conn.close()

    return render_template("kpi_dashboard.html",
        kpis=kpis,
        health_pct=health_pct,
        on_target_count=on_target,
        custom_kpis=custom_kpis,
        available_kpis=available_kpis)


@app.route('/erp/finance/kpi-dashboard/add-kpi', methods=["POST"])
def kpi_add():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect(url_for("kpi_dashboard"))

    vendor_id = result[0]
    kpi_name = request.form.get("kpi_name", "").strip()
    kpi_target = float(request.form.get("kpi_target", 0) or 0)

    if kpi_name:
        c.execute("CREATE TABLE IF NOT EXISTS vendor_kpis (id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id INTEGER, kpi_name TEXT, kpi_target REAL, is_active BOOLEAN DEFAULT 1, display_order INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (vendor_id) REFERENCES vendors(id))")
        c.execute("SELECT id FROM vendor_kpis WHERE vendor_id=? AND kpi_name=?", (vendor_id, kpi_name))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE vendor_kpis SET is_active=1, kpi_target=? WHERE id=?", (kpi_target, existing[0]))
        else:
            c.execute("INSERT INTO vendor_kpis (vendor_id, kpi_name, kpi_target) VALUES (?,?,?)", (vendor_id, kpi_name, kpi_target))
        conn.commit()
        flash(f"KPI '{kpi_name}' added successfully!")

    conn.close()
    return redirect(url_for("kpi_dashboard"))


@app.route('/erp/finance/kpi-dashboard/remove-kpi/<int:kpi_id>', methods=["POST"])
def kpi_remove(kpi_id):
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if result:
        c.execute("UPDATE vendor_kpis SET is_active=0 WHERE id=? AND vendor_id=?", (kpi_id, result[0]))
        conn.commit()
        flash("KPI removed.")

    conn.close()
    return redirect(url_for("kpi_dashboard"))


@app.route('/erp/finance/kpi-dashboard/save-kpis', methods=["POST"])
def kpi_save():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    result = c.fetchone()
    if result:
        vendor_id = result[0]
        c.execute("SELECT id FROM vendor_kpis WHERE vendor_id=? AND is_active=1", (vendor_id,))
        for row in c.fetchall():
            target = float(request.form.get(f"target_{row[0]}", 0) or 0)
            c.execute("UPDATE vendor_kpis SET kpi_target=? WHERE id=?", (target, row[0]))
        conn.commit()
        flash("KPI settings saved!")

    conn.close()
    return redirect(url_for("kpi_dashboard"))


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

# ---- COMMUNITY AND PUBLIC CONTACT ROUTES ----

@app.route('/community')
def community_posts():
    """Community posts showing NGO updates"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Get community updates from NGOs
    c.execute("""
        SELECT scu.*, sd.stray_uid, np.name as ngo_name
        FROM stray_community_updates scu
        JOIN stray_dogs sd ON scu.stray_id = sd.id
        JOIN ngo_partners np ON scu.ngo_id = np.id
        WHERE scu.is_verified = 1
        ORDER BY scu.created_at DESC
        LIMIT 50
    """)
    
    posts_data = c.fetchall()
    posts = []
    
    for post in posts_data:
        posts.append({
            'id': post[0],
            'stray_id': post[1],
            'update_type': post[3],
            'description': post[4],
            'photo_url': post[5],
            'video_url': post[6],
            'location_latitude': post[7],
            'location_longitude': post[8],
            'created_by': post[9],
            'created_at': post[11],
            'stray_uid': post[12],
            'ngo_name': post[13]
        })
    
    conn.close()
    return render_template("community_posts.html", posts=posts)

@app.route('/public-contact')
def public_contact():
    """Public contact form for reporting issues"""
    return render_template("public_contact.html")

@app.route('/api/community/comment', methods=["POST"])
def add_community_comment():
    """Add comment to community post"""
    if "user" not in session:
        return {"success": False, "error": "Login required"}, 401
    
    data = request.get_json()
    post_id = data.get("post_id")
    comment_text = data.get("comment_text")
    
    if not post_id or not comment_text:
        return {"success": False, "error": "Missing data"}, 400
    
    # For now, we'll store comments in a simple way
    # In a real implementation, you'd have a separate comments table
    return {"success": True, "message": "Comment added"}

@app.route('/api/community/react', methods=["POST"])
def add_community_reaction():
    """Add reaction to community post"""
    if "user" not in session:
        return {"success": False, "error": "Login required"}, 401
    
    data = request.get_json()
    post_id = data.get("post_id")
    reaction_type = data.get("reaction_type")
    
    if not post_id or not reaction_type:
        return {"success": False, "error": "Missing data"}, 400
    
    # For now, we'll store reactions in a simple way
    # In a real implementation, you'd have a separate reactions table
    return {"success": True, "message": "Reaction added"}

@app.route('/api/public-contact', methods=["POST"])
def submit_public_contact():
    """Submit public contact form"""
    data = request.get_json()
    
    issue_type = data.get("issue_type")
    description = data.get("description")
    reporter_email = data.get("reporter_email")
    stray_uid = data.get("stray_uid")
    
    if not issue_type or not description:
        return {"success": False, "error": "Missing required fields"}, 400
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    try:
        # Get stray ID if provided
        stray_id = None
        if stray_uid:
            c.execute("SELECT id FROM stray_dogs WHERE stray_uid = ?", (stray_uid,))
            stray_result = c.fetchone()
            if stray_result:
                stray_id = stray_result[0]
        
        # Insert citizen report
        c.execute("""
            INSERT INTO citizen_reports 
            (stray_id, reporter_email, report_type, description, priority_level)
            VALUES (?, ?, ?, ?, ?)
        """, (stray_id, reporter_email, issue_type, description, 'medium'))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Report submitted successfully"}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}, 500

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
@require_module('basic_crm')
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
        customer_id = request.form.get("customer_id")

        c.execute("SELECT id FROM crm_customers WHERE id = ? AND vendor_id = ?", (customer_id, vendor_id))
        if not c.fetchone():
            conn.close()
            flash("Invalid customer selected")
            return redirect(url_for("crm_interactions"))

        # Insert interaction
        c.execute("""
            INSERT INTO crm_interactions 
            (customer_id, vendor_id, interaction_type, direction, subject, description, 
             outcome, follow_up_required, follow_up_date, duration_minutes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, vendor_id, request.form.get("interaction_type"),
              request.form.get("direction"), request.form.get("subject"), 
              request.form.get("description"), request.form.get("outcome"),
              1 if request.form.get("follow_up_required") else 0,
              request.form.get("follow_up_date"), request.form.get("duration_minutes"), email))

        # Update customer's last contact date
        c.execute("""
            UPDATE crm_customers 
            SET last_contact_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (customer_id,))

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

@app.route('/erp/crm/tasks')
def crm_tasks():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return render_template("crm_tasks.html", tasks=[], customers=[], stats={
            'pending': 0, 'in_progress': 0, 'overdue': 0, 'completed_this_week': 0
        }, today='')

    vendor_id = vendor_result[0]
    from datetime import date as dt_date
    today = dt_date.today().isoformat()

    c.execute("SELECT COUNT(*) FROM crm_tasks WHERE vendor_id = ? AND status = 'pending'", (vendor_id,))
    pending = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM crm_tasks WHERE vendor_id = ? AND status = 'in_progress'", (vendor_id,))
    in_progress = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM crm_tasks WHERE vendor_id = ? AND status IN ('pending','in_progress') AND due_date < ?", (vendor_id, today))
    overdue = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM crm_tasks WHERE vendor_id = ? AND status = 'completed' AND completed_date >= date('now', '-7 days')", (vendor_id,))
    completed_this_week = c.fetchone()[0] or 0

    stats = {
        'pending': pending,
        'in_progress': in_progress,
        'overdue': overdue,
        'completed_this_week': completed_this_week
    }

    c.execute("""
        SELECT t.*, cc.first_name, cc.last_name
        FROM crm_tasks t
        LEFT JOIN crm_customers cc ON t.customer_id = cc.id
        WHERE t.vendor_id = ?
        ORDER BY
            CASE t.status WHEN 'pending' THEN 0 WHEN 'in_progress' THEN 1 WHEN 'completed' THEN 2 ELSE 3 END,
            CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
            t.due_date ASC
    """, (vendor_id,))
    tasks = c.fetchall()

    c.execute("SELECT id, first_name, last_name, user_email FROM crm_customers WHERE vendor_id = ? ORDER BY first_name", (vendor_id,))
    customers = c.fetchall()

    conn.close()
    return render_template("crm_tasks.html", tasks=tasks, customers=customers, stats=stats, today=today)


@app.route('/erp/crm/tasks/add', methods=["POST"])
def add_crm_task():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("crm_tasks"))

    vendor_id = vendor_result[0]
    customer_id = request.form.get("customer_id") or None

    if customer_id:
        c.execute("SELECT id FROM crm_customers WHERE id = ? AND vendor_id = ?", (customer_id, vendor_id))
        if not c.fetchone():
            conn.close()
            flash("Invalid customer selected")
            return redirect(url_for("crm_tasks"))

    c.execute("""
        INSERT INTO crm_tasks (vendor_id, customer_id, task_type, title, description, priority, due_date, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vendor_id, customer_id, request.form.get("task_type"), request.form.get("title"),
          request.form.get("description"), request.form.get("priority", "medium"),
          request.form.get("due_date") or None, email))

    conn.commit()
    conn.close()
    flash("Task created successfully!")
    return redirect(url_for("crm_tasks"))


@app.route('/erp/crm/tasks/<int:task_id>/update', methods=["POST"])
def update_crm_task(task_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("crm_tasks"))

    vendor_id = vendor_result[0]
    new_status = request.form.get("status")

    c.execute("SELECT id FROM crm_tasks WHERE id = ? AND vendor_id = ?", (task_id, vendor_id))
    if not c.fetchone():
        conn.close()
        flash("Task not found")
        return redirect(url_for("crm_tasks"))

    if new_status == 'completed':
        c.execute("UPDATE crm_tasks SET status = ?, completed_date = CURRENT_TIMESTAMP WHERE id = ?", (new_status, task_id))
    else:
        c.execute("UPDATE crm_tasks SET status = ? WHERE id = ?", (new_status, task_id))

    conn.commit()
    conn.close()
    flash(f"Task updated to {new_status.replace('_', ' ')}!")
    return redirect(url_for("crm_tasks"))


@app.route('/erp/crm/opportunities')
def crm_opportunities():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        empty_pipeline = {s: [] for s in ['prospecting', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']}
        return render_template("crm_opportunities.html", pipeline=empty_pipeline, customers=[], summary={
            'total_open': 0, 'total_pipeline_value': 0, 'weighted_value': 0, 'won_count': 0, 'won_value': 0
        })

    vendor_id = vendor_result[0]

    c.execute("""
        SELECT o.*, cc.first_name, cc.last_name
        FROM crm_opportunities o
        JOIN crm_customers cc ON o.customer_id = cc.id
        WHERE o.vendor_id = ?
        ORDER BY o.created_at DESC
    """, (vendor_id,))
    opportunities = c.fetchall()

    pipeline = {s: [] for s in ['prospecting', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']}
    total_open = 0
    total_pipeline_value = 0
    weighted_value = 0
    won_count = 0
    won_value = 0

    for opp in opportunities:
        stage = opp[5]
        opp_data = {
            'id': opp[0],
            'customer_id': opp[1],
            'name': opp[3],
            'type': opp[4],
            'stage': opp[5],
            'probability': opp[6] or 0,
            'value': opp[7] or 0,
            'close_date': opp[8],
            'customer_name': f"{opp[16]} {opp[17] or ''}".strip()
        }
        if stage in pipeline:
            pipeline[stage].append(opp_data)

        if stage not in ('closed_won', 'closed_lost'):
            total_open += 1
            total_pipeline_value += opp_data['value']
            weighted_value += opp_data['value'] * opp_data['probability'] / 100
        elif stage == 'closed_won':
            won_count += 1
            won_value += opp_data['value']

    summary = {
        'total_open': total_open,
        'total_pipeline_value': total_pipeline_value,
        'weighted_value': weighted_value,
        'won_count': won_count,
        'won_value': won_value
    }

    c.execute("SELECT id, first_name, last_name FROM crm_customers WHERE vendor_id = ? ORDER BY first_name", (vendor_id,))
    customers = c.fetchall()

    conn.close()
    return render_template("crm_opportunities.html", pipeline=pipeline, customers=customers, summary=summary)


@app.route('/erp/crm/opportunities/add', methods=["POST"])
def add_crm_opportunity():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("crm_opportunities"))

    vendor_id = vendor_result[0]
    customer_id = request.form.get("customer_id")

    c.execute("SELECT id FROM crm_customers WHERE id = ? AND vendor_id = ?", (customer_id, vendor_id))
    if not c.fetchone():
        conn.close()
        flash("Invalid customer selected")
        return redirect(url_for("crm_opportunities"))

    c.execute("""
        INSERT INTO crm_opportunities (customer_id, vendor_id, opportunity_name, opportunity_type, stage,
            probability, expected_value, expected_close_date, description, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, vendor_id, request.form.get("opportunity_name"),
          request.form.get("opportunity_type"), request.form.get("stage", "prospecting"),
          request.form.get("probability", 10), request.form.get("expected_value") or None,
          request.form.get("expected_close_date") or None, request.form.get("description"), email))

    conn.commit()
    conn.close()
    flash("Opportunity created successfully!")
    return redirect(url_for("crm_opportunities"))


@app.route('/erp/crm/opportunities/<int:opp_id>/stage', methods=["POST"])
def update_opportunity_stage(opp_id):
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("crm_opportunities"))

    vendor_id = vendor_result[0]

    c.execute("SELECT stage FROM crm_opportunities WHERE id = ? AND vendor_id = ?", (opp_id, vendor_id))
    opp = c.fetchone()
    if not opp:
        conn.close()
        flash("Opportunity not found")
        return redirect(url_for("crm_opportunities"))

    direction = request.form.get("direction")
    stages_order = ['prospecting', 'qualified', 'proposal', 'negotiation']
    current_stage = opp[0]

    if direction == 'won':
        new_stage = 'closed_won'
        c.execute("UPDATE crm_opportunities SET stage = ?, actual_close_date = CURRENT_TIMESTAMP, probability = 100, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stage, opp_id))
    elif direction == 'lost':
        new_stage = 'closed_lost'
        c.execute("UPDATE crm_opportunities SET stage = ?, actual_close_date = CURRENT_TIMESTAMP, probability = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stage, opp_id))
    elif direction == 'forward' and current_stage in stages_order:
        idx = stages_order.index(current_stage)
        if idx < len(stages_order) - 1:
            new_stage = stages_order[idx + 1]
            prob_map = {'prospecting': 10, 'qualified': 30, 'proposal': 50, 'negotiation': 75}
            c.execute("UPDATE crm_opportunities SET stage = ?, probability = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stage, prob_map.get(new_stage, 10), opp_id))
    elif direction == 'back' and current_stage in stages_order:
        idx = stages_order.index(current_stage)
        if idx > 0:
            new_stage = stages_order[idx - 1]
            prob_map = {'prospecting': 10, 'qualified': 30, 'proposal': 50, 'negotiation': 75}
            c.execute("UPDATE crm_opportunities SET stage = ?, probability = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stage, prob_map.get(new_stage, 10), opp_id))

    conn.commit()
    conn.close()
    flash("Opportunity stage updated!")
    return redirect(url_for("crm_opportunities"))


@app.route('/erp/crm/promotions')
def crm_promotions():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return render_template("crm_promotions.html", campaigns=[], stats={
            'total_campaigns': 0, 'active_campaigns': 0, 'total_recipients': 0, 'opted_out': 0
        }, eligible_count=0)

    vendor_id = vendor_result[0]

    c.execute("SELECT COUNT(*) FROM crm_campaigns WHERE vendor_id = ?", (vendor_id,))
    total_campaigns = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_campaigns WHERE vendor_id = ? AND status = 'active'", (vendor_id,))
    active_campaigns = c.fetchone()[0] or 0

    c.execute("""SELECT COUNT(*) FROM crm_campaign_members cm
        JOIN crm_campaigns cc ON cm.campaign_id = cc.id
        WHERE cc.vendor_id = ?""", (vendor_id,))
    total_recipients = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id = ? AND marketing_opt_out = 1", (vendor_id,))
    opted_out = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM crm_customers WHERE vendor_id = ? AND (marketing_opt_out IS NULL OR marketing_opt_out = 0) AND user_email IS NOT NULL AND user_email != ''", (vendor_id,))
    eligible_count = c.fetchone()[0] or 0

    stats = {
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'total_recipients': total_recipients,
        'opted_out': opted_out
    }

    c.execute("SELECT * FROM crm_campaigns WHERE vendor_id = ? ORDER BY created_at DESC", (vendor_id,))
    campaigns = c.fetchall()

    conn.close()
    return render_template("crm_promotions.html", campaigns=campaigns, stats=stats, eligible_count=eligible_count)


@app.route('/erp/crm/promotions/send', methods=["POST"])
def send_crm_promotion():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id, name FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("crm_promotions"))

    vendor_id = vendor_result[0]
    vendor_name = vendor_result[1]

    campaign_name = request.form.get("campaign_name")
    campaign_type = request.form.get("campaign_type", "promotional")
    target_audience = request.form.get("target_audience", "all")
    message_text = request.form.get("message_text")
    description = request.form.get("description")

    c.execute("""
        INSERT INTO crm_campaigns (vendor_id, campaign_name, campaign_type, description, start_date, target_audience, status)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'active')
    """, (vendor_id, campaign_name, campaign_type, description, target_audience))
    campaign_id = c.lastrowid

    audience_filter = "AND (marketing_opt_out IS NULL OR marketing_opt_out = 0) AND user_email IS NOT NULL AND user_email != ''"
    if target_audience == 'active':
        audience_filter += " AND customer_status = 'active'"
    elif target_audience == 'inactive':
        audience_filter += " AND customer_status = 'inactive'"
    elif target_audience == 'vip':
        audience_filter += " AND lifecycle_stage = 'vip'"
    elif target_audience == 'new':
        audience_filter += " AND lifecycle_stage = 'new'"
    elif target_audience == 'leads':
        audience_filter += " AND lifecycle_stage = 'lead'"

    c.execute(f"SELECT id, user_email FROM crm_customers WHERE vendor_id = ? {audience_filter}", (vendor_id,))
    eligible_customers = c.fetchall()

    sent_count = 0
    for cust in eligible_customers:
        customer_id = cust[0]
        customer_email = cust[1]

        c.execute("INSERT INTO crm_campaign_members (campaign_id, customer_id, status, sent_date) VALUES (?, ?, 'sent', CURRENT_TIMESTAMP)", (campaign_id, customer_id))

        c.execute("SELECT id FROM chat_conversations WHERE vendor_id = ? AND user_email = ?", (vendor_id, customer_email))
        conv = c.fetchone()

        if conv:
            conv_id = conv[0]
        else:
            c.execute("INSERT INTO chat_conversations (vendor_id, user_email) VALUES (?, ?)", (vendor_id, customer_email))
            conv_id = c.lastrowid

        c.execute("""
            INSERT INTO chat_messages (conversation_id, sender_type, sender_id, message_text, message_type)
            VALUES (?, 'vendor', ?, ?, 'text')
        """, (conv_id, email, f"[Promotion: {campaign_name}]\n{message_text}"))

        c.execute("UPDATE chat_conversations SET last_message_time = CURRENT_TIMESTAMP, user_unread_count = user_unread_count + 1 WHERE id = ?", (conv_id,))
        sent_count += 1

    c.execute("UPDATE crm_campaigns SET status = 'completed', end_date = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))

    conn.commit()
    conn.close()
    flash(f"Promotion sent to {sent_count} customers via in-app chat!")
    return redirect(url_for("crm_promotions"))


@app.route('/erp/messages')
def erp_messages():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return render_template("erp_messages.html", conversations=[], active_conversation=None, messages=[])

    vendor_id = vendor_result[0]

    c.execute("""
        SELECT cc.id, cc.user_email, cc.last_message_time, cc.vendor_unread_count, cc.user_unread_count,
               (SELECT message_text FROM chat_messages WHERE conversation_id = cc.id ORDER BY timestamp DESC LIMIT 1) as last_message,
               crm.first_name, crm.last_name, crm.id as crm_id
        FROM chat_conversations cc
        LEFT JOIN crm_customers crm ON cc.user_email = crm.user_email AND crm.vendor_id = cc.vendor_id
        WHERE cc.vendor_id = ?
        ORDER BY cc.last_message_time DESC
    """, (vendor_id,))
    conv_rows = c.fetchall()

    conversations = []
    for row in conv_rows:
        customer_name = f"{row[6]} {row[7] or ''}".strip() if row[6] else None
        conversations.append({
            'id': row[0],
            'user_email': row[1],
            'last_message_time': row[2],
            'vendor_unread_count': row[3],
            'user_unread_count': row[4],
            'last_message': row[5],
            'customer_name': customer_name,
            'crm_customer_id': row[8]
        })

    active_conversation = None
    messages = []
    conv_id = request.args.get("conv_id")

    if conv_id:
        c.execute("SELECT id, user_email, vendor_unread_count FROM chat_conversations WHERE id = ? AND vendor_id = ?", (conv_id, vendor_id))
        active_conv = c.fetchone()
        if active_conv:
            c.execute("SELECT crm.first_name, crm.last_name, crm.id FROM crm_customers crm WHERE crm.user_email = ? AND crm.vendor_id = ?", (active_conv[1], vendor_id))
            crm_row = c.fetchone()

            active_conversation = {
                'id': active_conv[0],
                'user_email': active_conv[1],
                'customer_name': f"{crm_row[0]} {crm_row[1] or ''}".strip() if crm_row else None,
                'crm_customer_id': crm_row[2] if crm_row else None
            }

            c.execute("SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conv_id,))
            messages = c.fetchall()

            if active_conv[2] > 0:
                c.execute("UPDATE chat_conversations SET vendor_unread_count = 0 WHERE id = ?", (conv_id,))
                c.execute("UPDATE chat_messages SET is_read = 1 WHERE conversation_id = ? AND sender_type = 'user'", (conv_id,))
                conn.commit()

    conn.close()
    return render_template("erp_messages.html", conversations=conversations, active_conversation=active_conversation, messages=messages)


@app.route('/erp/messages/new', methods=["POST"])
def erp_new_message():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        flash("Vendor not found")
        return redirect(url_for("erp_messages"))

    vendor_id = vendor_result[0]
    customer_email = request.form.get("customer_email")
    message_text = request.form.get("message_text")

    c.execute("SELECT id FROM chat_conversations WHERE vendor_id = ? AND user_email = ?", (vendor_id, customer_email))
    existing = c.fetchone()

    if existing:
        conv_id = existing[0]
    else:
        c.execute("INSERT INTO chat_conversations (vendor_id, user_email) VALUES (?, ?)", (vendor_id, customer_email))
        conv_id = c.lastrowid

    c.execute("""
        INSERT INTO chat_messages (conversation_id, sender_type, sender_id, message_text)
        VALUES (?, 'vendor', ?, ?)
    """, (conv_id, email, message_text))

    c.execute("UPDATE chat_conversations SET last_message_time = CURRENT_TIMESTAMP, user_unread_count = user_unread_count + 1 WHERE id = ?", (conv_id,))

    conn.commit()
    conn.close()
    flash("Message sent!")
    return redirect(url_for("erp_messages", conv_id=conv_id))


@app.route('/erp/messages/send', methods=["POST"])
def erp_send_message():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    email = session["vendor"]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id FROM vendors WHERE email=?", (email,))
    vendor_result = c.fetchone()
    if not vendor_result:
        conn.close()
        return redirect(url_for("erp_messages"))

    vendor_id = vendor_result[0]
    conv_id = request.form.get("conversation_id")
    message_text = request.form.get("message_text")

    c.execute("SELECT id FROM chat_conversations WHERE id = ? AND vendor_id = ?", (conv_id, vendor_id))
    if not c.fetchone():
        conn.close()
        flash("Conversation not found")
        return redirect(url_for("erp_messages"))

    c.execute("""
        INSERT INTO chat_messages (conversation_id, sender_type, sender_id, message_text)
        VALUES (?, 'vendor', ?, ?)
    """, (conv_id, email, message_text))

    c.execute("UPDATE chat_conversations SET last_message_time = CURRENT_TIMESTAMP, user_unread_count = user_unread_count + 1 WHERE id = ?", (conv_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("erp_messages", conv_id=conv_id))


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
        latitude = float(request.form.get("latitude", 0))
        longitude = float(request.form.get("longitude", 0))
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

# ---- JWT HELPER FUNCTIONS ----

def generate_token(email, user_type):
    payload = {
        'email': email,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return pyjwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'success': False, 'error': 'Token required'}), 401
        try:
            data = pyjwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            current_user = data['email']
            user_type = data['user_type']
        except pyjwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        return f(current_user, user_type, *args, **kwargs)
    return decorated

# ---- JSON API v1 ROUTES ----

@app.route('/api/v1/auth/register', methods=["POST"])
def api_register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    if f"user:{email}" in db:
        return jsonify({'success': False, 'error': 'User already exists'}), 409

    db[f"user:{email}"] = {"email": email, "password": password, "name": name}
    token = generate_token(email, 'pet_parent')
    return jsonify({'success': True, 'token': token, 'user': {'email': email, 'name': name}})

@app.route('/api/v1/auth/login', methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    user_key = f"user:{email}"
    user = db.get(user_key)

    if user and user.get("password") == password:
        token = generate_token(email, 'pet_parent')
        return jsonify({'success': True, 'token': token, 'user': {'email': email, 'name': user.get('name', '')}})
    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@app.route('/api/v1/auth/me')
@token_required
def api_me(current_user, user_type):
    user = db.get(f"user:{current_user}", {})
    return jsonify({'success': True, 'user': {'email': current_user, 'name': user.get('name', ''), 'user_type': user_type}})

@app.route('/api/v1/pets')
@token_required
def api_get_pets(current_user, user_type):
    pets = db.get(f"pets:{current_user}", [])
    return jsonify({'success': True, 'pets': pets})

@app.route('/api/v1/pets', methods=["POST"])
@token_required
def api_add_pet(current_user, user_type):
    data = request.get_json() or {}
    pets = db.get(f"pets:{current_user}", [])

    pet = {
        "name": data.get("name", ""),
        "species": data.get("species", ""),
        "breed": data.get("breed", ""),
        "birthday": data.get("birthday", ""),
        "blood": data.get("blood", ""),
        "parent_name": data.get("parent_name", ""),
        "parent_phone": data.get("parent_phone", ""),
        "photo": ""
    }

    pets.append(pet)
    db[f"pets:{current_user}"] = pets
    return jsonify({'success': True, 'pet': pet})

@app.route('/api/v1/pets/<int:pet_index>')
@token_required
def api_get_pet(current_user, user_type, pet_index):
    pets = db.get(f"pets:{current_user}", [])
    if pet_index < 0 or pet_index >= len(pets):
        return jsonify({'success': False, 'error': 'Pet not found'}), 404

    pet = pets[pet_index]
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT service, date, time, status FROM bookings WHERE user_email = ? ORDER BY date DESC", (current_user,))
    bookings = [{'service': r[0], 'date': r[1], 'time': r[2], 'status': r[3]} for r in c.fetchall()]

    c.execute("SELECT service, date, time, status FROM bookings WHERE user_email = ? AND status = 'completed' ORDER BY date DESC", (current_user,))
    booking_history = [{'service': r[0], 'date': r[1], 'time': r[2], 'status': r[3]} for r in c.fetchall()]

    conn.close()
    return jsonify({'success': True, 'pet': pet, 'bookings': bookings, 'booking_history': booking_history})

@app.route('/api/v1/pets/<int:pet_index>', methods=["PUT"])
@token_required
def api_update_pet(current_user, user_type, pet_index):
    pets = db.get(f"pets:{current_user}", [])
    if pet_index < 0 or pet_index >= len(pets):
        return jsonify({'success': False, 'error': 'Pet not found'}), 404

    data = request.get_json() or {}
    for field in ['name', 'species', 'breed', 'birthday', 'blood', 'parent_name', 'parent_phone']:
        if field in data:
            pets[pet_index][field] = data[field]

    db[f"pets:{current_user}"] = pets
    return jsonify({'success': True, 'pet': pets[pet_index]})

@app.route('/api/v1/pets/<int:pet_index>/passport')
@token_required
def api_pet_passport(current_user, user_type, pet_index):
    pets = db.get(f"pets:{current_user}", [])
    if pet_index < 0 or pet_index >= len(pets):
        return jsonify({'success': False, 'error': 'Pet not found'}), 404

    pet_id = pet_index + 1
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT doc_type, uploaded_by_role, uploaded_by_user_id, filename, upload_time, status, comments FROM passport_documents WHERE pet_id = ? ORDER BY upload_time DESC", (pet_id,))
    docs_raw = c.fetchall()
    conn.close()

    documents = []
    doc_status = {}
    for doc in docs_raw:
        d = {'doc_type': doc[0], 'uploaded_by_role': doc[1], 'uploaded_by_user_id': doc[2], 'filename': doc[3], 'upload_time': doc[4], 'status': doc[5], 'comments': doc[6]}
        documents.append(d)
        if doc[0] not in doc_status or doc[4] > doc_status[doc[0]]['upload_time']:
            doc_status[doc[0]] = d

    required_docs = {
        'microchip': {'name': 'Microchip Certificate', 'allowed_roles': ['parent']},
        'vaccine': {'name': 'Vaccination Records', 'allowed_roles': ['vet']},
        'health_cert': {'name': 'Health Certificate', 'allowed_roles': ['vet']},
        'dgft': {'name': 'DGFT Certificate', 'allowed_roles': ['handler']},
        'aqcs': {'name': 'AQCS Certificate', 'allowed_roles': ['handler']},
        'quarantine': {'name': 'Quarantine Clearance', 'allowed_roles': ['handler']}
    }

    completed = sum(1 for dt in required_docs if dt in doc_status and doc_status[dt]['status'] == 'approved')
    completion_pct = int((completed / len(required_docs)) * 100)

    return jsonify({'success': True, 'documents': documents, 'required_docs': required_docs, 'completion_pct': completion_pct})

@app.route('/api/v1/groomers')
@token_required
def api_groomers(current_user, user_type):
    search_lat = request.args.get('lat', type=float)
    search_lon = request.args.get('lon', type=float)
    location_name = None

    location_query = request.args.get('location')
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query

    vendors = []
    has_searched = search_lat is not None and search_lon is not None
    if has_searched:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, email, password, category, city, phone, bio, image_url,
                     latitude, longitude, is_online, account_status, break_start_date,
                     break_end_date, break_reason, address, state, pincode, booking_radius_km
                     FROM vendors WHERE (account_status IS NULL OR account_status = 'active')""")
        db_vendors = c.fetchall()
        conn.close()

        for v in db_vendors:
            v_lat, v_lon = v[9], v[10]
            if v_lat is None or v_lon is None:
                continue
            radius = v[19] or 10.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vendors.append({
                    "id": v[0], "name": v[1], "description": v[7] or "Professional pet grooming services.",
                    "image": v[8] or "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400",
                    "city": v[5] or "Unknown", "latitude": v_lat, "longitude": v_lon,
                    "is_online": v[11], "address": v[16] or "", "state": v[17] or "",
                    "pincode": v[18] or "", "distance": round(dist, 1)
                })
        vendors.sort(key=lambda x: x["distance"])

    return jsonify({'success': True, 'vendors': vendors, 'location_name': location_name, 'has_searched': has_searched})

@app.route('/api/v1/marketplace')
@token_required
def api_marketplace(current_user, user_type):
    search_lat = request.args.get('lat', type=float)
    search_lon = request.args.get('lon', type=float)
    location_name = None

    location_query = request.args.get('location')
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query

    vendors = []
    if search_lat is not None and search_lon is not None:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""SELECT DISTINCT v.id, v.name, v.email, v.password, v.category, v.city, v.phone, v.bio, v.image_url,
                     v.latitude, v.longitude, v.is_online, v.account_status, v.break_start_date, v.break_end_date,
                     v.break_reason, v.address, v.state, v.pincode, v.delivery_radius_km,
                     (SELECT COUNT(*) FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0) as product_count
                     FROM vendors v
                     WHERE EXISTS (SELECT 1 FROM products p WHERE p.vendor_id = v.id AND p.quantity > 0)
                     AND (v.is_online = 1 OR NOT (LOWER(v.category) LIKE '%groom%' OR LOWER(v.category) LIKE '%salon%' OR LOWER(v.category) LIKE '%spa%' OR LOWER(v.category) LIKE '%boarding%'))
                     AND (v.account_status IS NULL OR v.account_status = 'active')""")
        online_vendors = c.fetchall()
        conn.close()

        for v in online_vendors:
            v_lat, v_lon = v[9], v[10]
            if v_lat is None or v_lon is None:
                continue
            radius = v[19] or 5.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vendors.append({
                    "id": v[0], "name": v[1], "category": v[4], "city": v[5], "bio": v[7],
                    "image_url": v[8] or "https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400",
                    "product_count": v[20], "is_online": v[11], "distance": round(dist, 1)
                })
        vendors.sort(key=lambda x: x["distance"])

    return jsonify({'success': True, 'vendors': vendors, 'location_name': location_name})

@app.route('/api/v1/marketplace/vendor/<int:vendor_id>')
@token_required
def api_marketplace_vendor(current_user, user_type, vendor_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT name, city, bio, is_online FROM vendors WHERE id=?", (vendor_id,))
    vendor_data = c.fetchone()
    if not vendor_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Vendor not found'}), 404

    vendor = {"name": vendor_data[0], "city": vendor_data[1], "bio": vendor_data[2], "is_online": vendor_data[3]}

    c.execute("""SELECT p.id, p.name, p.description, p.sale_price, p.quantity, p.image_url,
                 COALESCE(pd.discount_type, 'none') as discount_type,
                 COALESCE(pd.discount_value, 0) as discount_value,
                 COALESCE(pd.is_active, 0) as is_active,
                 CASE WHEN pd.discount_type = 'percentage' AND pd.is_active = 1 THEN p.sale_price * (1 - pd.discount_value / 100)
                      WHEN pd.discount_type = 'fixed' AND pd.is_active = 1 THEN p.sale_price - pd.discount_value
                      ELSE p.sale_price END as discounted_price,
                 CASE WHEN pd.discount_type IS NOT NULL AND pd.is_active = 1 THEN 1 ELSE 0 END as has_discount
                 FROM products p LEFT JOIN product_discounts pd ON p.id = pd.product_id
                 WHERE p.vendor_id=? AND p.quantity > 0 ORDER BY p.name""", (vendor_id,))
    products = []
    for p in c.fetchall():
        products.append({
            'id': p[0], 'name': p[1], 'description': p[2], 'sale_price': p[3],
            'quantity': p[4], 'image_url': p[5], 'discount_type': p[6],
            'discount_value': p[7], 'discounted_price': p[9], 'has_discount': bool(p[10])
        })

    conn.close()
    return jsonify({'success': True, 'vendor': vendor, 'products': products})

@app.route('/api/v1/vendor/<int:vendor_id>')
@token_required
def api_vendor_profile(current_user, user_type, vendor_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("""SELECT id, name, email, password, category, city, phone, bio, image_url,
                 latitude, longitude, is_online, account_status, break_start_date,
                 break_end_date, break_reason, address, state, pincode
                 FROM vendors WHERE id = ?""", (vendor_id,))
    data = c.fetchone()
    if not data:
        conn.close()
        return jsonify({'success': False, 'error': 'Vendor not found'}), 404

    c.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE vendor_id = ?", (data[0],))
    rs = c.fetchone()
    avg_rating = round(rs[0], 1) if rs[0] else 0
    total_reviews = rs[1] or 0

    c.execute("SELECT COUNT(*) FROM reviews WHERE vendor_id = ? AND rating >= 4", (data[0],))
    good = c.fetchone()[0] or 0
    success_rate = round((good / total_reviews * 100), 1) if total_reviews > 0 else 100

    c.execute("SELECT COUNT(*) FROM products WHERE vendor_id = ? AND quantity > 0", (data[0],))
    has_products = c.fetchone()[0] > 0

    c.execute("SELECT service_name, description, price, duration_minutes, category FROM vendor_services WHERE vendor_id = ? AND is_active = 1 ORDER BY service_name", (data[0],))
    services = []
    for s in c.fetchall():
        services.append({'name': s[0], 'description': s[1] or '', 'price': s[2], 'duration': s[3], 'category': s[4]})

    c.execute("SELECT id, vendor_id, rating, review_text, service_type, user_email, timestamp FROM reviews WHERE vendor_id = ? ORDER BY timestamp DESC", (data[0],))
    reviews = [{'id': r[0], 'rating': r[2], 'review_text': r[3], 'service_type': r[4], 'user_email': r[5], 'timestamp': r[6]} for r in c.fetchall()]

    vendor = {
        "id": data[0], "name": data[1], "description": data[7] or "", "image": data[8] or "",
        "city": data[5] or "", "is_online": data[11], "category": data[4] or "",
        "rating": avg_rating, "total_reviews": total_reviews, "success_rate": success_rate
    }

    conn.close()
    return jsonify({'success': True, 'vendor': vendor, 'services': services, 'reviews': reviews, 'has_products': has_products})

@app.route('/api/v1/vendor/<int:vendor_id>/groomers')
@token_required
def api_vendor_groomers(current_user, user_type, vendor_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT e.id, e.name, e.position, e.avg_overall_rating, e.total_reviews, e.is_certified, e.is_groomer_of_month, e.profile_image
                 FROM employees e WHERE e.vendor_id=? AND e.status='active' ORDER BY e.avg_overall_rating DESC""", (vendor_id,))
    groomers = []
    for g in c.fetchall():
        groomers.append({
            'id': g[0], 'name': g[1], 'position': g[2], 'avg_rating': g[3] or 0,
            'total_reviews': g[4] or 0, 'is_certified': g[5], 'is_groomer_of_month': g[6],
            'profile_image': g[7]
        })
    conn.close()
    return jsonify({'success': True, 'groomers': groomers})

@app.route('/api/v1/groomer/<int:employee_id>')
@token_required
def api_groomer_profile(current_user, user_type, employee_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT e.id, e.name, e.position, e.avg_overall_rating, e.total_reviews, e.is_certified, e.is_groomer_of_month,
                 e.profile_image, v.name as vendor_name, v.city as vendor_city, v.id as vendor_id
                 FROM employees e JOIN vendors v ON e.vendor_id=v.id WHERE e.id=?""", (employee_id,))
    emp = c.fetchone()
    if not emp:
        conn.close()
        return jsonify({'success': False, 'error': 'Groomer not found'}), 404

    groomer = {
        'id': emp[0], 'name': emp[1], 'position': emp[2], 'avg_rating': emp[3] or 0,
        'total_reviews': emp[4] or 0, 'is_certified': emp[5], 'is_groomer_of_month': emp[6],
        'profile_image': emp[7]
    }
    vendor = {'id': emp[10], 'name': emp[8], 'city': emp[9]}

    c.execute("SELECT overall_rating, review_text, created_at, would_book_again, reviewer_email FROM employee_reviews WHERE employee_id=? ORDER BY created_at DESC", (employee_id,))
    reviews = [{'rating': r[0], 'review_text': r[1], 'created_at': r[2], 'would_book_again': r[3], 'reviewer_email': r[4]} for r in c.fetchall()]

    conn.close()
    return jsonify({'success': True, 'groomer': groomer, 'reviews': reviews, 'vendor': vendor})

@app.route('/api/v1/vendor/<int:vendor_id>/slots')
@token_required
def api_vendor_slots(current_user, user_type, vendor_id):
    date = request.args.get('date')
    if not date:
        return jsonify({'success': False, 'error': 'Date parameter required'}), 400

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT * FROM vendor_time_slots WHERE vendor_id = ? AND is_active = 1", (vendor_id,))
    settings = c.fetchone()

    if not settings:
        available_slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                          "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]
    else:
        available_slots = generate_time_slots(settings, date)

    c.execute("SELECT time, COUNT(*) as booking_count FROM bookings WHERE vendor_id = ? AND date = ? AND status != 'cancelled' GROUP BY time", (vendor_id, date))
    existing_bookings = dict(c.fetchall())
    max_capacity = settings[6] if settings else 1

    slots = []
    for slot in available_slots:
        current_bookings = existing_bookings.get(slot, 0)
        if current_bookings < max_capacity:
            slots.append({"time": slot, "available": True, "remaining_capacity": max_capacity - current_bookings})

    conn.close()
    return jsonify({'success': True, 'slots': slots})

@app.route('/api/v1/bookings', methods=["POST"])
@token_required
def api_create_booking(current_user, user_type):
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    service = data.get('service')
    date = data.get('date')
    time_slot = data.get('time')

    if not all([vendor_id, service, date, time_slot]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""INSERT INTO bookings (vendor_id, user_email, service, date, time, duration, status,
                 pet_name, pet_parent_name, pet_parent_phone, employee_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (vendor_id, current_user, service, date, time_slot,
               data.get('duration', 60), 'confirmed',
               data.get('pet_name', ''), data.get('pet_parent_name', ''),
               data.get('pet_parent_phone', ''), data.get('employee_id')))
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'booking_id': booking_id})

@app.route('/api/v1/bookings')
@token_required
def api_get_bookings(current_user, user_type):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT b.id, b.service, b.date, b.time, b.duration, b.status, v.name as vendor_name, v.phone,
                 b.pet_name, b.pet_parent_name, b.pet_parent_phone, v.id as vendor_id
                 FROM bookings b LEFT JOIN vendors v ON b.vendor_id = v.id
                 WHERE b.user_email = ? ORDER BY b.date DESC, b.time DESC""", (current_user,))
    bookings = []
    for b in c.fetchall():
        bookings.append({
            'id': b[0], 'service': b[1], 'date': b[2], 'time': b[3],
            'duration': b[4] or 60, 'status': b[5], 'vendor_name': b[6] or 'Unknown',
            'vendor_phone': b[7], 'pet_name': b[8], 'pet_parent_name': b[9],
            'pet_parent_phone': b[10], 'vendor_id': b[11]
        })
    conn.close()
    return jsonify({'success': True, 'bookings': bookings})

@app.route('/api/v1/bookings/<int:booking_id>/review', methods=["POST"])
@token_required
def api_booking_review(current_user, user_type, booking_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    booking = c.fetchone()
    if not booking:
        conn.close()
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    col_names = [desc[0] for desc in c.description]
    booking_dict = dict(zip(col_names, booking))

    if booking_dict.get('user_email') != current_user:
        conn.close()
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    if booking_dict.get('status') != 'completed':
        conn.close()
        return jsonify({'success': False, 'error': 'Only completed bookings can be reviewed'}), 400

    c.execute("SELECT id FROM employee_reviews WHERE booking_id=?", (booking_id,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Already reviewed'}), 409

    employee_id = booking_dict.get('employee_id')
    if not employee_id:
        conn.close()
        return jsonify({'success': False, 'error': 'No groomer assigned to this booking'}), 400

    data = request.get_json() or {}
    overall = int(data.get('overall_rating', 5))
    quality = int(data.get('service_quality', 5))
    punctuality = int(data.get('punctuality', 5))
    handling = int(data.get('handling_of_pet', 5))
    review_text = data.get('review_text', '')
    would_book = 1 if data.get('would_book_again', True) else 0

    c.execute("""INSERT INTO employee_reviews (employee_id, booking_id, vendor_id, reviewer_email,
                 overall_rating, service_quality, punctuality, handling_of_pet, review_text, would_book_again)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (employee_id, booking_id, booking_dict.get('vendor_id'), current_user,
               overall, quality, punctuality, handling, review_text, would_book))
    try:
        c.execute("INSERT INTO reviews (vendor_id, user_email, rating, review_text, service_type) VALUES (?,?,?,?,?)",
                  (booking_dict.get('vendor_id'), current_user, overall, review_text, "Grooming"))
    except Exception:
        pass
    conn.commit()
    conn.close()
    update_employee_review_stats(employee_id)
    return jsonify({'success': True})

@app.route('/api/v1/orders')
@token_required
def api_get_orders(current_user, user_type):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT o.id, o.total_amount, o.status, o.delivery_type, o.delivery_fee,
                 o.estimated_delivery, o.tracking_notes, o.order_date, v.name as vendor_name
                 FROM orders o JOIN vendors v ON o.vendor_id = v.id
                 WHERE o.user_email = ? ORDER BY o.order_date DESC""", (current_user,))
    orders = []
    for o in c.fetchall():
        order = {
            'id': o[0], 'total_amount': o[1], 'status': o[2], 'delivery_type': o[3],
            'delivery_fee': o[4], 'estimated_delivery': o[5], 'tracking_notes': o[6],
            'order_date': o[7], 'vendor_name': o[8]
        }
        c.execute("""SELECT oi.quantity, oi.unit_price, p.name, p.image_url
                     FROM order_items oi JOIN products p ON oi.product_id = p.id
                     WHERE oi.order_id = ?""", (o[0],))
        order['items'] = [{'quantity': i[0], 'unit_price': i[1], 'product_name': i[2], 'image_url': i[3]} for i in c.fetchall()]
        orders.append(order)
    conn.close()
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/v1/orders', methods=["POST"])
@token_required
def api_create_order(current_user, user_type):
    data = request.get_json() or {}
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO orders (user_email, vendor_id, total_amount, delivery_address, delivery_type, delivery_fee, estimated_delivery)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (current_user, data['vendor_id'], data['total_amount'], data.get('delivery_address', ''),
                   data.get('delivery_type', 'delivery'), data.get('delivery_fee', 0), data.get('estimated_delivery', '')))
        order_id = c.lastrowid
        for item in data.get('items', []):
            c.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                      (order_id, item['product_id'], item['quantity'], item['unit_price']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/v1/handlers')
@token_required
def api_handlers(current_user, user_type):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT id, name, country, base_price, services_offered, experience_years,
                 success_rate, total_bookings, profile_image, bio, languages, certifications, is_active
                 FROM handler_profiles WHERE is_active = 1
                 ORDER BY success_rate DESC, total_bookings DESC""")
    handlers = []
    for h in c.fetchall():
        handlers.append({
            'id': h[0], 'name': h[1], 'country': h[2], 'base_price': h[3],
            'services_offered': h[4], 'experience_years': h[5], 'success_rate': h[6],
            'total_bookings': h[7], 'profile_image': h[8], 'bio': h[9],
            'languages': h[10], 'certifications': h[11]
        })
    conn.close()
    return jsonify({'success': True, 'handlers': handlers})

@app.route('/api/v1/handlers/<int:handler_id>')
@token_required
def api_handler_detail(current_user, user_type, handler_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT id, name, country, base_price, services_offered, experience_years,
                 success_rate, total_bookings, profile_image, bio, languages, certifications
                 FROM handler_profiles WHERE id = ?""", (handler_id,))
    h = c.fetchone()
    if not h:
        conn.close()
        return jsonify({'success': False, 'error': 'Handler not found'}), 404

    handler = {
        'id': h[0], 'name': h[1], 'country': h[2], 'base_price': h[3],
        'services_offered': h[4], 'experience_years': h[5], 'success_rate': h[6],
        'total_bookings': h[7], 'profile_image': h[8], 'bio': h[9],
        'languages': h[10], 'certifications': h[11]
    }

    c.execute("SELECT id, handler_id, pet_parent_email, rating, review_text, created_at FROM handler_reviews WHERE handler_id = ? ORDER BY created_at DESC", (handler_id,))
    reviews = [{'id': r[0], 'rating': r[3], 'review_text': r[4], 'created_at': r[5], 'reviewer_email': r[2]} for r in c.fetchall()]

    conn.close()
    return jsonify({'success': True, 'handler': handler, 'reviews': reviews})

@app.route('/api/v1/handlers/<int:handler_id>/book', methods=["POST"])
@token_required
def api_book_handler(current_user, user_type, handler_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute("SELECT id, name, country, base_price, email FROM handler_profiles WHERE id = ? AND is_active = 1", (handler_id,))
    h = c.fetchone()
    if not h:
        conn.close()
        return jsonify({'success': False, 'error': 'Handler not found'}), 404

    data = request.get_json() or {}
    total_amount = h[3]
    handler_fee = total_amount * 0.9
    platform_fee = total_amount * 0.1
    auto_release_time = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""INSERT INTO handler_bookings (handler_id, pet_parent_email, pet_name, pet_type, destination_country,
                 travel_date, total_amount, handler_fee, platform_fee, auto_release_time, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (handler_id, current_user, data.get('pet_name', ''), data.get('pet_type', ''),
               data.get('destination_country', ''), data.get('travel_date', ''),
               total_amount, handler_fee, platform_fee, auto_release_time, data.get('notes', '')))
    booking_id = c.lastrowid

    c.execute("INSERT INTO escrow_transactions (booking_id, transaction_type, amount, initiated_by, reason) VALUES (?, 'hold', ?, ?, 'Initial booking escrow hold')",
              (booking_id, total_amount, current_user))
    c.execute("UPDATE handler_profiles SET total_bookings = total_bookings + 1 WHERE id = ?", (handler_id,))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'booking_id': booking_id})

@app.route('/api/v1/handler-bookings')
@token_required
def api_handler_bookings(current_user, user_type):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT hb.*, hp.name as handler_name, hp.country, hp.profile_image
                 FROM handler_bookings hb JOIN handler_profiles hp ON hb.handler_id = hp.id
                 WHERE hb.pet_parent_email = ? ORDER BY hb.created_at DESC""", (current_user,))
    bookings = []
    for b in c.fetchall():
        bookings.append({
            'id': b[0], 'handler_id': b[1], 'pet_name': b[3], 'pet_type': b[4],
            'destination_country': b[5], 'travel_date': b[6], 'total_amount': b[7],
            'handler_fee': b[8], 'platform_fee': b[9], 'escrow_status': b[10],
            'booking_status': b[11], 'created_at': b[12],
            'handler_name': b[17], 'handler_country': b[18], 'handler_image': b[19]
        })
    conn.close()
    return jsonify({'success': True, 'bookings': bookings})

@app.route('/api/v1/community')
def api_community():
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT scu.*, sd.stray_uid, np.name as ngo_name
                 FROM stray_community_updates scu
                 JOIN stray_dogs sd ON scu.stray_id = sd.id
                 JOIN ngo_partners np ON scu.ngo_id = np.id
                 WHERE scu.is_verified = 1 ORDER BY scu.created_at DESC LIMIT 50""")
    posts = []
    for p in c.fetchall():
        posts.append({
            'id': p[0], 'stray_id': p[1], 'update_type': p[3], 'description': p[4],
            'photo_url': p[5], 'video_url': p[6], 'location_latitude': p[7],
            'location_longitude': p[8], 'created_by': p[9], 'created_at': p[11],
            'stray_uid': p[12], 'ngo_name': p[13]
        })
    conn.close()
    return jsonify({'success': True, 'posts': posts})

@app.route('/api/v1/stray-tracker')
def api_stray_tracker():
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT sd.stray_uid, sd.photo_url, sd.location_address, sd.breed_type,
                 sd.temperament, sd.collar_color, sd.total_vaccinations, sd.last_vaccination_date,
                 np.name as ngo_name, sd.location_latitude, sd.location_longitude
                 FROM stray_dogs sd JOIN ngo_partners np ON sd.ngo_id = np.id
                 WHERE sd.verification_status = 'verified' AND sd.current_status = 'Active'
                 ORDER BY sd.last_updated DESC LIMIT 50""")
    strays = []
    for s in c.fetchall():
        strays.append({
            'stray_uid': s[0], 'photo_url': s[1], 'location_address': s[2], 'breed_type': s[3],
            'temperament': s[4], 'collar_color': s[5], 'total_vaccinations': s[6],
            'last_vaccination_date': s[7], 'ngo_name': s[8], 'latitude': s[9], 'longitude': s[10]
        })

    c.execute("SELECT COUNT(*) FROM stray_dogs WHERE verification_status = 'verified'")
    total_verified = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM stray_vaccinations WHERE verification_status = 'verified'")
    total_vacc = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(DISTINCT ngo_id) FROM stray_dogs")
    active_ngos = c.fetchone()[0] or 0

    conn.close()
    return jsonify({'success': True, 'strays': strays, 'stats': {
        'total_verified_strays': total_verified, 'total_vaccinations': total_vacc, 'active_ngos': active_ngos
    }})

@app.route('/api/v1/stray/<stray_uid>')
def api_stray_detail(stray_uid):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT sd.*, np.name as ngo_name, np.contact_person, np.phone
                 FROM stray_dogs sd JOIN ngo_partners np ON sd.ngo_id = np.id
                 WHERE sd.stray_uid = ? AND sd.verification_status = 'verified'""", (stray_uid,))
    stray_row = c.fetchone()
    if not stray_row:
        conn.close()
        return jsonify({'success': False, 'error': 'Stray not found'}), 404

    col_names = [desc[0] for desc in c.description]
    stray = dict(zip(col_names, stray_row))

    c.execute("SELECT * FROM stray_vaccinations WHERE stray_id = ? AND verification_status = 'verified' ORDER BY vaccination_date DESC", (stray_row[0],))
    vacc_cols = [desc[0] for desc in c.description]
    vaccinations = [dict(zip(vacc_cols, r)) for r in c.fetchall()]

    c.execute("SELECT * FROM stray_community_updates WHERE stray_id = ? AND is_verified = 1 ORDER BY created_at DESC LIMIT 10", (stray_row[0],))
    upd_cols = [desc[0] for desc in c.description]
    updates = [dict(zip(upd_cols, r)) for r in c.fetchall()]

    conn.close()
    return jsonify({'success': True, 'stray': stray, 'vaccinations': vaccinations, 'updates': updates})

@app.route('/api/v1/chat/conversations')
@token_required
def api_chat_conversations(current_user, user_type):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("""SELECT cc.id, cc.vendor_id, cc.last_message_time, cc.vendor_unread_count, cc.user_unread_count,
                 v.name as vendor_name,
                 (SELECT message_text FROM chat_messages WHERE conversation_id = cc.id ORDER BY timestamp DESC LIMIT 1) as last_message
                 FROM chat_conversations cc JOIN vendors v ON cc.vendor_id = v.id
                 WHERE cc.user_email = ? ORDER BY cc.last_message_time DESC""", (current_user,))
    conversations = []
    for c_row in c.fetchall():
        conversations.append({
            'id': c_row[0], 'vendor_id': c_row[1], 'last_message_time': c_row[2],
            'vendor_unread_count': c_row[3], 'user_unread_count': c_row[4],
            'vendor_name': c_row[5], 'last_message': c_row[6]
        })
    conn.close()
    return jsonify({'success': True, 'conversations': conversations})

@app.route('/api/v1/chat/<int:conversation_id>')
@token_required
def api_chat_messages(current_user, user_type, conversation_id):
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM chat_conversations WHERE id = ? AND user_email = ?", (conversation_id, current_user))
    if not c.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    c.execute("SELECT id, sender_type, sender_id, message_text, timestamp, is_read FROM chat_messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
    messages = [{'id': m[0], 'sender_type': m[1], 'sender_id': m[2], 'message_text': m[3], 'timestamp': m[4], 'is_read': m[5]} for m in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/v1/chat/send', methods=["POST"])
@token_required
def api_chat_send(current_user, user_type):
    data = request.get_json() or {}
    conversation_id = data.get('conversation_id')
    message_text = data.get('message')

    if not conversation_id or not message_text:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM chat_conversations WHERE id = ? AND user_email = ?", (conversation_id, current_user))
    if not c.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    c.execute("INSERT INTO chat_messages (conversation_id, sender_type, sender_id, message_text) VALUES (?, 'user', ?, ?)",
              (conversation_id, current_user, message_text))
    c.execute("UPDATE chat_conversations SET vendor_unread_count = vendor_unread_count + 1, last_message_time = CURRENT_TIMESTAMP WHERE id = ?",
              (conversation_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/v1/chat/start', methods=["POST"])
@token_required
def api_chat_start(current_user, user_type):
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    if not vendor_id:
        return jsonify({'success': False, 'error': 'Vendor ID required'}), 400

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id FROM chat_conversations WHERE vendor_id = ? AND user_email = ?", (vendor_id, current_user))
    existing = c.fetchone()
    if existing:
        conn.close()
        return jsonify({'success': True, 'conversation_id': existing[0]})

    c.execute("INSERT INTO chat_conversations (vendor_id, user_email) VALUES (?, ?)", (vendor_id, current_user))
    conversation_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'conversation_id': conversation_id})

@app.route('/api/v1/vets')
@token_required
def api_vets(current_user, user_type):
    search_lat = request.args.get('lat', type=float)
    search_lon = request.args.get('lon', type=float)
    location_name = None

    location_query = request.args.get('location')
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query

    vets = []
    if search_lat is not None and search_lon is not None:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, email, category, city, phone, bio, image_url,
                     latitude, longitude, is_online, address, state, pincode, booking_radius_km
                     FROM vendors
                     WHERE (account_status IS NULL OR account_status = 'active')
                     AND (LOWER(category) LIKE '%vet%' OR LOWER(category) LIKE '%clinic%' OR LOWER(category) LIKE '%hospital%')""")
        for v in c.fetchall():
            v_lat, v_lon = v[8], v[9]
            if v_lat is None or v_lon is None:
                continue
            radius = v[14] or 15.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vets.append({
                    "id": v[0], "name": v[1], "category": v[3], "city": v[4],
                    "phone": v[5], "bio": v[6], "image_url": v[7],
                    "latitude": v_lat, "longitude": v_lon, "is_online": v[10],
                    "distance": round(dist, 1)
                })
        vets.sort(key=lambda x: x["distance"])
        conn.close()

    return jsonify({'success': True, 'vets': vets, 'location_name': location_name})

@app.route('/api/v1/boarding')
@token_required
def api_boarding(current_user, user_type):
    search_lat = request.args.get('lat', type=float)
    search_lon = request.args.get('lon', type=float)
    location_name = None

    location_query = request.args.get('location')
    if location_query:
        lat, lon, display = geocode_location(location_query)
        if lat is not None and lon is not None:
            search_lat, search_lon = lat, lon
            location_name = location_query

    vendors = []
    if search_lat is not None and search_lon is not None:
        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, email, category, city, phone, bio, image_url,
                     latitude, longitude, is_online, address, state, pincode, booking_radius_km
                     FROM vendors
                     WHERE (account_status IS NULL OR account_status = 'active')
                     AND (LOWER(category) LIKE '%board%' OR LOWER(category) LIKE '%kennel%' OR LOWER(category) LIKE '%daycare%')""")
        for v in c.fetchall():
            v_lat, v_lon = v[8], v[9]
            if v_lat is None or v_lon is None:
                continue
            radius = v[14] or 15.0
            dist = haversine(search_lat, search_lon, v_lat, v_lon)
            if dist <= radius:
                vendors.append({
                    "id": v[0], "name": v[1], "category": v[3], "city": v[4],
                    "bio": v[6], "image_url": v[7], "latitude": v_lat, "longitude": v_lon,
                    "is_online": v[10], "distance": round(dist, 1)
                })
        vendors.sort(key=lambda x: x["distance"])
        conn.close()

    return jsonify({'success': True, 'vendors': vendors, 'location_name': location_name})

@app.route('/api/v1/set-location', methods=["POST"])
@token_required
def api_set_location(current_user, user_type):
    data = request.get_json() or {}
    lat = data.get('lat')
    lon = data.get('lon')

    if lat is None or lon is None:
        return jsonify({'success': False, 'error': 'lat and lon required'}), 400

    import urllib.request
    location_name = "Your location"
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "FurrButler/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())
            addr = geo_data.get("address", {})
            location_name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or addr.get("county") or "Your location"
    except Exception:
        pass

    user_data = db.get(f"user:{current_user}", {})
    user_data['location'] = {"lat": lat, "lon": lon, "name": location_name}
    db[f"user:{current_user}"] = user_data

    return jsonify({'success': True, 'location_name': location_name})

@app.route('/api/v1/languages')
def api_languages():
    languages = get_supported_languages()
    return jsonify({'success': True, 'languages': languages})


@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms_of_service():
    return render_template('terms.html')

@app.route('/furrvet/privacy')
def furrvet_privacy():
    return render_template('furrvet_privacy.html')

@app.route('/accept-cookies', methods=["POST"])
def accept_cookies():
    session['cookie_consent'] = True
    return redirect(request.referrer or url_for("dashboard"))

@app.route('/gdpr/export-data')
def gdpr_export_data():
    if "user" not in session:
        return redirect(url_for("login"))
    
    import json as json_mod
    email = session["user"]
    export = {"email": email, "exported_at": datetime.now().isoformat()}
    
    user_data = db.get(f"user:{email}")
    if user_data:
        safe_data = {k: v for k, v in user_data.items() if k != "password"}
        export["profile"] = safe_data
    
    pets_data = db.get(f"pets:{email}")
    if pets_data:
        export["pets"] = pets_data
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, vendor_id, service, date, time, duration, status, pet_name FROM bookings WHERE user_email=?", (email,))
    bookings = c.fetchall()
    conn.close()
    if bookings:
        export["bookings"] = [{"id": b[0], "vendor_id": b[1], "service": b[2], "date": b[3], "time": b[4], "duration": b[5], "status": b[6], "pet_name": b[7]} for b in bookings]
    
    response = app.response_class(
        response=json_mod.dumps(export, indent=2, default=str),
        status=200,
        mimetype='application/json'
    )
    response.headers["Content-Disposition"] = f"attachment; filename=furrbutler_data_{email}.json"
    return response

@app.route('/gdpr/delete-account', methods=["POST"])
def gdpr_delete_account():
    if "user" not in session:
        return redirect(url_for("login"))
    
    email = session["user"]
    
    user_data = db.get(f"user:{email}")
    if user_data:
        user_data["gdpr_deletion_scheduled"] = datetime.now().isoformat()
        user_data["gdpr_deletion_status"] = "scheduled"
        db[f"user:{email}"] = user_data
    
    gdpr_log_entry = {
        "action": "account_deletion_scheduled",
        "user_type": "pet_parent",
        "email": email,
        "timestamp": datetime.now().isoformat(),
        "status": "scheduled"
    }
    breach_log = db.get("gdpr:deletion_log") or []
    breach_log.append(gdpr_log_entry)
    db["gdpr:deletion_log"] = breach_log
    
    session.clear()
    flash("Your account deletion has been scheduled. Your data will be removed within 30 days.")
    return redirect(url_for("login"))

@app.route('/gdpr/vendor-export-data')
def gdpr_vendor_export_data():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    
    import json as json_mod
    email = session["vendor"]
    export = {"email": email, "exported_at": datetime.now().isoformat(), "user_type": "vendor"}
    
    vendor_data = db.get(f"vendor:{email}")
    if vendor_data:
        safe_data = {k: v for k, v in vendor_data.items() if k != "password"}
        export["profile"] = safe_data
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors WHERE email=?", (email,))
    vendor_row = c.fetchone()
    if vendor_row:
        cols = [desc[0] for desc in c.description]
        vendor_dict = dict(zip(cols, vendor_row))
        vendor_dict.pop("password", None)
        export["vendor_record"] = vendor_dict
        
        vendor_id = vendor_row[0]
        c.execute("SELECT id, user_email, service, date, time, duration, status, pet_name FROM bookings WHERE vendor_id=?", (vendor_id,))
        bookings = c.fetchall()
        if bookings:
            export["bookings"] = [{"id": b[0], "user_email": b[1], "service": b[2], "date": b[3], "time": b[4], "duration": b[5], "status": b[6], "pet_name": b[7]} for b in bookings]
    conn.close()
    
    response = app.response_class(
        response=json_mod.dumps(export, indent=2, default=str),
        status=200,
        mimetype='application/json'
    )
    response.headers["Content-Disposition"] = f"attachment; filename=furrbutler_vendor_data_{email}.json"
    return response

@app.route('/gdpr/vendor-delete-account', methods=["POST"])
def gdpr_vendor_delete_account():
    if "vendor" not in session:
        return redirect(url_for("vendor_login"))
    
    email = session["vendor"]
    
    vendor_data = db.get(f"vendor:{email}")
    if vendor_data:
        vendor_data["gdpr_deletion_scheduled"] = datetime.now().isoformat()
        vendor_data["gdpr_deletion_status"] = "scheduled"
        db[f"vendor:{email}"] = vendor_data
    
    gdpr_log_entry = {
        "action": "account_deletion_scheduled",
        "user_type": "vendor",
        "email": email,
        "timestamp": datetime.now().isoformat(),
        "status": "scheduled"
    }
    breach_log = db.get("gdpr:deletion_log") or []
    breach_log.append(gdpr_log_entry)
    db["gdpr:deletion_log"] = breach_log
    
    session.clear()
    flash("Your vendor account deletion has been scheduled. Your data will be removed within 30 days.")
    return redirect(url_for("vendor_login"))


@app.route('/api/v1/gdpr/privacy-policy')
def api_gdpr_privacy_policy():
    return jsonify({
        "success": True,
        "privacy_policy_url": url_for("privacy_policy", _external=True),
        "last_updated": "2026-04-07",
        "version": "1.0"
    })

@app.route('/api/v1/gdpr/terms')
def api_gdpr_terms():
    return jsonify({
        "success": True,
        "terms_url": url_for("terms_of_service", _external=True),
        "last_updated": "2026-04-07",
        "version": "1.0"
    })

@app.route('/api/v1/gdpr/consent', methods=["POST"])
@token_required
def api_gdpr_consent(current_user, user_type):
    data = request.get_json()
    consent_type = data.get("consent_type", "privacy_policy")
    accepted = data.get("accepted", False)
    
    user_data = db.get(f"user:{current_user}")
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    if "gdpr_consents" not in user_data:
        user_data["gdpr_consents"] = {}
    
    user_data["gdpr_consents"][consent_type] = {
        "accepted": accepted,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }
    db[f"user:{current_user}"] = user_data
    
    return jsonify({"success": True, "message": "Consent recorded"})

@app.route('/api/v1/gdpr/consent', methods=["GET"])
@token_required
def api_gdpr_get_consent(current_user, user_type):
    user_data = db.get(f"user:{current_user}")
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    consents = user_data.get("gdpr_consents", {})
    return jsonify({"success": True, "consents": consents})

@app.route('/api/v1/gdpr/export-data')
@token_required
def api_gdpr_export_data(current_user, user_type):
    export = {"email": current_user, "exported_at": datetime.now().isoformat()}
    
    user_data = db.get(f"user:{current_user}")
    if user_data:
        safe_data = {k: v for k, v in user_data.items() if k != "password"}
        export["profile"] = safe_data
    
    pets_data = db.get(f"pets:{current_user}")
    if pets_data:
        export["pets"] = pets_data
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT id, vendor_id, service, date, time, duration, status, pet_name FROM bookings WHERE user_email=?", (current_user,))
    bookings = c.fetchall()
    conn.close()
    if bookings:
        export["bookings"] = [{"id": b[0], "vendor_id": b[1], "service": b[2], "date": b[3], "time": b[4], "duration": b[5], "status": b[6], "pet_name": b[7]} for b in bookings]
    
    return jsonify({"success": True, "data": export})

@app.route('/api/v1/gdpr/delete-account', methods=["POST"])
@token_required
def api_gdpr_delete_account(current_user, user_type):
    user_data = db.get(f"user:{current_user}")
    if user_data:
        user_data["gdpr_deletion_scheduled"] = datetime.now().isoformat()
        user_data["gdpr_deletion_status"] = "scheduled"
        db[f"user:{current_user}"] = user_data
    
    gdpr_log_entry = {
        "action": "account_deletion_scheduled",
        "user_type": "pet_parent",
        "email": current_user,
        "timestamp": datetime.now().isoformat(),
        "status": "scheduled",
        "source": "mobile_app"
    }
    breach_log = db.get("gdpr:deletion_log") or []
    breach_log.append(gdpr_log_entry)
    db["gdpr:deletion_log"] = breach_log
    
    return jsonify({"success": True, "message": "Account deletion scheduled. Your data will be removed within 30 days."})


@app.route('/admin/gdpr/breach-log')
def admin_gdpr_breach_log():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))
    
    deletion_log = db.get("gdpr:deletion_log") or []
    breach_log = db.get("gdpr:breach_log") or []
    
    return render_template("gdpr_breach_log.html", deletion_log=deletion_log, breach_log=breach_log)


@app.route('/furrvet/gdpr/privacy-notice')
def furrvet_gdpr_privacy_notice():
    return render_template('furrvet_privacy.html')

@app.route('/furrvet/gdpr/consent', methods=["GET"])
def furrvet_gdpr_consent_page():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT medical_processing_consent, retention_acknowledged, referral_sharing_consent, research_consent, consent_date FROM furrvet_gdpr_consents WHERE vet_id = ? ORDER BY id DESC LIMIT 1", (vet_id,))
    existing = c.fetchone()
    conn.close()
    return render_template('furrvet_consent.html', existing=existing)

@app.route('/furrvet/gdpr/consent', methods=["POST"])
def furrvet_gdpr_consent_save():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))
    vet_id = session['furrvet_vet_id']
    medical = 1 if request.form.get('medical_processing_consent') else 0
    retention = 1 if request.form.get('retention_acknowledged') else 0
    referral = 1 if request.form.get('referral_sharing_consent') else 0
    research = 1 if request.form.get('research_consent') else 0
    if not medical or not retention:
        flash("You must accept the required consents (medical data processing and retention acknowledgement).")
        return redirect(url_for('furrvet_gdpr_consent_page'))
    consent_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip_address = request.remote_addr or 'unknown'
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("""INSERT INTO furrvet_gdpr_consents 
        (vet_id, medical_processing_consent, retention_acknowledged, referral_sharing_consent, research_consent, consent_date, consent_version, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, '1.0', ?)""",
        (vet_id, medical, retention, referral, research, consent_date, ip_address))
    conn.commit()
    conn.close()
    flash("All consents have been saved successfully.")
    return redirect(url_for('furrvet_gdpr_consent_page'))

@app.route('/furrvet/gdpr/export-records')
def furrvet_gdpr_export_records():
    if 'furrvet_vet_id' not in session:
        return redirect(url_for('furrvet_login'))
    vet_id = session['furrvet_vet_id']
    conn = sqlite3.connect('furrvet.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pets WHERE id IN (SELECT DISTINCT pet_id FROM medical_records WHERE vet_id = ?) OR id IN (SELECT DISTINCT pet_id FROM appointments WHERE vet_id = ?)", (vet_id, vet_id))
    pets_cols = [desc[0] for desc in c.description]
    pets_rows = c.fetchall()
    pets_data = [dict(zip(pets_cols, row)) for row in pets_rows]
    pet_ids = [p['id'] for p in pets_data] if pets_data else []
    owner_ids = list(set(p.get('owner_id') for p in pets_data if p.get('owner_id')))
    if owner_ids:
        placeholders = ','.join('?' * len(owner_ids))
        c.execute(f"SELECT * FROM pet_owners WHERE id IN ({placeholders})", owner_ids)
    else:
        c.execute("SELECT * FROM pet_owners WHERE 1=0")
    owners_cols = [desc[0] for desc in c.description]
    owners_rows = c.fetchall()
    owners_data = [dict(zip(owners_cols, row)) for row in owners_rows]
    c.execute("SELECT * FROM medical_records WHERE vet_id = ?", (vet_id,))
    med_cols = [desc[0] for desc in c.description]
    med_rows = c.fetchall()
    med_data = [dict(zip(med_cols, row)) for row in med_rows]
    if pet_ids:
        placeholders = ','.join('?' * len(pet_ids))
        c.execute(f"SELECT * FROM vaccinations WHERE pet_id IN ({placeholders})", pet_ids)
    else:
        c.execute("SELECT * FROM vaccinations WHERE 1=0")
    vax_cols = [desc[0] for desc in c.description]
    vax_rows = c.fetchall()
    vax_data = [dict(zip(vax_cols, row)) for row in vax_rows]
    conn.close()
    export = {
        "export_date": datetime.now().isoformat(),
        "exported_by_vet_id": vet_id,
        "clinic_name": session.get('furrvet_clinic_name', ''),
        "patients": pets_data,
        "pet_owners": owners_data,
        "medical_records": med_data,
        "vaccinations": vax_data
    }
    response = app.response_class(
        response=json.dumps(export, indent=2, default=str),
        status=200,
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = 'attachment; filename=furrvet_records_export.json'
    return response

@app.route('/furrwings/privacy')
def furrwings_privacy_notice():
    return render_template('furrwings_privacy.html')

@app.route('/erp/gdpr/dpa')
def erp_gdpr_dpa():
    if 'vendor' not in session:
        return redirect(url_for('vendor_login'))
    return render_template('erp_dpa.html')

@app.route('/admin/gdpr/breach-log', methods=["POST"])
def admin_gdpr_breach_log_post():
    if not session.get("master_admin"):
        return redirect(url_for("master_admin_login"))
    detected_date = request.form.get('detected_date', '')
    description = request.form.get('description', '')
    affected_users = request.form.get('affected_users', '')
    severity = request.form.get('severity', 'low')
    reported_to_authority = True if request.form.get('reported_to_authority') else False
    report_date = request.form.get('report_date', '')
    resolution = request.form.get('resolution', '')
    breach_entry = {
        "detected_date": detected_date,
        "description": description,
        "affected_users": affected_users,
        "severity": severity,
        "reported_to_authority": reported_to_authority,
        "report_date": report_date,
        "resolution": resolution,
        "logged_at": datetime.now().isoformat()
    }
    breach_log = db.get("gdpr:breach_log") or []
    breach_log.append(breach_entry)
    db["gdpr:breach_log"] = breach_log
    flash("Breach record added successfully.")
    return redirect(url_for('admin_gdpr_breach_log'))

@app.route('/api/v1/gdpr/furrwings-notice')
def api_gdpr_furrwings_notice():
    return jsonify({
        "success": True,
        "furrwings_privacy_url": url_for("furrwings_privacy_notice", _external=True),
        "transfer_notice": "FurrWings facilitates international pet travel. As part of this service, your pet's health and passport data may be transferred to and processed in countries outside India and the European Economic Area. Transfers are made under Article 49(1)(b) (contract performance) and legal obligations to destination country authorities. Standard contractual clauses apply where applicable.",
        "data_transferred": [
            "Pet passport information",
            "Vaccination records",
            "Health certificates",
            "Owner contact details",
            "Travel documentation"
        ],
        "retention": {
            "travel_records": "7 years",
            "pet_passport": "Life of pet + 5 years",
            "health_certificates": "5 years"
        },
        "last_updated": "2026-04-07",
        "version": "1.0"
    })

@app.route('/api/v1/gdpr/furrwings-consent', methods=["POST"])
@token_required
def api_gdpr_furrwings_consent(current_user, user_type):
    data = request.get_json()
    transfer_consent = data.get("transfer_consent", False)
    user_data = db.get(f"user:{current_user}")
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404
    if "gdpr_consents" not in user_data:
        user_data["gdpr_consents"] = {}
    user_data["gdpr_consents"]["furrwings_transfer"] = {
        "accepted": transfer_consent,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }
    db[f"user:{current_user}"] = user_data
    return jsonify({"success": True, "message": "International transfer consent recorded"})


# Run app
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, use_reloader=False, log_output=True)
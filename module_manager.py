
import sqlite3
from datetime import datetime
from enum import Enum

class ModuleStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled" 
    TRIAL = "trial"
    PREMIUM = "premium"

class ModuleManager:
    def __init__(self, db_path='erp.db'):
        self.db_path = db_path
        self.init_module_tables()
        self.register_default_modules()
    
    def init_module_tables(self):
        """Initialize module management tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Module definitions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                is_core BOOLEAN DEFAULT 0,
                pricing_tier TEXT DEFAULT 'free',
                monthly_price REAL DEFAULT 0.0,
                annual_price REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Vendor module subscriptions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS vendor_module_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'disabled',
                subscription_type TEXT DEFAULT 'free',
                subscribed_at TEXT,
                expires_at TEXT,
                trial_ends_at TEXT,
                auto_renewal BOOLEAN DEFAULT 1,
                payment_status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id),
                FOREIGN KEY (module_name) REFERENCES modules(module_name),
                UNIQUE(vendor_id, module_name)
            )
        ''')
        
        # Module usage analytics
        c.execute('''
            CREATE TABLE IF NOT EXISTS module_usage_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                usage_date DATE NOT NULL,
                metadata TEXT,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id),
                FOREIGN KEY (module_name) REFERENCES modules(module_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_default_modules(self):
        """Register all available modules in the system"""
        modules = [
            # Core modules (always enabled)
            {
                'module_name': 'dashboard',
                'display_name': 'Dashboard',
                'description': 'Main vendor dashboard and overview',
                'category': 'core',
                'is_core': True,
                'pricing_tier': 'free'
            },
            {
                'module_name': 'basic_inventory',
                'display_name': 'Basic Inventory',
                'description': 'Basic product and stock management',
                'category': 'core',
                'is_core': True,
                'pricing_tier': 'free'
            },
            {
                'module_name': 'basic_bookings',
                'display_name': 'Basic Bookings',
                'description': 'Basic appointment scheduling',
                'category': 'core',
                'is_core': True,
                'pricing_tier': 'free'
            },
            
            # Premium inventory features
            {
                'module_name': 'advanced_inventory',
                'display_name': 'Advanced Inventory Analytics',
                'description': 'FIFO costing, turnover analysis, demand forecasting',
                'category': 'inventory',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 29.99,
                'annual_price': 299.99
            },
            {
                'module_name': 'inventory_automation',
                'display_name': 'Inventory Automation',
                'description': 'Auto-reorder, smart alerts, batch management',
                'category': 'inventory',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 19.99,
                'annual_price': 199.99
            },
            
            # CRM and Customer Management
            {
                'module_name': 'basic_crm',
                'display_name': 'Basic CRM',
                'description': 'Customer management and basic interactions',
                'category': 'crm',
                'is_core': False,
                'pricing_tier': 'starter',
                'monthly_price': 15.99,
                'annual_price': 159.99
            },
            {
                'module_name': 'advanced_crm',
                'display_name': 'Advanced CRM',
                'description': 'Campaigns, automation, lead scoring',
                'category': 'crm',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 39.99,
                'annual_price': 399.99
            },
            
            # HR Management
            {
                'module_name': 'hr_management',
                'display_name': 'HR Management',
                'description': 'Employee management, timesheets, payroll',
                'category': 'hr',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 24.99,
                'annual_price': 249.99
            },
            
            # Financial and Accounting
            {
                'module_name': 'advanced_accounting',
                'display_name': 'Advanced Accounting',
                'description': 'P&L, balance sheet, cash flow reports',
                'category': 'accounting',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 34.99,
                'annual_price': 349.99
            },
            {
                'module_name': 'tax_compliance',
                'display_name': 'Tax Compliance',
                'description': 'GST reports, tax filing assistance',
                'category': 'accounting',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 19.99,
                'annual_price': 199.99
            },
            
            # WhatsApp and Communication
            {
                'module_name': 'whatsapp_business',
                'display_name': 'WhatsApp Business Integration',
                'description': 'WhatsApp catalog, automated responses',
                'category': 'communication',
                'is_core': False,
                'pricing_tier': 'starter',
                'monthly_price': 12.99,
                'annual_price': 129.99
            },
            
            # AI and Automation
            {
                'module_name': 'ai_chatbot',
                'display_name': 'AI Chatbot',
                'description': 'Intelligent customer service bot',
                'category': 'ai',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 49.99,
                'annual_price': 499.99
            },
            {
                'module_name': 'predictive_analytics',
                'display_name': 'Predictive Analytics',
                'description': 'Sales forecasting, demand prediction',
                'category': 'ai',
                'is_core': False,
                'pricing_tier': 'enterprise',
                'monthly_price': 99.99,
                'annual_price': 999.99
            },
            
            # FurrWings Features
            {
                'module_name': 'pet_passport',
                'display_name': 'Pet Passport System',
                'description': 'International pet travel documentation',
                'category': 'furrwings',
                'is_core': False,
                'pricing_tier': 'premium',
                'monthly_price': 24.99,
                'annual_price': 249.99
            },
            
            # Stray Tracker
            {
                'module_name': 'stray_tracker',
                'display_name': 'Stray Dog Tracker',
                'description': 'NGO partnership and stray management',
                'category': 'social',
                'is_core': False,
                'pricing_tier': 'free'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        for module in modules:
            c.execute('''
                INSERT OR REPLACE INTO modules 
                (module_name, display_name, description, category, is_core, pricing_tier, monthly_price, annual_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                module['module_name'], module['display_name'], module['description'],
                module['category'], module['is_core'], module['pricing_tier'],
                module.get('monthly_price', 0.0), module.get('annual_price', 0.0)
            ))
        
        conn.commit()
        conn.close()
    
    def is_module_enabled(self, vendor_id, module_name):
        """Check if a module is enabled for a vendor — all modules are currently free and accessible"""
        return True
    
    def enable_module(self, vendor_id, module_name, subscription_type='free', duration_days=None):
        """Enable a module for a vendor"""
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        expires_at = None
        if duration_days:
            expires_at = (datetime.now() + timedelta(days=duration_days)).isoformat()
        
        c.execute('''
            INSERT OR REPLACE INTO vendor_module_subscriptions 
            (vendor_id, module_name, status, subscription_type, subscribed_at, expires_at)
            VALUES (?, ?, 'enabled', ?, ?, ?)
        ''', (vendor_id, module_name, subscription_type, datetime.now().isoformat(), expires_at))
        
        conn.commit()
        conn.close()
        
        self.log_module_usage(vendor_id, module_name, 'module_enabled')
    
    def disable_module(self, vendor_id, module_name):
        """Disable a module for a vendor"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if it's a core module
        c.execute("SELECT is_core FROM modules WHERE module_name = ?", (module_name,))
        module = c.fetchone()
        if module and module[0]:  # Can't disable core modules
            print(f"DEBUG: Cannot disable core module: {module_name}")
            conn.close()
            return False
        
        # Check if subscription exists
        c.execute("SELECT id FROM vendor_module_subscriptions WHERE vendor_id = ? AND module_name = ?", (vendor_id, module_name))
        existing = c.fetchone()
        
        if existing:
            # Update existing subscription
            c.execute('''
                UPDATE vendor_module_subscriptions 
                SET status = 'disabled' 
                WHERE vendor_id = ? AND module_name = ?
            ''', (vendor_id, module_name))
            print(f"DEBUG: Updated existing subscription for {module_name} to disabled")
        else:
            # Insert new disabled subscription
            c.execute('''
                INSERT INTO vendor_module_subscriptions 
                (vendor_id, module_name, status, subscription_type)
                VALUES (?, ?, 'disabled', 'free')
            ''', (vendor_id, module_name))
            print(f"DEBUG: Created new disabled subscription for {module_name}")
        
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        
        print(f"DEBUG: Disable operation affected {rows_affected} rows")
        self.log_module_usage(vendor_id, module_name, 'module_disabled')
        return True
    
    def start_trial(self, vendor_id, module_name, trial_days=14):
        """Start a trial for a premium module"""
        from datetime import datetime, timedelta
        
        trial_ends_at = (datetime.now() + timedelta(days=trial_days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO vendor_module_subscriptions 
            (vendor_id, module_name, status, subscription_type, subscribed_at, trial_ends_at)
            VALUES (?, ?, 'trial', 'trial', ?, ?)
        ''', (vendor_id, module_name, datetime.now().isoformat(), trial_ends_at))
        
        conn.commit()
        conn.close()
        
        self.log_module_usage(vendor_id, module_name, 'trial_started')
    
    def get_vendor_modules(self, vendor_id):
        """Get all modules and their status for a vendor"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT m.*, 
                   COALESCE(vms.status, 'disabled') as status,
                   vms.subscription_type,
                   vms.expires_at,
                   vms.trial_ends_at
            FROM modules m
            LEFT JOIN vendor_module_subscriptions vms ON m.module_name = vms.module_name AND vms.vendor_id = ?
            ORDER BY m.category, m.display_name
        ''', (vendor_id,))
        
        modules = c.fetchall()
        conn.close()
        
        result = []
        for module in modules:
            is_enabled = self.is_module_enabled(vendor_id, module[1])  # module_name is index 1
            result.append({
                'id': module[0],
                'module_name': module[1],
                'display_name': module[2],
                'description': module[3],
                'category': module[4],
                'is_core': module[5],
                'pricing_tier': module[6],
                'monthly_price': module[7],
                'annual_price': module[8],
                'status': module[10] if module[10] else 'disabled',
                'subscription_type': module[11],
                'expires_at': module[12],
                'trial_ends_at': module[13],
                'is_enabled': is_enabled
            })
        
        return result
    
    def log_module_usage(self, vendor_id, module_name, action_type, metadata=None):
        """Log module usage for analytics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO module_usage_analytics 
            (vendor_id, module_name, action_type, usage_date, metadata)
            VALUES (?, ?, ?, DATE('now'), ?)
        ''', (vendor_id, module_name, action_type, metadata))
        
        conn.commit()
        conn.close()

# Module decorator for route protection
def require_module(module_name):
    """Decorator to protect routes with module requirements"""
    from functools import wraps
    from flask import session, redirect, url_for, flash
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "vendor" not in session:
                return redirect(url_for("erp_login"))
            
            # Get vendor ID
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("SELECT id FROM vendors WHERE email = ?", (session["vendor"],))
            vendor_result = c.fetchone()
            conn.close()
            
            if not vendor_result:
                flash("Vendor not found")
                return redirect(url_for("erp_login"))
            
            vendor_id = vendor_result[0]
            module_manager = ModuleManager()
            
            if not module_manager.is_module_enabled(vendor_id, module_name):
                flash(f"This feature requires the {module_name.replace('_', ' ').title()} module. Please upgrade your plan.")
                return redirect(url_for("module_management"))
            
            # Log module usage
            module_manager.log_module_usage(vendor_id, module_name, 'feature_accessed')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

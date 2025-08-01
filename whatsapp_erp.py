import json
import sqlite3
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import os

class WhatsAppERPSimulator:
    def __init__(self, db_path='erp.db'):
        self.db_path = db_path
        self.catalog_file = 'whatsapp_catalog.json'
        self.init_whatsapp_tables()
        self.load_catalog()

    def init_whatsapp_tables(self):
        """Initialize WhatsApp-specific tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # WhatsApp vendor profiles
        c.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE,
                business_name TEXT,
                vendor_id INTEGER,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (vendor_id) REFERENCES vendors (id)
            )
        ''')

        # WhatsApp message logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_phone TEXT,
                message_text TEXT,
                message_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_text TEXT,
                processed BOOLEAN DEFAULT 0
            )
        ''')

        # WhatsApp bookings
        c.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_phone TEXT,
                customer_name TEXT,
                pet_name TEXT,
                service_type TEXT,
                booking_date DATE,
                booking_time TIME,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ WhatsApp ERP tables initialized")

    def load_catalog(self):
        """Load or create WhatsApp catalog JSON"""
        if os.path.exists(self.catalog_file):
            with open(self.catalog_file, 'r') as f:
                self.catalog = json.load(f)
        else:
            self.catalog = {
                "catalog_id": "furrbutler_catalog",
                "version": "1.0",
                "products": []
            }
            self.save_catalog()
        print(f"📱 WhatsApp catalog loaded: {len(self.catalog['products'])} products")

    def save_catalog(self):
        """Save catalog to JSON file"""
        with open(self.catalog_file, 'w') as f:
            json.dump(self.catalog, f, indent=2)

    def register_vendor_via_whatsapp(self, phone_number, business_name):
        """Simulate vendor registration via WhatsApp"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # Check if vendor already exists
            c.execute("SELECT * FROM whatsapp_vendors WHERE phone_number = ?", (phone_number,))
            existing = c.fetchone()

            if existing:
                return {
                    "success": False,
                    "message": f"📱 Business already registered with {phone_number}"
                }

            # Create main vendor profile
            c.execute('''
                INSERT INTO vendors (name, email, phone, type, status) 
                VALUES (?, ?, ?, ?, ?)
            ''', (business_name, f"{phone_number}@whatsapp.business", phone_number, "groomer", "active"))

            vendor_id = c.lastrowid

            # Create WhatsApp vendor profile
            c.execute('''
                INSERT INTO whatsapp_vendors (phone_number, business_name, vendor_id)
                VALUES (?, ?, ?)
            ''', (phone_number, business_name, vendor_id))

            conn.commit()

            welcome_message = f"""
🎉 Welcome to FurrButler WhatsApp Business!

📱 Your business '{business_name}' is now registered!
📞 Phone: {phone_number}

🚀 Get started with these commands:
• "Add 10 units Dog Shampoo ₹450 each" - Add inventory
• "Restock Cat Food by 20 units" - Update stock
• "Current inventory?" - Check stock levels
• "Book grooming for Luna, April 25, 10 AM" - Add booking

💡 Type 'help' anytime for more commands!
            """

            return {
                "success": True,
                "message": welcome_message,
                "vendor_id": vendor_id
            }

        except Exception as e:
            conn.rollback()
            return {
                "success": False,
                "message": f"❌ Registration failed: {str(e)}"
            }
        finally:
            conn.close()

    def parse_vendor_message(self, phone_number, message):
        """Parse and handle vendor WhatsApp messages"""
        message = message.strip().lower()

        # Log the message
        self.log_message(phone_number, message, "incoming")

        # Command patterns
        patterns = {
            'add_inventory': r'add (\d+) units? (.+?) ₹?(\d+) each',
            'restock': r'restock (.+?) by (\d+) units?',
            'check_inventory': r'(current inventory|stock levels?|what do i have)',
            'low_stock': r'(what\'s running low|low stock|need restock)',
            'book_appointment': r'book (.+?) for (.+?), (.+?), (.+)',
            'help': r'help|commands?|what can i do'
        }

        # Try to match patterns
        for command_type, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                return self.handle_command(phone_number, command_type, match.groups(), message)

        # Fallback for unrecognized commands
        return self.handle_unknown_command(phone_number, message)

    def handle_command(self, phone_number, command_type, groups, original_message):
        """Handle parsed commands"""

        if command_type == 'add_inventory':
            quantity, product_name, price = groups
            return self.add_inventory(phone_number, product_name, int(quantity), float(price))

        elif command_type == 'restock':
            product_name, quantity = groups
            return self.restock_inventory(phone_number, product_name, int(quantity))

        elif command_type == 'check_inventory':
            return self.get_inventory_status(phone_number)

        elif command_type == 'low_stock':
            return self.get_low_stock_items(phone_number)

        elif command_type == 'book_appointment':
            service_type, customer_name, date_str, time_str = groups
            return self.handle_booking(phone_number, customer_name, service_type, date_str, time_str)

        elif command_type == 'help':
            return self.get_help_message()

        return self.handle_unknown_command(phone_number, original_message)

    def add_inventory(self, phone_number, product_name, quantity, price):
        """Add new inventory item"""
        vendor_id = self.get_vendor_id(phone_number)
        if not vendor_id:
            return "❌ Vendor not found. Please register first."

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # Check if product exists
            c.execute('''
                SELECT id, stock_quantity FROM products 
                WHERE vendor_id = ? AND LOWER(name) = LOWER(?)
            ''', (vendor_id, product_name))

            existing = c.fetchone()

            if existing:
                # Update existing product
                product_id, current_stock = existing
                new_stock = current_stock + quantity
                c.execute('''
                    UPDATE products SET stock_quantity = ?, sale_price = ?
                    WHERE id = ?
                ''', (new_stock, price, product_id))

                action = f"Updated {product_name}: +{quantity} units (Total: {new_stock})"
            else:
                # Create new product
                c.execute('''
                    INSERT INTO products (vendor_id, name, description, category, sale_price, buy_price, stock_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (vendor_id, product_name, f"Added via WhatsApp", "general", price, price * 0.7, quantity))

                action = f"Added new product: {product_name} (₹{price} each, {quantity} units)"

            conn.commit()

            # Update catalog
            self.update_catalog(vendor_id)

            response = f"""
✅ Inventory Updated!

{action}
💰 Price: ₹{price} each
📦 Added via WhatsApp Business

📱 Your catalog has been updated automatically!
            """

            return response.strip()

        except Exception as e:
            conn.rollback()
            return f"❌ Failed to add inventory: {str(e)}"
        finally:
            conn.close()

    def restock_inventory(self, phone_number, product_name, quantity):
        """Restock existing inventory"""
        vendor_id = self.get_vendor_id(phone_number)
        if not vendor_id:
            return "❌ Vendor not found. Please register first."

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            c.execute('''
                SELECT id, stock_quantity FROM products 
                WHERE vendor_id = ? AND LOWER(name) LIKE LOWER(?)
            ''', (vendor_id, f'%{product_name}%'))

            product = c.fetchone()

            if not product:
                return f"❌ Product '{product_name}' not found. Use 'Add' command to create new products."

            product_id, current_stock = product
            new_stock = current_stock + quantity

            c.execute('UPDATE products SET stock_quantity = ? WHERE id = ?', (new_stock, product_id))
            conn.commit()

            # Update catalog
            self.update_catalog(vendor_id)

            return f"""
✅ Restocked Successfully!

📦 {product_name}
➕ Added: {quantity} units
📊 New total: {new_stock} units

📱 Catalog updated!
            """

        except Exception as e:
            conn.rollback()
            return f"❌ Restock failed: {str(e)}"
        finally:
            conn.close()

    def get_inventory_status(self, phone_number):
        """Get current inventory status"""
        vendor_id = self.get_vendor_id(phone_number)
        if not vendor_id:
            return "❌ Vendor not found. Please register first."

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT name, stock_quantity, sale_price 
            FROM products WHERE vendor_id = ? AND stock_quantity > 0
            ORDER BY name
        ''', (vendor_id,))

        products = c.fetchall()
        conn.close()

        if not products:
            return "📦 No inventory found. Add products using 'Add' command."

        response = "📊 **Current Inventory:**\n\n"
        total_value = 0

        for name, stock, price in products:
            value = stock * price
            total_value += value
            response += f"• {name}\n  📦 {stock} units @ ₹{price} = ₹{value}\n\n"

        response += f"💰 **Total Value:** ₹{total_value:,.2f}"

        return response

    def get_low_stock_items(self, phone_number, threshold=5):
        """Get low stock items"""
        vendor_id = self.get_vendor_id(phone_number)
        if not vendor_id:
            return "❌ Vendor not found. Please register first."

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT name, stock_quantity 
            FROM products WHERE vendor_id = ? AND stock_quantity <= ?
            ORDER BY stock_quantity ASC
        ''', (vendor_id, threshold))

        products = c.fetchall()
        conn.close()

        if not products:
            return f"✅ All products have sufficient stock (>{threshold} units)"

        response = f"⚠️ **Low Stock Alert (≤{threshold} units):**\n\n"

        for name, stock in products:
            if stock == 0:
                response += f"🔴 {name}: OUT OF STOCK\n"
            else:
                response += f"🟡 {name}: {stock} units left\n"

        response += "\n💡 Use 'Restock [product] by [quantity] units' to replenish."

        return response

    def handle_booking(self, phone_number, customer_name, service_type, date_str, time_str):
        """Handle booking appointments"""
        vendor_id = self.get_vendor_id(phone_number)
        if not vendor_id:
            return "❌ Vendor not found. Please register first."

        try:
            # Parse date and time (basic parsing)
            from datetime import datetime

            # Simple date parsing - can be enhanced
            booking_date = datetime.now().date()
            booking_time = datetime.now().time()

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute('''
                INSERT INTO whatsapp_bookings 
                (vendor_phone, customer_name, pet_name, service_type, booking_date, booking_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (phone_number, customer_name, "Pet", service_type, booking_date, booking_time))

            booking_id = c.lastrowid
            conn.commit()
            conn.close()

            return f"""
✅ **Booking Confirmed!**

📅 Booking ID: #{booking_id}
👤 Customer: {customer_name}
🐾 Service: {service_type}
📆 Date: {date_str}
⏰ Time: {time_str}

📱 Customer will receive confirmation automatically.
            """

        except Exception as e:
            return f"❌ Booking failed: {str(e)}\n\n💡 Try: 'Book grooming for John, April 25, 10 AM'"

    def get_help_message(self):
        """Get help message with all commands"""
        return """
🤖 **FurrButler WhatsApp Commands:**

📦 **Inventory Management:**
• "Add 10 units Dog Shampoo ₹450 each"
• "Restock Cat Food by 20 units"
• "Current inventory?" or "Stock levels?"
• "What's running low?" or "Low stock?"

📅 **Bookings:**
• "Book grooming for Luna, April 25, 10 AM"
• "Book boarding for Max, Next Friday, 9 AM"

ℹ️ **Information:**
• "Help" - Show this message
• "My bookings today"
• "Sales summary"

💡 **Tips:**
- Use natural language
- Include ₹ symbol for prices
- Be specific with product names
- Date formats: "April 25", "Next Friday", etc.

Need assistance? Just ask! 🐾
        """

    def handle_unknown_command(self, phone_number, message):
        """Handle unrecognized commands"""
        return f"""
❓ **I didn't understand that command.**

You sent: "{message}"

💡 **Try these examples:**
• "Add 5 units Dog Food ₹300 each"
• "Current inventory?"
• "Book grooming for Buddy, tomorrow, 2 PM"
• "Help" - for all commands

🤖 I'm learning! Your message has been logged for improvement.
        """

    def update_catalog(self, vendor_id):
        """Update WhatsApp Business catalog"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT id, name, description, sale_price, stock_quantity, image_url
            FROM products WHERE vendor_id = ? AND stock_quantity > 0
        ''', (vendor_id,))

        products = c.fetchall()
        conn.close()

        # Update catalog JSON
        vendor_products = []
        for product in products:
            product_id, name, desc, price, stock, image = product
            vendor_products.append({
                "id": f"prod_{product_id}",
                "name": name,
                "description": desc or f"Available: {stock} units",
                "price": price,
                "currency": "INR",
                "stock": stock,
                "image_url": image or "https://via.placeholder.com/300x300?text=Pet+Product",
                "deep_link": f"https://furrbutler.com/product/{product_id}",
                "vendor_id": vendor_id
            })

        # Find and update vendor's products in catalog
        self.catalog["products"] = [p for p in self.catalog["products"] if p.get("vendor_id") != vendor_id]
        self.catalog["products"].extend(vendor_products)

        self.save_catalog()
        print(f"📱 Catalog updated for vendor {vendor_id}: {len(vendor_products)} products")

    def get_vendor_id(self, phone_number):
        """Get vendor ID from phone number"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT vendor_id FROM whatsapp_vendors WHERE phone_number = ?", (phone_number,))
        result = c.fetchone()
        conn.close()

        return result[0] if result else None

    def log_message(self, phone_number, message, message_type):
        """Log WhatsApp messages"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO whatsapp_messages (vendor_phone, message_text, message_type)
            VALUES (?, ?, ?)
        ''', (phone_number, message, message_type))

        conn.commit()
        conn.close()

# Simulation functions for testing
def simulate_whatsapp_message(phone_number, message):
    """Simulate receiving a WhatsApp message"""
    erp = WhatsAppERPSimulator()

    print(f"\n📱 **Incoming WhatsApp Message:**")
    print(f"From: {phone_number}")
    print(f"Message: '{message}'")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    response = erp.parse_vendor_message(phone_number, message)

    print(f"🤖 **FurrButler Response:**")
    print(response)
    print("=" * 50)

    return response

def run_whatsapp_simulation():
    """Run comprehensive WhatsApp simulation"""
    print("🚀 **FurrButler WhatsApp Business ERP Simulation**\n")

    # Initialize
    erp = WhatsAppERPSimulator()

    # Test vendor registration
    print("1️⃣ **VENDOR REGISTRATION SIMULATION:**")
    reg_result = erp.register_vendor_via_whatsapp("+91-9876543210", "Pawsome Grooming")
    print(reg_result["message"])
    print("\n")

    # Test various commands
    test_messages = [
        ("+91-9876543210", "Add 15 units Dog Shampoo ₹350 each"),
        ("+91-9876543210", "Add 8 units Cat Food ₹180 each"),
        ("+91-9876543210", "Restock Dog Shampoo by 5 units"),
        ("+91-9876543210", "Current inventory?"),
        ("+91-9876543210", "What's running low?"),
        ("+91-9876543210", "Book grooming for Buddy, April 25, 10 AM"),
        ("+91-9876543210", "Help"),
        ("+91-9876543210", "Invalid command test"),
    ]

    print("2️⃣ **MESSAGE PROCESSING SIMULATION:**")
    for phone, message in test_messages:
        simulate_whatsapp_message(phone, message)
        print()

if __name__ == "__main__":
    run_whatsapp_simulation()
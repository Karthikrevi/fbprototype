import sqlite3
import random
from datetime import datetime, timedelta

def populate_test_data():
    print("Starting test data population...")
    
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Create test vendors
    vendors = [
        ("Fluffy Grooming", "fluffy@erp.com", "test123", "Grooming", "Mumbai", "+91-9876543210"),
        ("Waggy Tails", "waggy@erp.com", "test123", "Grooming", "Delhi", "+91-9876543211"),
        ("Royal Pets", "royal@erp.com", "test123", "Boarding", "Bangalore", "+91-9876543212")
    ]
    
    for vendor in vendors:
        c.execute("""
            INSERT OR IGNORE INTO vendors (name, email, password, category, city, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, vendor)
    
    conn.commit()
    conn.close()
    
    print("Test data populated successfully!")

if __name__ == "__main__":
    populate_test_data()

def create_test_vendors():
    """Create 3 test vendor accounts"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    vendors_data = [
        {
            'name': 'Fluffy Paws',
            'email': 'fluffy@erp.com',
            'password': 'test123',
            'phone': '+91-9876543210',
            'city': 'Mumbai',
            'category': 'Pet Store',
            'bio': 'Premium pet products and supplies in Mumbai',
            'months_history': 3
        },
        {
            'name': 'Waggy Tails',
            'email': 'waggy@erp.com', 
            'password': 'test123',
            'phone': '+91-9876543211',
            'city': 'Delhi',
            'category': 'Pet Store & Grooming',
            'bio': 'Complete pet care services and grooming in Delhi',
            'months_history': 6
        },
        {
            'name': 'Royal Woofs',
            'email': 'royal@erp.com',
            'password': 'test123', 
            'phone': '+91-9876543212',
            'city': 'Bangalore',
            'category': 'Premium Pet Services',
            'bio': 'Luxury pet services and premium products in Bangalore',
            'months_history': 12
        }
    ]

    vendor_ids = []

    for vendor in vendors_data:
        # Use plain text password to match Flask app's authentication system
        plain_password = vendor['password']

        try:
            c.execute("""
                INSERT INTO vendors (name, email, password, phone, city, category, bio, is_online)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (vendor['name'], vendor['email'], plain_password, vendor['phone'], 
                  vendor['city'], vendor['category'], vendor['bio']))

            vendor_id = c.lastrowid
            vendor_ids.append({'id': vendor_id, 'months_history': vendor['months_history'], 'name': vendor['name']})
            print(f"Created vendor: {vendor['name']} (ID: {vendor_id})")

        except sqlite3.IntegrityError:
            print(f"Vendor {vendor['name']} already exists, getting ID...")
            c.execute("SELECT id FROM vendors WHERE email = ?", (vendor['email'],))
            result = c.fetchone()
            if result:
                vendor_ids.append({'id': result[0], 'months_history': vendor['months_history'], 'name': vendor['name']})

    conn.commit()
    conn.close()
    return vendor_ids

def create_products_for_vendor(vendor_id, vendor_name):
    """Create 10 products for each vendor across different categories"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Clear existing products for this vendor
    c.execute("DELETE FROM products WHERE vendor_id = ?", (vendor_id,))

    categories = ['Pet Food', 'Toys', 'Grooming Supplies', 'Health Products', 'Accessories']

    products_data = [
        # Pet Food
        {'name': 'Premium Dog Food (5kg)', 'category': 'Pet Food', 'buy_price': 800, 'sale_price': 1200, 'quantity': random.randint(50, 200)},
        {'name': 'Cat Treats (500g)', 'category': 'Pet Food', 'buy_price': 150, 'sale_price': 250, 'quantity': random.randint(30, 150)},

        # Toys
        {'name': 'Squeaky Ball Set', 'category': 'Toys', 'buy_price': 200, 'sale_price': 350, 'quantity': random.randint(40, 120)},
        {'name': 'Interactive Puzzle Toy', 'category': 'Toys', 'buy_price': 500, 'sale_price': 800, 'quantity': random.randint(20, 80)},

        # Grooming Supplies
        {'name': 'Pet Shampoo (250ml)', 'category': 'Grooming Supplies', 'buy_price': 300, 'sale_price': 450, 'quantity': random.randint(25, 100)},
        {'name': 'Nail Clippers', 'category': 'Grooming Supplies', 'buy_price': 400, 'sale_price': 600, 'quantity': random.randint(15, 60)},

        # Health Products
        {'name': 'Vitamin Supplements', 'category': 'Health Products', 'buy_price': 600, 'sale_price': 950, 'quantity': random.randint(30, 90)},
        {'name': 'Flea & Tick Spray', 'category': 'Health Products', 'buy_price': 250, 'sale_price': 400, 'quantity': random.randint(20, 80)},

        # Accessories
        {'name': 'Designer Pet Collar', 'category': 'Accessories', 'buy_price': 300, 'sale_price': 550, 'quantity': random.randint(25, 100)},
        {'name': 'Pet Carrier Bag', 'category': 'Accessories', 'buy_price': 1200, 'sale_price': 1800, 'quantity': random.randint(10, 50)}
    ]

    product_ids = []

    for product in products_data:
        c.execute("""
            INSERT INTO products (vendor_id, name, category, buy_price, sale_price, quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, product['name'], product['category'], product['buy_price'], 
              product['sale_price'], product['quantity']))

        product_id = c.lastrowid
        product_ids.append({
            'id': product_id,
            'name': product['name'],
            'sale_price': product['sale_price'],
            'category': product['category']
        })

    conn.commit()
    conn.close()
    print(f"Created {len(products_data)} products for {vendor_name}")
    return product_ids

def create_sales_data(vendor_id, vendor_name, product_ids, months_history):
    """Generate realistic sales data for the specified time period"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Clear existing sales data for this vendor
    c.execute("DELETE FROM sales_log WHERE vendor_id = ?", (vendor_id,))

    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_history * 30)

    sales_count = 0
    current_date = start_date

    # Create different sale patterns for different products
    fast_moving = product_ids[:3]  # First 3 products are fast-moving
    slow_moving = product_ids[3:6]  # Next 3 are slow-moving
    stagnant = product_ids[6:]      # Rest are stagnant

    while current_date <= end_date:
        # Fast-moving products: 2-5 sales per day
        for product in fast_moving:
            if random.random() < 0.8:  # 80% chance of sale
                quantity = random.randint(1, 3)
                total_amount = quantity * product['sale_price']
                total_cogs = quantity * (product['sale_price'] * 0.6)  # Assume 60% COGS
                product_name = product['name']

                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, current_date.strftime('%Y-%m-%d')))
                sales_count += 1

                # Add to ledger - COGS (Debit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'debit', 'Cost of Goods Sold', ?, ?, 'Product Sales')
                """, (vendor_id, total_cogs, f"COGS - {product_name} x{quantity}"))

                # Add to ledger - Sales Revenue (Credit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'credit', 'Sales Revenue', ?, ?, 'Product Sales')
                """, (vendor_id, total_amount, f"Sales Revenue - {product_name} x{quantity}"))

        # Slow-moving products: 1-2 sales per week
        for product in slow_moving:
            if random.random() < 0.15:  # 15% chance of sale
                quantity = random.randint(1, 2)
                total_amount = quantity * product['sale_price']
                total_cogs = quantity * (product['sale_price'] * 0.6)  # Assume 60% COGS
                product_name = product['name']

                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, current_date.strftime('%Y-%m-%d')))
                sales_count += 1

                # Add to ledger - COGS (Debit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'debit', 'Cost of Goods Sold', ?, ?, 'Product Sales')
                """, (vendor_id, total_cogs, f"COGS - {product_name} x{quantity}"))

                # Add to ledger - Sales Revenue (Credit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'credit', 'Sales Revenue', ?, ?, 'Product Sales')
                """, (vendor_id, total_amount, f"Sales Revenue - {product_name} x{quantity}"))

        # Stagnant products: very rare sales
        for product in stagnant:
            if random.random() < 0.02:  # 2% chance of sale
                quantity = 1
                total_amount = product['sale_price']
                total_cogs = quantity * (product['sale_price'] * 0.6)  # Assume 60% COGS
                product_name = product['name']

                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, current_date.strftime('%Y-%m-%d')))
                sales_count += 1

                # Add to ledger - COGS (Debit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'debit', 'Cost of Goods Sold', ?, ?, 'Product Sales')
                """, (vendor_id, total_cogs, f"COGS - {product_name} x{quantity}"))

                # Add to ledger - Sales Revenue (Credit)
                c.execute("""
                    INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                    VALUES (?, 'credit', 'Sales Revenue', ?, ?, 'Product Sales')
                """, (vendor_id, total_amount, f"Sales Revenue - {product_name} x{quantity}"))

        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"Created {sales_count} sales records for {vendor_name}")

def create_grooming_services():
    """Create grooming services in the system"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Check if table exists, if not create it
    c.execute("""
        CREATE TABLE IF NOT EXISTS grooming_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            service_name TEXT,
            price REAL,
            duration_minutes INTEGER,
            description TEXT,
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    """)

    # Clear existing services
    c.execute("DELETE FROM grooming_services")

    services_data = [
        {'name': 'Basic Haircut', 'price': 500, 'duration': 60, 'description': 'Professional pet grooming and styling'},
        {'name': 'Nail Trim', 'price': 200, 'duration': 30, 'description': 'Safe nail clipping and filing'},
        {'name': 'Dental Clean', 'price': 800, 'duration': 90, 'description': 'Complete dental cleaning and checkup'},
        {'name': 'Spa Bath', 'price': 600, 'duration': 75, 'description': 'Relaxing bath with premium shampoo and conditioning'}
    ]

    # Get all vendor IDs
    c.execute("SELECT id FROM vendors")
    vendor_ids = [row[0] for row in c.fetchall()]

    for vendor_id in vendor_ids:
        for service in services_data:
            c.execute("""
                INSERT INTO grooming_services (vendor_id, service_name, price, duration_minutes, description)
                VALUES (?, ?, ?, ?, ?)
            """, (vendor_id, service['name'], service['price'], service['duration'], service['description']))

    conn.commit()
    conn.close()
    print("Created grooming services for all vendors")

def create_grooming_bookings(vendor_ids):
    """Create grooming bookings data"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Check if bookings table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS grooming_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            service_id INTEGER,
            customer_name TEXT,
            pet_name TEXT,
            booking_date TEXT,
            service_price REAL,
            status TEXT DEFAULT 'Completed',
            FOREIGN KEY (vendor_id) REFERENCES vendors (id),
            FOREIGN KEY (service_id) REFERENCES grooming_services (id)
        )
    """)

    # Clear existing bookings
    c.execute("DELETE FROM grooming_bookings")

    customer_names = ['John Smith', 'Sarah Johnson', 'Mike Brown', 'Lisa Wilson', 'Tom Davis', 'Emma Thompson']
    pet_names = ['Buddy', 'Luna', 'Max', 'Bella', 'Charlie', 'Lucy', 'Rocky', 'Daisy']

    for vendor_info in vendor_ids:
        vendor_id = vendor_info['id']
        months_history = vendor_info['months_history']

        # Get services for this vendor
        c.execute("SELECT id, service_name, price FROM grooming_services WHERE vendor_id = ?", (vendor_id,))
        services = c.fetchall()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_history * 30)

        bookings_count = 0
        current_date = start_date

        while current_date <= end_date:
            # Random bookings (1-3 per week)
            if random.random() < 0.3:  # 30% chance of booking each day
                service = random.choice(services)
                customer = random.choice(customer_names)
                pet = random.choice(pet_names)

                c.execute("""
                    INSERT INTO grooming_bookings (vendor_id, service_id, customer_name, pet_name, booking_date, service_price, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Completed')
                """, (vendor_id, service[0], customer, pet, current_date.strftime('%Y-%m-%d'), service[2]))
                bookings_count += 1

            current_date += timedelta(days=1)

        print(f"Created {bookings_count} grooming bookings for {vendor_info['name']}")

    conn.commit()
    conn.close()

def update_ledger_entries(vendor_ids):
    """Create ledger entries for sales and expenses"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    for vendor_info in vendor_ids:
        vendor_id = vendor_info['id']

        # Get total sales for this vendor
        c.execute("SELECT SUM(total_amount) FROM sales_log WHERE vendor_id = ?", (vendor_id,))
        total_sales = c.fetchone()[0] or 0

        # Get total grooming revenue
        c.execute("SELECT SUM(service_price) FROM grooming_bookings WHERE vendor_id = ?", (vendor_id,))
        total_grooming = c.fetchone()[0] or 0

        # Add sales revenue entry
        if total_sales > 0:
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'debit', 'Sales Revenue', ?, 'Product Sales Revenue', 'Product Sales')
            """, (vendor_id, total_sales))

        # Add grooming revenue entry
        if total_grooming > 0:
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'debit', 'Service Revenue', ?, 'Grooming Services Revenue', 'Service Revenue')
            """, (vendor_id, total_grooming))

        # Add some expense entries
        expenses = [
            ('Rent', random.randint(10000, 25000), 'Monthly Rent'),
            ('Utilities', random.randint(3000, 8000), 'Electricity and Water'),
            ('Marketing', random.randint(5000, 15000), 'Advertising and Promotion'),
            ('Supplies', random.randint(8000, 20000), 'Inventory and Supplies')
        ]

        for expense_type, amount, desc in expenses:
            c.execute("""
                INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
                VALUES (?, 'credit', ?, ?, ?, 'Operating Expenses')
            """, (vendor_id, expense_type, amount, desc))

    conn.commit()
    conn.close()
    print("Updated ledger entries for all vendors")

def main():
    """Main function to populate all test data"""
    print("🐾 Starting FurrButler ERP Test Data Population...")
    print("=" * 50)

    # Step 1: Create vendors
    print("1. Creating vendor accounts...")
    vendor_ids = create_test_vendors()

    # Step 2: Create products for each vendor
    print("\n2. Creating products...")
    all_product_ids = {}
    for vendor_info in vendor_ids:
        vendor_id = vendor_info['id']
        vendor_name = vendor_info['name']
        product_ids = create_products_for_vendor(vendor_id, vendor_name)
        all_product_ids[vendor_id] = product_ids

    # Step 3: Create sales data
    print("\n3. Generating sales data...")
    for vendor_info in vendor_ids:
        vendor_id = vendor_info['id']
        vendor_name = vendor_info['name']
        months_history = vendor_info['months_history']
        product_ids = all_product_ids[vendor_id]
        create_sales_data(vendor_id, vendor_name, product_ids, months_history)

    # Step 4: Create grooming services
    print("\n4. Creating grooming services...")
    create_grooming_services()

    # Step 5: Create grooming bookings
    print("\n5. Generating grooming bookings...")
    create_grooming_bookings(vendor_ids)

    # Step 6: Update ledger entries
    print("\n6. Updating accounting ledgers...")
    update_ledger_entries(vendor_ids)

    print("\n" + "=" * 50)
    print("✅ Test data population completed successfully!")
    print("\n📋 Summary:")
    print("• 3 Vendor accounts created")
    print("• 10 Products per vendor (30 total)")
    print("• Sales data spanning 3-12 months")
    print("• 4 Grooming services per vendor")
    print("• Realistic booking history")
    print("• Complete accounting entries")
    print("\n🔐 Login Credentials:")
    print("• fluffy@erp.com / test123 (3 months history)")
    print("• waggy@erp.com / test123 (6 months history)")
    print("• royal@erp.com / test123 (12 months history)")
    print("\nYou can now test all reporting and analytics modules!")

if __name__ == "__main__":
    populate_test_data()e__ == "__main__":
    main()
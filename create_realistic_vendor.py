
import sqlite3
import random
from datetime import datetime, timedelta

def create_realistic_vendor():
    """Create a realistic vendor with sample data"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Create realistic vendor
    c.execute("""
        INSERT OR IGNORE INTO vendors (name, email, password, category, city, phone, bio, image_url, is_online)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("Pawsome Pets", "pawsome@erp.com", "demo123", "Pet Store", "Mumbai", "+91-9876543210", 
          "Complete pet care solutions", "https://images.unsplash.com/photo-1522075469751-3847ae47cab9", 1))
    
    vendor_id = c.lastrowid
    
    # Add sample products
    products = [
        ("Premium Dog Food", "High-quality nutritious dog food", "Food", 800, 1200, 50, "DOG_FOOD_001"),
        ("Cat Litter", "Odor-control cat litter", "Accessories", 300, 450, 30, "CAT_LITTER_001"),
        ("Pet Toy Ball", "Interactive toy for dogs", "Toys", 150, 250, 25, "TOY_BALL_001")
    ]
    
    for product in products:
        c.execute("""
            INSERT OR IGNORE INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id,) + product)
    
    conn.commit()
    conn.close()
    
    print("Realistic vendor created successfully!")

if __name__ == "__main__":
    create_realistic_vendor()

def create_realistic_vendor():
    """Create a comprehensive vendor with realistic performance data"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    print("🐾 Creating Realistic Vendor Account...")
    
    # Create the vendor
    vendor_data = {
        'name': 'PetCare Pro',
        'email': 'petcare@erp.com',
        'password': 'test123',
        'phone': '+91-8888888888',
        'city': 'Bangalore',
        'category': 'Pet Store & Services',
        'bio': 'Premium pet care products and services with 8+ years of experience',
        'is_online': 1
    }
    
    try:
        c.execute("""
            INSERT INTO vendors (name, email, password, phone, city, category, bio, is_online)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vendor_data['name'], vendor_data['email'], vendor_data['password'], 
              vendor_data['phone'], vendor_data['city'], vendor_data['category'], 
              vendor_data['bio'], vendor_data['is_online']))
        
        vendor_id = c.lastrowid
        print(f"✅ Created vendor: {vendor_data['name']} (ID: {vendor_id})")
        
    except sqlite3.IntegrityError:
        print("📝 Vendor already exists, getting existing ID...")
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_data['email'],))
        vendor_id = c.fetchone()[0]
        
        # Clear existing data for this vendor
        c.execute("DELETE FROM products WHERE vendor_id = ?", (vendor_id,))
        c.execute("DELETE FROM sales_log WHERE vendor_id = ?", (vendor_id,))
        c.execute("DELETE FROM inventory_batches WHERE product_id IN (SELECT id FROM products WHERE vendor_id = ?)", (vendor_id,))
        c.execute("DELETE FROM ledger_entries WHERE vendor_id = ?", (vendor_id,))
        c.execute("DELETE FROM expenses WHERE vendor_id = ?", (vendor_id,))
        print("🗑️ Cleared existing data for vendor")
    
    conn.commit()
    return vendor_id, conn, c

def create_realistic_products(vendor_id, conn, c):
    """Create products with different performance levels"""
    print("\n📦 Creating Product Portfolio...")
    
    # HIGH PERFORMERS (Top 20% - Fast moving, high margin)
    high_performers = [
        {'name': 'Premium Dog Food Royal Canin (10kg)', 'category': 'Pet Food', 'buy_price': 2800, 'sale_price': 3500, 'quantity': 180, 'performance': 'high'},
        {'name': 'Cat Litter Clumping (15kg)', 'category': 'Pet Care', 'buy_price': 800, 'sale_price': 1200, 'quantity': 250, 'performance': 'high'},
        {'name': 'Interactive Puzzle Feeder', 'category': 'Toys', 'buy_price': 450, 'sale_price': 750, 'quantity': 120, 'performance': 'high'},
        {'name': 'Flea & Tick Prevention Spray', 'category': 'Health', 'buy_price': 300, 'sale_price': 500, 'quantity': 200, 'performance': 'high'},
    ]
    
    # MID PERFORMERS (Middle 60% - Moderate sales, decent margins)
    mid_performers = [
        {'name': 'Dog Treats Chicken Jerky (500g)', 'category': 'Pet Food', 'buy_price': 200, 'sale_price': 350, 'quantity': 150, 'performance': 'mid'},
        {'name': 'Pet Shampoo Herbal (250ml)', 'category': 'Grooming', 'buy_price': 180, 'sale_price': 280, 'quantity': 100, 'performance': 'mid'},
        {'name': 'Rope Toy Large', 'category': 'Toys', 'buy_price': 150, 'sale_price': 250, 'quantity': 80, 'performance': 'mid'},
        {'name': 'Pet Bed Memory Foam Medium', 'category': 'Accessories', 'buy_price': 800, 'sale_price': 1200, 'quantity': 40, 'performance': 'mid'},
        {'name': 'Nail Clippers Professional', 'category': 'Grooming', 'buy_price': 200, 'sale_price': 320, 'quantity': 60, 'performance': 'mid'},
        {'name': 'Water Bowl Stainless Steel', 'category': 'Accessories', 'buy_price': 300, 'sale_price': 450, 'quantity': 70, 'performance': 'mid'},
        {'name': 'Vitamin Supplements Multi', 'category': 'Health', 'buy_price': 400, 'sale_price': 600, 'quantity': 50, 'performance': 'mid'},
        {'name': 'Leash Retractable 5m', 'category': 'Accessories', 'buy_price': 350, 'sale_price': 550, 'quantity': 45, 'performance': 'mid'},
    ]
    
    # LOW PERFORMERS (Bottom 20% - Slow moving, low margins, seasonal)
    low_performers = [
        {'name': 'Luxury Pet Cologne (50ml)', 'category': 'Grooming', 'buy_price': 500, 'sale_price': 650, 'quantity': 30, 'performance': 'low'},
        {'name': 'Designer Pet Sunglasses', 'category': 'Accessories', 'buy_price': 400, 'sale_price': 500, 'quantity': 25, 'performance': 'low'},
        {'name': 'Automatic Pet Feeder Premium', 'category': 'Tech', 'buy_price': 2500, 'sale_price': 3200, 'quantity': 15, 'performance': 'low'},
        {'name': 'Pet Stroller Deluxe', 'category': 'Accessories', 'buy_price': 3000, 'sale_price': 3800, 'quantity': 8, 'performance': 'low'},
        {'name': 'Holiday Pet Costume Set', 'category': 'Seasonal', 'buy_price': 300, 'sale_price': 400, 'quantity': 20, 'performance': 'low'},
        {'name': 'Pet Massage Oil (100ml)', 'category': 'Wellness', 'buy_price': 250, 'sale_price': 350, 'quantity': 18, 'performance': 'low'},
        {'name': 'GPS Pet Tracker', 'category': 'Tech', 'buy_price': 1500, 'sale_price': 2000, 'quantity': 12, 'performance': 'low'},
        {'name': 'Pet Birthday Cake Mix', 'category': 'Seasonal', 'buy_price': 150, 'sale_price': 200, 'quantity': 22, 'performance': 'low'},
    ]
    
    all_products = high_performers + mid_performers + low_performers
    product_data = []
    
    for product in all_products:
        c.execute("""
            INSERT INTO products (vendor_id, name, category, buy_price, sale_price, quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_id, product['name'], product['category'], product['buy_price'], 
              product['sale_price'], product['quantity']))
        
        product_id = c.lastrowid
        product_data.append({
            'id': product_id,
            'name': product['name'],
            'category': product['category'],
            'buy_price': product['buy_price'],
            'sale_price': product['sale_price'],
            'quantity': product['quantity'],
            'performance': product['performance']
        })
        
        # Create initial inventory batch
        c.execute("""
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        """, (product_id, product['quantity'], product['buy_price'], product['quantity']))
    
    conn.commit()
    print(f"✅ Created {len(all_products)} products:")
    print(f"   🚀 High Performers: {len(high_performers)}")
    print(f"   📈 Mid Performers: {len(mid_performers)}")
    print(f"   🐌 Low Performers: {len(low_performers)}")
    
    return product_data

def generate_realistic_sales(vendor_id, product_data, conn, c):
    """Generate 6 months of realistic sales data with different performance patterns"""
    print("\n💰 Generating 6 Months of Sales Data...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    current_date = start_date
    total_sales = 0
    total_revenue = 0
    
    # Customer names for variety
    customers = [
        'john@customer.com', 'sarah@customer.com', 'mike@customer.com',
        'lisa@customer.com', 'tom@customer.com', 'emma@customer.com',
        'raj@customer.com', 'priya@customer.com', 'amit@customer.com',
        'deepa@customer.com', '', ''  # Empty strings for POS sales
    ]
    
    while current_date <= end_date:
        # HIGH PERFORMERS: 3-8 sales per day (80% probability)
        for product in [p for p in product_data if p['performance'] == 'high']:
            if random.random() < 0.80:  # 80% chance
                quantity = random.randint(1, 4)
                customer = random.choice(customers)
                total_amount = quantity * product['sale_price']
                cogs = quantity * product['buy_price']
                
                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, customer_email, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, customer, current_date.strftime('%Y-%m-%d')))
                
                total_sales += 1
                total_revenue += total_amount
                
                # Update inventory
                c.execute("""
                    UPDATE inventory_batches 
                    SET remaining_quantity = remaining_quantity - ? 
                    WHERE product_id = ? AND remaining_quantity > 0
                    ORDER BY date_added ASC
                    LIMIT 1
                """, (quantity, product['id']))
        
        # MID PERFORMERS: 1-3 sales per day (40% probability)
        for product in [p for p in product_data if p['performance'] == 'mid']:
            if random.random() < 0.40:  # 40% chance
                quantity = random.randint(1, 2)
                customer = random.choice(customers)
                total_amount = quantity * product['sale_price']
                cogs = quantity * product['buy_price']
                
                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, customer_email, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, customer, current_date.strftime('%Y-%m-%d')))
                
                total_sales += 1
                total_revenue += total_amount
                
                # Update inventory
                c.execute("""
                    UPDATE inventory_batches 
                    SET remaining_quantity = remaining_quantity - ? 
                    WHERE product_id = ? AND remaining_quantity > 0
                    ORDER BY date_added ASC
                    LIMIT 1
                """, (quantity, product['id']))
        
        # LOW PERFORMERS: 0-1 sales per day (10% probability)
        for product in [p for p in product_data if p['performance'] == 'low']:
            if random.random() < 0.10:  # 10% chance
                quantity = 1
                customer = random.choice(customers)
                total_amount = quantity * product['sale_price']
                cogs = quantity * product['buy_price']
                
                c.execute("""
                    INSERT INTO sales_log (vendor_id, product_id, quantity, unit_price, total_amount, customer_email, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (vendor_id, product['id'], quantity, product['sale_price'], total_amount, customer, current_date.strftime('%Y-%m-%d')))
                
                total_sales += 1
                total_revenue += total_amount
                
                # Update inventory
                c.execute("""
                    UPDATE inventory_batches 
                    SET remaining_quantity = remaining_quantity - ? 
                    WHERE product_id = ? AND remaining_quantity > 0
                    ORDER BY date_added ASC
                    LIMIT 1
                """, (quantity, product['id']))
        
        current_date += timedelta(days=1)
    
    conn.commit()
    
    print(f"✅ Generated {total_sales} sales transactions")
    print(f"💰 Total Revenue: ₹{total_revenue:,.2f}")
    return total_sales, total_revenue

def create_expenses(vendor_id, conn, c):
    """Create realistic business expenses"""
    print("\n💸 Creating Business Expenses...")
    
    # Monthly recurring expenses
    monthly_expenses = [
        {'category': 'Rent', 'amount': 25000, 'description': 'Monthly store rent'},
        {'category': 'Utilities', 'amount': 8000, 'description': 'Electricity, water, internet'},
        {'category': 'Staff Salary', 'amount': 45000, 'description': 'Employee salaries'},
        {'category': 'Insurance', 'amount': 5000, 'description': 'Business insurance'},
    ]
    
    # Variable expenses
    variable_expenses = [
        {'category': 'Marketing', 'amount': 12000, 'description': 'Social media advertising'},
        {'category': 'Supplies', 'amount': 8000, 'description': 'Packaging and supplies'},
        {'category': 'Transportation', 'amount': 6000, 'description': 'Delivery and logistics'},
        {'category': 'Maintenance', 'amount': 4000, 'description': 'Equipment maintenance'},
    ]
    
    # Create 6 months of expenses
    total_expenses = 0
    for month in range(6):
        expense_date = (datetime.now() - timedelta(days=30*month)).strftime('%Y-%m-%d')
        
        # Monthly expenses
        for expense in monthly_expenses:
            amount = expense['amount'] + random.randint(-2000, 2000)  # Add some variation
            c.execute("""
                INSERT INTO expenses (vendor_id, category, amount, description, date)
                VALUES (?, ?, ?, ?, ?)
            """, (vendor_id, expense['category'], amount, expense['description'], expense_date))
            total_expenses += amount
        
        # Variable expenses (not every month)
        for expense in variable_expenses:
            if random.random() < 0.7:  # 70% chance
                amount = expense['amount'] + random.randint(-1000, 1000)
                c.execute("""
                    INSERT INTO expenses (vendor_id, category, amount, description, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (vendor_id, expense['category'], amount, expense['description'], expense_date))
                total_expenses += amount
    
    conn.commit()
    print(f"✅ Created expenses totaling ₹{total_expenses:,.2f}")
    return total_expenses

def create_ledger_entries(vendor_id, total_revenue, total_expenses, conn, c):
    """Create proper ledger entries for accounting"""
    print("\n📊 Creating Ledger Entries...")
    
    # Sales Revenue (Credit)
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
        VALUES (?, 'credit', 'Sales Revenue', ?, 'Product sales revenue', 'Revenue')
    """, (vendor_id, total_revenue))
    
    # COGS (Debit) - Estimate 60% of revenue
    cogs = total_revenue * 0.60
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
        VALUES (?, 'debit', 'Cost of Goods Sold', ?, 'Cost of goods sold', 'COGS')
    """, (vendor_id, cogs))
    
    # Operating Expenses (Debit)
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
        VALUES (?, 'debit', 'Operating Expenses', ?, 'Business operating expenses', 'Expenses')
    """, (vendor_id, total_expenses))
    
    # Inventory Asset (Debit)
    inventory_value = total_revenue * 0.40  # Remaining inventory value
    c.execute("""
        INSERT INTO ledger_entries (vendor_id, entry_type, account, amount, description, sub_category)
        VALUES (?, 'debit', 'Inventory', ?, 'Inventory asset value', 'Assets')
    """, (vendor_id, inventory_value))
    
    conn.commit()
    print("✅ Ledger entries created")

def update_product_quantities(vendor_id, conn, c):
    """Update product quantities based on sales"""
    print("\n🔄 Updating Product Quantities...")
    
    # Recalculate quantities from inventory batches
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
    print("✅ Product quantities updated")

def create_vendor_settings(vendor_id, conn, c):
    """Create vendor-specific settings"""
    print("\n⚙️ Creating Vendor Settings...")
    
    c.execute("""
        INSERT OR REPLACE INTO settings_vendor 
        (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports, 
         standard_delivery_price, express_delivery_price, same_day_delivery_price, free_delivery_threshold)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vendor_id, 18.0, 10.0, 1, 1, 1, 2.99, 5.99, 12.99, 50.00))
    
    conn.commit()
    print("✅ Vendor settings configured")

def main():
    """Main function to create realistic vendor"""
    print("🌟 Creating Realistic Vendor with Performance Analytics Data")
    print("=" * 60)
    
    # Step 1: Create vendor
    vendor_id, conn, c = create_realistic_vendor()
    
    # Step 2: Create products with different performance levels
    product_data = create_realistic_products(vendor_id, conn, c)
    
    # Step 3: Generate realistic sales data
    total_sales, total_revenue = generate_realistic_sales(vendor_id, product_data, conn, c)
    
    # Step 4: Create business expenses
    total_expenses = create_expenses(vendor_id, conn, c)
    
    # Step 5: Create ledger entries
    create_ledger_entries(vendor_id, total_revenue, total_expenses, conn, c)
    
    # Step 6: Update product quantities
    update_product_quantities(vendor_id, conn, c)
    
    # Step 7: Create vendor settings
    create_vendor_settings(vendor_id, conn, c)
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 REALISTIC VENDOR CREATED SUCCESSFULLY!")
    print("\n📊 Performance Summary:")
    print(f"• Total Products: {len(product_data)}")
    print(f"• High Performers: 4 (fast-moving, high demand)")
    print(f"• Mid Performers: 8 (moderate sales, decent margins)")
    print(f"• Low Performers: 8 (slow-moving, seasonal/luxury)")
    print(f"• Total Sales: {total_sales} transactions")
    print(f"• Total Revenue: ₹{total_revenue:,.2f}")
    print(f"• Total Expenses: ₹{total_expenses:,.2f}")
    print(f"• Net Profit: ₹{total_revenue - total_expenses:,.2f}")
    print(f"• Data Period: 6 months")
    
    print("\n🔐 Login Credentials:")
    print("• Email: petcare@erp.com")
    print("• Password: test123")
    
    print("\n📈 Analytics You Can Now Test:")
    print("• Inventory Analytics - See velocity classifications")
    print("• Sales Analytics - View performance patterns")
    print("• P&L Reports - Complete financial picture")
    print("• Inventory Reports - Stock levels and turnover")
    print("• Expense Management - Realistic cost structure")
    print("• General Ledger - Complete accounting entries")
    
    print("\n✨ This vendor has realistic business patterns perfect for testing!")

if __name__ == "__main__":
    main()

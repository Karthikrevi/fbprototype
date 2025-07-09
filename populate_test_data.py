
import sqlite3
from datetime import datetime

def delete_existing_vendors():
    """Delete all existing test vendors from the database"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    print("🗑️ Deleting existing test vendors...")

    # Delete in proper order to maintain foreign key constraints
    c.execute("DELETE FROM platform_earnings")
    c.execute("DELETE FROM platform_fees") 
    c.execute("DELETE FROM sales_log")
    c.execute("DELETE FROM receipts")
    c.execute("DELETE FROM bookings")
    c.execute("DELETE FROM order_items")
    c.execute("DELETE FROM orders")
    c.execute("DELETE FROM inventory_batches")
    c.execute("DELETE FROM product_batches")
    c.execute("DELETE FROM products")
    c.execute("DELETE FROM ledger_entries")
    c.execute("DELETE FROM expenses")
    c.execute("DELETE FROM settings_vendor")
    c.execute("DELETE FROM reviews")

    # Keep the demo vendor but delete other test vendors
    c.execute("DELETE FROM vendors WHERE email != 'demo@furrbutler.com'")

    conn.commit()
    conn.close()
    print("✅ Existing test vendors deleted successfully!")

def create_test_vendors():
    """Create new test vendor accounts with proper login functionality"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Test vendor accounts with simple, working credentials
    test_vendors = [
        {
            'name': 'Paws & Claws Grooming',
            'email': 'test1@vendor.com',
            'password': 'test123',
            'category': 'Groomer',
            'city': 'Trivandrum',
            'phone': '+91-9876543210',
            'bio': 'Premium grooming services for all breeds. Professional and caring staff.',
            'image_url': 'https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        },
        {
            'name': 'Pet Paradise Store',
            'email': 'test2@vendor.com',
            'password': 'test123',
            'category': 'Pet Store',
            'city': 'Trivandrum',
            'phone': '+91-9876543211',
            'bio': 'Complete pet supplies store with food, toys, and accessories.',
            'image_url': 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        },
        {
            'name': 'Happy Tails Boarding',
            'email': 'test3@vendor.com',
            'password': 'test123',
            'category': 'Boarding',
            'city': 'Trivandrum',
            'phone': '+91-9876543212',
            'bio': 'Safe and comfortable boarding facilities for your beloved pets.',
            'image_url': 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        },
        {
            'name': 'Furry Friends Pharmacy',
            'email': 'test4@vendor.com',
            'password': 'test123',
            'category': 'Pharmacy',
            'city': 'Trivandrum',
            'phone': '+91-9876543213',
            'bio': 'Complete pharmacy with medicines, vitamins, and health products for pets.',
            'image_url': 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        }
    ]

    print("👥 Creating new test vendor accounts...")

    for vendor in test_vendors:
        try:
            c.execute('''
                INSERT INTO vendors 
                (name, email, password, category, city, phone, bio, image_url, latitude, longitude, is_online, account_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                vendor['name'], vendor['email'], vendor['password'], vendor['category'], 
                vendor['city'], vendor['phone'], vendor['bio'], vendor['image_url'],
                vendor['latitude'], vendor['longitude'], vendor['is_online']
            ))

            vendor_id = c.lastrowid

            # Create default settings for each vendor
            c.execute('''
                INSERT INTO settings_vendor 
                (vendor_id, gst_rate, platform_fee, razorpay_enabled, cod_enabled, auto_reports)
                VALUES (?, 18.0, 10.0, 1, 1, 0)
            ''', (vendor_id,))

            # Add some sample products for each vendor
            create_sample_products(c, vendor_id, vendor['category'])

            print(f"✅ Created vendor: {vendor['email']} / {vendor['password']}")

        except Exception as e:
            print(f"❌ Error creating vendor {vendor['email']}: {e}")

    conn.commit()
    conn.close()

    print("\n🎉 Test vendor accounts created successfully!")
    print("\n📧 Login Credentials (Email / Password):")
    print("test1@vendor.com / test123 (Groomer)")
    print("test2@vendor.com / test123 (Pet Store)")  
    print("test3@vendor.com / test123 (Boarding)")
    print("test4@vendor.com / test123 (Pharmacy)")
    print("demo@furrbutler.com / demo123 (Demo Account)")
    print("\n🌐 Login at: /erp-login (use Vendor Login tab)")

def create_sample_products(cursor, vendor_id, category):
    """Create sample products based on vendor category"""

    if category == 'Groomer':
        products = [
            ("Premium Dog Shampoo", "Professional grade dog shampoo", "Grooming", 15.00, 25.00, 30, "GROOM001"),
            ("Pet Nail Clippers", "Professional nail clippers", "Grooming", 8.00, 15.00, 20, "GROOM002"),
            ("Grooming Brush Set", "Complete brush set", "Grooming", 12.00, 22.00, 15, "GROOM003")
        ]
    elif category == 'Pet Store':
        products = [
            ("Premium Dog Food", "High quality dog food", "Food", 20.00, 35.00, 50, "FOOD001"),
            ("Cat Treats", "Delicious cat treats", "Food", 5.00, 10.00, 40, "FOOD002"),
            ("Pet Toy Set", "Interactive pet toys", "Toys", 8.00, 18.00, 25, "TOY001")
        ]
    elif category == 'Boarding':
        products = [
            ("Boarding Service", "Daily boarding service", "Services", 20.00, 40.00, 100, "BOARD001"),
            ("Pet Bedding", "Comfortable pet bedding", "Accessories", 15.00, 30.00, 20, "BED001")
        ]
    elif category == 'Pharmacy':
        products = [
            ("Pet Vitamins", "Daily pet vitamins", "Medicine", 12.00, 25.00, 30, "MED001"),
            ("Flea Treatment", "Effective flea treatment", "Medicine", 18.00, 35.00, 25, "MED002"),
            ("Pet Antibiotics", "Pet antibiotics", "Medicine", 25.00, 45.00, 15, "MED003")
        ]
    else:
        products = []

    for product in products:
        name, description, cat, buy_price, sale_price, quantity, barcode = product

        # Insert product
        cursor.execute('''
            INSERT INTO products (vendor_id, name, description, category, buy_price, sale_price, quantity, barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vendor_id, name, description, cat, buy_price, sale_price, quantity, barcode))

        product_id = cursor.lastrowid

        # Insert inventory batch
        cursor.execute('''
            INSERT INTO inventory_batches (product_id, quantity, unit_cost, remaining_quantity)
            VALUES (?, ?, ?, ?)
        ''', (product_id, quantity, buy_price, quantity))

        # Insert product batch
        cursor.execute('''
            INSERT INTO product_batches (product_id, batch_name, quantity, buy_price, arrival_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, f"BATCH-{barcode}-001", quantity, buy_price, datetime.now().strftime("%Y-%m-%d")))

def main():
    """Main function to reset and populate test data"""
    print("🚀 Starting test vendor data population...")

    # Delete existing vendors
    delete_existing_vendors()

    # Create new test vendors
    create_test_vendors()

    print("\n✨ Test data population complete!")
    print("You can now login to the ERP system with the credentials shown above.")

if __name__ == "__main__":
    main()

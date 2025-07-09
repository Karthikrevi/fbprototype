
import sqlite3
from datetime import datetime

def create_test_vendors():
    """Create test vendor accounts for testing"""
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    
    # Test vendor accounts with simple credentials
    test_vendors = [
        {
            'name': 'Test Vendor 1',
            'email': 'vendor1@test.com',
            'password': 'test123',
            'category': 'Groomer',
            'city': 'Trivandrum',
            'phone': '+91-9876543210',
            'bio': 'Test grooming services',
            'image_url': 'https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        },
        {
            'name': 'Test Vendor 2', 
            'email': 'vendor2@test.com',
            'password': 'test123',
            'category': 'Pet Store',
            'city': 'Trivandrum',
            'phone': '+91-9876543211',
            'bio': 'Test pet supplies store',
            'image_url': 'https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        },
        {
            'name': 'Demo Grooming Center',
            'email': 'demo@grooming.com', 
            'password': 'demo123',
            'category': 'Groomer',
            'city': 'Trivandrum',
            'phone': '+91-9876543212',
            'bio': 'Professional pet grooming services',
            'image_url': 'https://images.unsplash.com/photo-1522075469751-3847ae47cab9?w=400',
            'latitude': 8.5241,
            'longitude': 76.9366,
            'is_online': 1
        }
    ]
    
    for vendor in test_vendors:
        try:
            c.execute('''
                INSERT OR REPLACE INTO vendors 
                (name, email, password, category, city, phone, bio, image_url, latitude, longitude, is_online, account_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                vendor['name'], vendor['email'], vendor['password'], vendor['category'], 
                vendor['city'], vendor['phone'], vendor['bio'], vendor['image_url'],
                vendor['latitude'], vendor['longitude'], vendor['is_online']
            ))
            print(f"✅ Created vendor: {vendor['email']} / {vendor['password']}")
        except Exception as e:
            print(f"❌ Error creating vendor {vendor['email']}: {e}")
    
    conn.commit()
    conn.close()
    print("\n🎉 Test vendor accounts created successfully!")
    print("\nYou can now login with:")
    print("📧 vendor1@test.com / test123")
    print("📧 vendor2@test.com / test123") 
    print("📧 demo@grooming.com / demo123")
    print("📧 demo@furrbutler.com / demo123 (existing demo account)")

if __name__ == "__main__":
    create_test_vendors()

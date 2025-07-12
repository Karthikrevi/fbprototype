# meta_whatsapp_integration.py
import sqlite3
import json
import requests
from datetime import datetime

def sync_with_meta_catalog(vendor_id):
    """
    Sync inventory with Meta WhatsApp Business API
    This will make products available for customers to order via WhatsApp
    """
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get vendor's WhatsApp business info
    c.execute("""
        SELECT wv.phone_number, v.name 
        FROM whatsapp_vendors wv
        JOIN vendors v ON wv.vendor_id = v.id
        WHERE wv.vendor_id = ?
    """, (vendor_id,))

    vendor_info = c.fetchone()
    if not vendor_info:
        conn.close()
        return

    phone_number, business_name = vendor_info

    # Get products for catalog
    c.execute("""
        SELECT id, name, description, sale_price, quantity, image_url
        FROM products 
        WHERE vendor_id = ? AND quantity > 0
    """, (vendor_id,))

    products = c.fetchall()
    conn.close()

    # Format for Meta WhatsApp Business API
    catalog_items = []
    for product in products:
        product_id, name, description, price, stock, image_url = product

        catalog_items.append({
            "retailer_id": f"fb_prod_{product_id}",
            "name": name,
            "description": description or "Available now",
            "price": int(price * 100),  # Price in cents
            "currency": "INR",
            "availability": "in stock" if stock > 0 else "out of stock",
            "image_url": image_url or "https://via.placeholder.com/300x300?text=Pet+Product",
            "url": f"https://your-domain.com/product/{product_id}"
        })

    # In production, send to Meta API
    meta_api_payload = {
        "catalog_id": f"catalog_{vendor_id}",
        "phone_number": phone_number,
        "business_name": business_name,
        "items": catalog_items
    }

    print(f"📱 Meta WhatsApp Catalog sync prepared for {business_name}: {len(catalog_items)} items")
    # TODO: Implement actual Meta API call
    # meta_api_response = send_to_meta_api(meta_api_payload)

    return True

import requests
import json
import os
from datetime import datetime

class MetaWhatsAppIntegration:
    def __init__(self):
        # Meta WhatsApp Business API credentials
        self.access_token = os.getenv('META_ACCESS_TOKEN', 'your_meta_access_token')
        self.business_id = os.getenv('META_BUSINESS_ID', 'your_business_id')
        self.phone_number_id = os.getenv('META_PHONE_NUMBER_ID', 'your_phone_number_id')
        self.base_url = "https://graph.facebook.com/v18.0"

    def sync_catalog_with_meta(self, vendor_id, products):
        """Sync vendor's product catalog with Meta WhatsApp Business"""
        try:
            catalog_data = self.format_products_for_meta(products)

            # Create or update catalog
            response = self.create_meta_catalog(vendor_id, catalog_data)

            if response.get('success'):
                print(f"✅ Catalog synced with Meta for vendor {vendor_id}")
                return True
            else:
                print(f"❌ Failed to sync catalog with Meta: {response.get('error')}")
                return False

        except Exception as e:
            print(f"❌ Meta sync error: {e}")
            return False

    def format_products_for_meta(self, products):
        """Format products for Meta WhatsApp Business catalog"""
        catalog_items = []

        for product in products:
            product_id, name, description, price, stock, image_url = product

            # Format according to Meta API requirements
            item = {
                "retailer_id": f"fb_prod_{product_id}",
                "name": name[:100],  # Max 100 characters
                "description": (description or "Available now")[:300],  # Max 300 characters
                "price": int(price * 100),  # Price in cents
                "currency": "INR",
                "availability": "in stock" if stock > 0 else "out of stock",
                "condition": "new",
                "link": f"https://furrbutler.com/product/{product_id}",
                "image_link": image_url or "https://via.placeholder.com/300x300?text=Pet+Product",
                "brand": "FurrButler",
                "category": "Pet Supplies"
            }

            catalog_items.append(item)

        return catalog_items

    def create_meta_catalog(self, vendor_id, catalog_items):
        """Create or update Meta WhatsApp Business catalog"""
        url = f"{self.base_url}/{self.business_id}/catalogs"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Prepare catalog payload
        payload = {
            "name": f"FurrButler Vendor {vendor_id} Catalog",
            "vertical": "commerce",
            "products": catalog_items
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return {"success": True, "catalog_id": response.json().get('id')}
            else:
                return {"success": False, "error": response.text}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_order_confirmation(self, customer_phone, order_details):
        """Send order confirmation via WhatsApp"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Format order confirmation message
        message_text = f"""
🎉 *Order Confirmed!*

📦 *Order Details:*
{order_details['summary']}

💰 *Total: ₹{order_details['total']}*

📍 *Delivery:* We'll contact you shortly for delivery arrangements.

Thank you for shopping with us! 🐾
        """

        payload = {
            "messaging_product": "whatsapp",
            "to": customer_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return False

    def setup_webhook(self, webhook_url):
        """Setup webhook for receiving WhatsApp messages"""
        url = f"{self.base_url}/{self.phone_number_id}/webhooks"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "callback_url": webhook_url,
            "verify_token": "furrbutler_webhook_token",
            "fields": ["messages", "message_deliveries", "message_reads"]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error setting up webhook: {e}")
            return False

# Integration instance
meta_integration = MetaWhatsAppIntegration()
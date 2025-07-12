from flask import Blueprint, request, jsonify, render_template
from whatsapp_erp import WhatsAppERPSimulator, simulate_whatsapp_message
import json

whatsapp_bp = Blueprint('whatsapp', __name__)
erp_simulator = WhatsAppERPSimulator()

@whatsapp_bp.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Simulated Twilio WhatsApp webhook endpoint
    In production, this will receive actual Twilio webhook data
    """
    try:
        # For now, simulate Twilio webhook format
        data = request.get_json()

        # Extract message details (simulated Twilio format)
        from_number = data.get('From', '').replace('whatsapp:', '')
        message_body = data.get('Body', '')
        message_sid = data.get('MessageSid', 'SIM_' + str(hash(message_body))[:8])

        print(f"📱 WhatsApp Webhook Received:")
        print(f"From: {from_number}")
        print(f"Message: {message_body}")
        print(f"SID: {message_sid}")

        # Process the message
        response_text = erp_simulator.parse_vendor_message(from_number, message_body)

        # Log response
        erp_simulator.log_message(from_number, response_text, "outgoing")

        # Simulate Twilio response format
        twilio_response = {
            "To": f"whatsapp:{from_number}",
            "Body": response_text,
            "MessageSid": f"RESP_{message_sid}",
            "Status": "sent"
        }

        print(f"🤖 Response sent: {response_text[:50]}...")

        return jsonify({
            "success": True,
            "response": twilio_response,
            "message": "Message processed successfully"
        })

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@whatsapp_bp.route('/whatsapp/simulate', methods=['POST', 'GET'])
def simulate_message():
    """Simulate sending a WhatsApp message for testing"""
    if request.method == 'GET':
        return render_template('whatsapp_simulator.html')

    try:
        data = request.get_json() or request.form
        phone_number = data.get('phone_number', '+91-9876543210')
        message = data.get('message', '')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Simulate the message
        response = simulate_whatsapp_message(phone_number, message)

        return jsonify({
            "success": True,
            "phone_number": phone_number,
            "message": message,
            "response": response
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@whatsapp_bp.route('/whatsapp/register-vendor', methods=['POST'])
def register_vendor():
    """Register a new vendor via WhatsApp simulation"""
    try:
        data = request.get_json() or request.form
        phone_number = data.get('phone_number')
        business_name = data.get('business_name')

        if not phone_number or not business_name:
            return jsonify({"error": "Phone number and business name are required"}), 400

        result = erp_simulator.register_vendor_via_whatsapp(phone_number, business_name)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@whatsapp_bp.route('/whatsapp/catalog')
def get_catalog():
    """Get WhatsApp Business catalog"""
    try:
        with open('whatsapp_catalog.json', 'r') as f:
            catalog = json.load(f)

        return jsonify(catalog)

    except FileNotFoundError:
        return jsonify({
            "catalog_id": "furrbutler_catalog",
            "version": "1.0",
            "products": []
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@whatsapp_bp.route('/whatsapp/dashboard')
def whatsapp_dashboard():
    """WhatsApp Business dashboard"""
    return render_template('whatsapp_dashboard.html')

@whatsapp_bp.route('/whatsapp/analytics')
def whatsapp_analytics():
    """WhatsApp Business analytics"""
    import sqlite3

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Get message statistics
    c.execute('''
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as message_count
        FROM whatsapp_messages 
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''')
    message_stats = c.fetchall()

    # Get top vendors by message volume
    c.execute('''
        SELECT 
            wv.business_name,
            wv.phone_number,
            COUNT(wm.id) as message_count
        FROM whatsapp_vendors wv
        LEFT JOIN whatsapp_messages wm ON wv.phone_number = wm.vendor_phone
        GROUP BY wv.id
        ORDER BY message_count DESC
        LIMIT 10
    ''')
    top_vendors = c.fetchall()

    # Get recent bookings
    c.execute('''
        SELECT * FROM whatsapp_bookings 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    recent_bookings = c.fetchall()

    conn.close()

    return jsonify({
        "message_stats": message_stats,
        "top_vendors": top_vendors,
        "recent_bookings": recent_bookings
    })

@whatsapp_bp.route('/whatsapp/messages/<phone_number>')
def get_vendor_messages(phone_number):
    """Get message history for a vendor"""
    import sqlite3

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    c.execute('''
        SELECT message_text, message_type, timestamp, response_text
        FROM whatsapp_messages 
        WHERE vendor_phone = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (phone_number,))

    messages = c.fetchall()
    conn.close()

    return jsonify({
        "phone_number": phone_number,
        "messages": [
            {
                "text": msg[0],
                "type": msg[1],
                "timestamp": msg[2],
                "response": msg[3]
            } for msg in messages
        ]
    })
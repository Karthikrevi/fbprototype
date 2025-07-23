
from contextlib import contextmanager
import sqlite3
from flask import session, redirect, url_for
import hashlib
from datetime import datetime

@contextmanager
def db_connection(db_name='erp.db'):
    """Context manager for database connections"""
    conn = sqlite3.connect(db_name, timeout=30.0)
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA busy_timeout=30000;')  # 30 seconds
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@contextmanager
def furrvet_db_connection():
    """Context manager for FurrVet database connections"""
    conn = sqlite3.connect('furrvet.db', timeout=30.0)
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA busy_timeout=30000;')  # 30 seconds
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_vendor_id(email):
    """Get vendor ID from email"""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM vendors WHERE email = ?", (email,))
        vendor_result = c.fetchone()
        return vendor_result[0] if vendor_result else None

def is_user_logged_in():
    """Check if user is logged in"""
    return "vendor" in session

def require_vendor_login():
    """Decorator to require vendor login"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not is_user_logged_in():
                return redirect(url_for('erp_login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def log_user_activity(user_email, action, details=""):
    """Log user activity for audit trail"""
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO user_activity_log 
            (user_email, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_email, action, details, datetime.now().isoformat()))
        conn.commit()

def get_vendor_stats(vendor_id):
    """Get comprehensive vendor statistics"""
    with db_connection() as conn:
        c = conn.cursor()
        
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

        return {
            "rating": avg_rating,
            "total_reviews": total_reviews,
            "total_orders": total_orders,
            "success_rate": success_rate,
            "is_online": is_online
        }

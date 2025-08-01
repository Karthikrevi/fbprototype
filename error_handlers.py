
from flask import render_template, jsonify, request, flash, redirect, url_for
import logging
from datetime import datetime

def setup_error_handlers(app):
    """Setup centralized error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json:
            return jsonify({"success": False, "error": "Bad Request", "code": 400}), 400
        return render_template('error.html', 
                             error_code=400, 
                             error_message="Bad Request"), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_json:
            return jsonify({"success": False, "error": "Unauthorized", "code": 401}), 401
        flash("You need to log in to access this page.")
        # Store the current page for redirect after login, but validate it first
        from urllib.parse import urlparse
        next_page = request.url
        parsed = urlparse(next_page)
        if parsed.netloc and parsed.netloc != request.host:
            next_page = None
        login_url = url_for('erp_login')
        if next_page:
            login_url = f"{login_url}?next={next_page}"
        return redirect(login_url)

    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({"success": False, "error": "Forbidden", "code": 403}), 403
        return render_template('error.html', 
                             error_code=403, 
                             error_message="Access Forbidden"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({"success": False, "error": "Not Found", "code": 404}), 404
        return render_template('error.html', 
                             error_code=404, 
                             error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        if request.is_json:
            return jsonify({"success": False, "error": "Internal Server Error", "code": 500}), 500
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Internal Server Error"), 500

def log_error(error_type, error_message, user_email=None, additional_data=None):
    """Log errors to database for tracking"""
    from database_utils import db_connection
    
    try:
        with db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO error_logs 
                (error_type, error_message, user_email, additional_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (error_type, error_message, user_email, 
                  str(additional_data) if additional_data else None, 
                  datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        logging.error(f"Failed to log error to database: {e}")

def handle_database_error(func):
    """Decorator for handling database errors gracefully"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error("database_error", str(e))
            flash("A database error occurred. Please try again.")
            return redirect(request.referrer or url_for('erp_dashboard'))
    wrapper.__name__ = func.__name__
    return wrapper

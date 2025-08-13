
from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging


def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        return jsonify({
            'error': e.name,
            'message': e.description,
            'status_code': e.code
        }), e.code
    
    @app.errorhandler(SQLAlchemyError)
    def handle_db_exception(e):
        """Handle database exceptions"""
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({
            'error': 'Database Error',
            'message': 'An error occurred while processing your request'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        """Handle general exceptions"""
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

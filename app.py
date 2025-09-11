
from flask import Flask, render_template, redirect, url_for
from config import Config
from extensions import init_extensions, db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    from fbregistry.routes_public import public_bp
    from fbregistry.routes_api import api_bp
    from ngo.routes import ngo_bp
    from vet.routes import vet_bp
    from gov.routes import gov_bp
    
    app.register_blueprint(public_bp, url_prefix='/v')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ngo_bp, url_prefix='/ngo')
    app.register_blueprint(vet_bp, url_prefix='/vet')
    app.register_blueprint(gov_bp, url_prefix='/gov')
    
    # Home route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login')
    def login():
        return redirect(url_for('ngo.login'))
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

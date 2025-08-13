
from api.extensions import db
from api.models.user import User, UserRole
import os

def seed_admin():
    """Create admin user if not exists."""
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    
    # Check if admin already exists
    admin_user = User.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        try:
            admin_user = User(
                email=admin_email,
                password=admin_password,
                role=UserRole.ADMIN,
                full_name='System Administrator',
                is_email_verified=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin user created: {admin_email}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to create admin user: {e}")
    else:
        print(f"ℹ️ Admin user already exists: {admin_email}")

if __name__ == '__main__':
    from api.furrbutler import create_app
    app = create_app()
    with app.app_context():
        seed_admin()

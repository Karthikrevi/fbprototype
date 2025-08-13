
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from flask.cli import with_appcontext
from api.furrbutler import create_app
from api.extensions import db
from api.seeds.seed_admin import seed_admin

app = create_app()

@app.cli.command()
def init_db():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")

@app.cli.command()
def upgrade_db():
    """Upgrade database with migrations."""
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()
        print("✅ Database upgraded")

@app.cli.command()
def seed_admin_user():
    """Create admin user."""
    with app.app_context():
        seed_admin()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("Commands: init-db, upgrade-db, seed-admin")
        sys.exit(1)
    
    command = sys.argv[1]
    with app.app_context():
        if command == 'init-db':
            db.create_all()
            print("✅ Database initialized")
        elif command == 'upgrade-db':
            try:
                from flask_migrate import upgrade
                upgrade()
                print("✅ Database upgraded")
            except Exception as e:
                print(f"❌ Migration failed: {e}")
        elif command == 'seed-admin':
            seed_admin()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)


#!/usr/bin/env python3
"""
GDPR-Compliant Users Database Initialization Script
==================================================

This script creates a secure users table for managing user and pet data
with GDPR compliance in mind. Run this once to initialize the database.

Features:
- Secure password hashing preparation
- Consent tracking for GDPR compliance
- Verification and access tracking
- Prepared for future encryption of PII data
"""

import sqlite3
import os
from datetime import datetime

def init_users_database(db_path='users.db'):
    """
    Initialize the GDPR-compliant users database with security considerations.
    
    Args:
        db_path (str): Path to the SQLite database file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create users table with GDPR compliance fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                consent_given BOOLEAN DEFAULT FALSE NOT NULL,
                consent_date TIMESTAMP,
                verified_at TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- GDPR compliance fields
                data_processing_consent BOOLEAN DEFAULT FALSE,
                marketing_consent BOOLEAN DEFAULT FALSE,
                consent_version TEXT DEFAULT '1.0',
                
                -- Security fields
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                
                -- Data retention
                deletion_requested_at TIMESTAMP,
                
                -- Indexes for performance
                CONSTRAINT email_format CHECK (email LIKE '%@%.%'),
                CONSTRAINT phone_format CHECK (phone IS NULL OR length(phone) >= 10)
            )
        """)
        
        # Create indexes for performance and security
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_verified ON users(verified_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_consent ON users(consent_given)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_last_accessed ON users(last_accessed)
        """)
        
        # Create consent log table for audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_consent_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                consent_type TEXT NOT NULL,
                consent_given BOOLEAN NOT NULL,
                consent_version TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create data processing activities log for GDPR Article 30
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                data_category TEXT NOT NULL,
                purpose TEXT NOT NULL,
                legal_basis TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create user sessions table for tracking access
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create trigger to update last_accessed automatically
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_user_last_accessed
            AFTER UPDATE ON users
            FOR EACH ROW
            WHEN NEW.last_accessed = OLD.last_accessed
            BEGIN
                UPDATE users SET last_accessed = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        # Create trigger to update updated_at automatically
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_user_updated_at
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        # Commit all changes
        conn.commit()
        
        print(f"✅ GDPR-compliant users database initialized successfully!")
        print(f"📁 Database file: {os.path.abspath(db_path)}")
        print(f"📊 Tables created:")
        print(f"   - users (main user data)")
        print(f"   - user_consent_log (consent audit trail)")
        print(f"   - data_processing_log (GDPR Article 30 compliance)")
        print(f"   - user_sessions (session management)")
        print(f"🔐 Triggers created for automatic timestamp updates")
        print(f"📈 Indexes created for performance optimization")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_database_structure(db_path='users.db'):
    """
    Verify that the database was created correctly.
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n🔍 Database verification:")
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
            
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print(f"\n👤 Users table structure ({len(columns)} columns):")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
            
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indexes = cursor.fetchall()
        
        print(f"\n📈 Indexes created: {len(indexes)}")
        for idx in indexes:
            if not idx[0].startswith('sqlite_'):  # Skip auto-created indexes
                print(f"   - {idx[0]}")
                
    except Exception as e:
        print(f"❌ Verification error: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """
    Main function to initialize the database and verify its structure.
    """
    print("🚀 Initializing GDPR-compliant users database...")
    print("=" * 60)
    
    # Initialize the database
    success = init_users_database()
    
    if success:
        # Verify the structure
        verify_database_structure()
        
        print("\n" + "=" * 60)
        print("✅ Database initialization completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Implement password hashing using bcrypt or similar")
        print("   2. Add email/phone encryption for PII protection")
        print("   3. Implement consent management workflows")
        print("   4. Set up data retention policies")
        print("   5. Create GDPR data export/deletion endpoints")
        
    else:
        print("\n❌ Database initialization failed!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()

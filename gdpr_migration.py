
#!/usr/bin/env python3
"""
GDPR Migration Script for Existing FurrButler Users
==================================================

This script migrates existing user data to GDPR-compliant format
without losing any existing functionality.
"""

import sqlite3
from encryption import encrypt_data
from datetime import datetime

def migrate_existing_users_to_gdpr():
    """Migrate existing users to GDPR-compliant format"""
    
    # Connect to both databases
    users_conn = sqlite3.connect('users.db')
    erp_conn = sqlite3.connect('erp.db')
    
    users_cursor = users_conn.cursor()
    erp_cursor = erp_conn.cursor()
    
    print("🔄 Starting GDPR migration for existing users...")
    
    try:
        # Get existing users from old Replit database format (if any exist in SQLite)
        # This is safe - if no users exist, nothing happens
        erp_cursor.execute("SELECT DISTINCT user_email FROM bookings WHERE user_email IS NOT NULL")
        existing_user_emails = [row[0] for row in erp_cursor.fetchall()]
        
        print(f"📧 Found {len(existing_user_emails)} user emails in booking records")
        
        migrated_count = 0
        
        for email in existing_user_emails:
            # Check if user already exists in GDPR database
            users_cursor.execute("SELECT id FROM users WHERE email = ?", (encrypt_data(email),))
            if users_cursor.fetchone():
                print(f"⏭️  User {email} already migrated, skipping...")
                continue
            
            # Create GDPR-compliant user record
            encrypted_email = encrypt_data(email)
            if encrypted_email:
                users_cursor.execute("""
                    INSERT INTO users (
                        email, password_hash, consent_given, consent_date,
                        data_processing_consent, marketing_consent, consent_version,
                        verified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    encrypted_email,
                    "MIGRATED_USER_TEMP_HASH",  # User will need to reset password
                    True,  # Assume consent for existing users
                    datetime.now().isoformat(),
                    True,
                    False,  # Don't assume marketing consent
                    "1.0",
                    datetime.now().isoformat()  # Mark as verified
                ))
                
                user_id = users_cursor.lastrowid
                
                # Log migration activity
                users_cursor.execute("""
                    INSERT INTO data_processing_log (
                        user_id, activity_type, data_category, purpose, legal_basis
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id, "migration", "account_data", 
                    "GDPR compliance migration", "legitimate_interest"
                ))
                
                migrated_count += 1
                print(f"✅ Migrated user: {email}")
        
        users_conn.commit()
        print(f"🎉 Migration completed! {migrated_count} users migrated to GDPR format")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        users_conn.rollback()
    
    finally:
        users_conn.close()
        erp_conn.close()

if __name__ == "__main__":
    migrate_existing_users_to_gdpr()

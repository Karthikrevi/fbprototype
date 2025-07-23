
#!/usr/bin/env python3
"""
Database Maintenance Script
Helps prevent database locks and optimize performance
"""

import sqlite3
import os
import time

def optimize_database(db_path):
    """Optimize SQLite database"""
    print(f"Optimizing {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path, timeout=60.0)
        
        # Enable WAL mode
        conn.execute('PRAGMA journal_mode=WAL;')
        
        # Optimize settings
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA cache_size=10000;')
        conn.execute('PRAGMA temp_store=memory;')
        
        # Vacuum to reclaim space and defragment
        conn.execute('VACUUM;')
        
        # Analyze for query optimization
        conn.execute('ANALYZE;')
        
        conn.close()
        print(f"✅ {db_path} optimized successfully")
        
    except Exception as e:
        print(f"❌ Error optimizing {db_path}: {e}")

def check_database_locks():
    """Check for database locks"""
    databases = ['erp.db', 'users.db', 'furrvet.db']
    
    for db in databases:
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db, timeout=1.0)
                conn.execute('SELECT 1;')
                conn.close()
                print(f"✅ {db} is accessible")
            except sqlite3.OperationalError:
                print(f"⚠️  {db} is locked or busy")

if __name__ == "__main__":
    print("🔧 Running database maintenance...")
    
    # Check current status
    check_database_locks()
    
    # Optimize databases
    databases = ['erp.db', 'users.db', 'furrvet.db']
    for db in databases:
        if os.path.exists(db):
            optimize_database(db)
    
    print("✅ Database maintenance completed")

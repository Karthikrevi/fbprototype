
import sqlite3
import threading
import time
import queue
from contextlib import contextmanager

class SQLiteConnectionPool:
    def __init__(self, database_path, max_connections=10, timeout=30):
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = queue.Queue(maxsize=max_connections)
        self.all_connections = []
        self.lock = threading.Lock()
        
        # Pre-create connections
        for _ in range(max_connections):
            conn = self._create_connection()
            self.pool.put(conn)
            self.all_connections.append(conn)
    
    def _create_connection(self):
        conn = sqlite3.connect(
            self.database_path, 
            timeout=self.timeout,
            check_same_thread=False
        )
        # Configure for better concurrency
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout=30000;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        return conn
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self.pool.get(timeout=self.timeout)
            yield conn
        except queue.Empty:
            raise Exception("Database connection pool exhausted")
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                try:
                    conn.commit()
                    self.pool.put(conn)
                except:
                    # Connection is broken, create a new one
                    try:
                        conn.close()
                    except:
                        pass
                    new_conn = self._create_connection()
                    self.pool.put(new_conn)
    
    def close_all(self):
        with self.lock:
            for conn in self.all_connections:
                try:
                    conn.close()
                except:
                    pass

# Global connection pools
erp_pool = SQLiteConnectionPool('erp.db')
users_pool = SQLiteConnectionPool('users.db')
furrvet_pool = SQLiteConnectionPool('furrvet.db')

@contextmanager
def get_erp_connection():
    with erp_pool.get_connection() as conn:
        yield conn

@contextmanager
def get_users_connection():
    with users_pool.get_connection() as conn:
        yield conn

@contextmanager
def get_furrvet_connection():
    with furrvet_pool.get_connection() as conn:
        yield conn

import sqlite3
import json
import os

_DB_PATH = os.path.join(os.path.dirname(__file__), 'kv_store.db')

def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.commit()
    return conn

class _ReplitDB:
    def __contains__(self, key):
        with _get_conn() as conn:
            row = conn.execute("SELECT 1 FROM kv WHERE key = ?", (key,)).fetchone()
            return row is not None

    def __getitem__(self, key):
        with _get_conn() as conn:
            row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
            if row is None:
                raise KeyError(key)
            return json.loads(row[0])

    def __setitem__(self, key, value):
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()

    def __delitem__(self, key):
        with _get_conn() as conn:
            conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            conn.commit()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

db = _ReplitDB()

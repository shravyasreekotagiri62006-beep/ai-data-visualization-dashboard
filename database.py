import sqlite3
import os

# Use /tmp for Vercel writable access, fallback to local file
DB_PATH = "/tmp/dashboard.db" if os.environ.get("VERCEL") else "dashboard.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Table for datasets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT,
            risk_analysis TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Table for chat history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        )
    ''')

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """ SQLite version of the helper """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        res = None
        if commit:
            conn.commit()
            res = cursor.lastrowid
        elif fetchone:
            res = cursor.fetchone()
        elif fetchall:
            res = cursor.fetchall()
        else:
            res = cursor
        return res
    finally:
        if not commit:
            conn.close()

# In SQLite mode, we can run this on every import safely because of IF NOT EXISTS
init_db()



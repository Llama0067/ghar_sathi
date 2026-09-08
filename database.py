import os
import sqlite3
import hashlib
import psycopg2

# Render provides DATABASE_URL in production. Fallback to local SQLite for offline testing.
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        # Render PostgreSQL URL adjustment for psycopg2 if needed
        url = DATABASE_URL.replace("postgres://", "postgresql://")
        return psycopg2.connect(url)
    else:
        # Local fallback database
        return sqlite3.connect("caretaker_server.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Auto-detect placeholder type (%s for Postgres, ? for SQLite)
    is_postgres = DATABASE_URL is not None
    pk_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Users Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {pk_type},
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(256) NOT NULL,
            role VARCHAR(20) NOT NULL,
            service_type VARCHAR(50),
            full_name VARCHAR(100) NOT NULL,
            rating REAL DEFAULT 5.0,
            hourly_rate INT DEFAULT 25,
            is_available INT DEFAULT 1
        )
    ''')
    
    # Bookings Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS bookings (
            id {pk_type},
            client_username VARCHAR(50) NOT NULL,
            worker_username VARCHAR(50),
            service_type VARCHAR(50) NOT NULL,
            date_time VARCHAR(100) NOT NULL,
            notes TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'Pending'
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
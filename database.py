import sqlite3
import hashlib

DB_NAME = "caretaker_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            service_type TEXT,
            full_name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_username TEXT NOT NULL,
            worker_username TEXT,
            service_type TEXT NOT NULL,
            date_time TEXT NOT NULL,
            notes TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, full_name, role, service_type=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, service_type) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), full_name, role, service_type)
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, service_type, full_name FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    result = cursor.fetchone()
    conn.close()
    return result

def create_booking(client_username, service_type, date_time, notes):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (client_username, service_type, date_time, notes) VALUES (?, ?, ?, ?)",
        (client_username, service_type, date_time, notes)
    )
    conn.commit()
    conn.close()

def fetch_client_bookings(client_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, service_type, date_time, notes, status, worker_username FROM bookings WHERE client_username = ? ORDER BY id DESC",
        (client_username,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_worker_jobs(service_type, worker_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, client_username, date_time, notes, status FROM bookings WHERE service_type = ? AND (status = 'Pending' OR worker_username = ?) ORDER BY id DESC",
        (service_type, worker_username)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_job_status(booking_id, worker_username, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bookings SET status = ?, worker_username = ? WHERE id = ?",
        (status, worker_username, booking_id)
    )
    conn.commit()
    conn.close()

if __name__ in {"__main__", "__mp_main__"}:
    init_db()
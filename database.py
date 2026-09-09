import hashlib
import sqlite3

DB_NAME = "caretaker_app.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            service_type TEXT
        )
    """
    )

    # Create bookings table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_username TEXT NOT NULL,
            worker_username TEXT,
            service_type TEXT NOT NULL,
            date_time TEXT NOT NULL,
            plan_duration TEXT NOT NULL,
            total_amount REAL NOT NULL,
            worker_payout REAL NOT NULL,
            company_cut REAL NOT NULL,
            notes TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """
    )

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
            (username, hash_password(password), full_name, role, service_type),
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
        (username, hash_password(password)),
    )
    result = cursor.fetchone()
    conn.close()
    return result


def create_booking(
    client_username,
    service_type,
    date_val,
    from_time,
    till_time,
    duration,
    amount,
    notes,
    payment_method,
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 70:30 Revenue Split Calculation
    worker_payout = round(amount * 0.70, 2)
    company_cut = round(amount * 0.30, 2)

    date_time_str = f"{date_val} ({from_time} - {till_time})"

    cursor.execute(
        """
        INSERT INTO bookings 
        (client_username, service_type, date_time, plan_duration, total_amount, worker_payout, company_cut, notes, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            client_username,
            service_type,
            date_time_str,
            duration,
            amount,
            worker_payout,
            company_cut,
            notes,
            payment_method,
        ),
    )

    conn.commit()
    conn.close()


def fetch_client_bookings(client_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, service_type, date_time, plan_duration, total_amount, notes, status, worker_username, payment_method FROM bookings WHERE client_username = ? ORDER BY id DESC",
        (client_username,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_worker_jobs(service_type, worker_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, client_username, date_time, plan_duration, worker_payout, notes, status FROM bookings WHERE service_type = ? AND (status = 'Pending' OR worker_username = ?) ORDER BY id DESC",
        (service_type, worker_username),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_worker_earnings(worker_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(worker_payout) FROM bookings WHERE worker_username = ? AND status = 'Completed'",
        (worker_username,),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0.0


def update_job_status(booking_id, worker_username, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bookings SET status = ?, worker_username = ? WHERE id = ?",
        (status, worker_username, booking_id),
    )
    conn.commit()
    conn.close()


if __name__ in {"__main__", "__mp_main__"}:
    init_db()
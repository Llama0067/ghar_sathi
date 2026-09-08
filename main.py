from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import database as db

app = FastAPI(title="CareConnect API Server", version="1.0.0")

# Enable CORS for desktop/web client connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    db.init_db()

# --- Data Schemas ---
class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # 'user' or 'worker'
    service_type: Optional[str] = None
    hourly_rate: Optional[int] = 25

class UserLogin(BaseModel):
    username: str
    password: str

class BookingCreate(BaseModel):
    client_username: str
    service_type: str
    date_time: str
    notes: str
    assigned_worker: Optional[str] = None

class StatusUpdate(BaseModel):
    booking_id: int
    worker_username: str
    status: str

# --- API Endpoints ---

@app.get("/")
def root():
    return {"status": "online", "message": "CareConnect Backend Running"}

@app.post("/api/register")
def register(user: UserRegister):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    try:
        cursor.execute(
            f"INSERT INTO users (username, password, full_name, role, service_type, hourly_rate) VALUES ({param}, {param}, {param}, {param}, {param}, {param})",
            (user.username, db.hash_password(user.password), user.full_name, user.role, user.service_type, user.hourly_rate)
        )
        conn.commit()
        return {"success": True, "message": "User registered successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/login")
def login(credentials: UserLogin):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    cursor.execute(
        f"SELECT role, service_type, full_name FROM users WHERE username = {param} AND password = {param}",
        (credentials.username, db.hash_password(credentials.password))
    )
    res = cursor.fetchone()
    conn.close()
    
    if not res:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return {
        "username": credentials.username,
        "role": res[0],
        "service_type": res[1],
        "full_name": res[2]
    }

@app.get("/api/matches/{service_type}")
def get_matches(service_type: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    cursor.execute(
        f"SELECT username, full_name, rating, hourly_rate FROM users WHERE role = 'worker' AND service_type = {param} AND is_available = 1 ORDER BY rating DESC",
        (service_type,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"username": r[0], "full_name": r[1], "rating": r[2], "hourly_rate": r[3]}
        for r in rows
    ]

@app.post("/api/bookings")
def create_booking(booking: BookingCreate):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    initial_status = "Accepted" if booking.assigned_worker else "Pending"
    
    cursor.execute(
        f"INSERT INTO bookings (client_username, service_type, date_time, notes, worker_username, status) VALUES ({param}, {param}, {param}, {param}, {param}, {param})",
        (booking.client_username, booking.service_type, booking.date_time, booking.notes, booking.assigned_worker, initial_status)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Booking created"}

@app.get("/api/bookings/client/{username}")
def get_client_bookings(username: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    cursor.execute(
        f"SELECT id, service_type, date_time, notes, status, worker_username FROM bookings WHERE client_username = {param} ORDER BY id DESC",
        (username,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"id": r[0], "service_type": r[1], "date_time": r[2], "notes": r[3], "status": r[4], "worker": r[5]}
        for r in rows
    ]

@app.get("/api/bookings/worker/{service_type}/{username}")
def get_worker_jobs(service_type: str, username: str):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    cursor.execute(
        f"SELECT id, client_username, date_time, notes, status FROM bookings WHERE service_type = {param} AND (status = 'Pending' OR worker_username = {param}) ORDER BY id DESC",
        (service_type, username)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"id": r[0], "client": r[1], "date_time": r[2], "notes": r[3], "status": r[4]}
        for r in rows
    ]

@app.put("/api/bookings/status")
def update_status(update: StatusUpdate):
    conn = db.get_connection()
    cursor = conn.cursor()
    param = "%s" if db.DATABASE_URL else "?"
    
    cursor.execute(
        f"UPDATE bookings SET status = {param}, worker_username = {param} WHERE id = {param}",
        (update.status, update.worker_username, update.booking_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, time
import sqlite3

# Import our calendar logic
from calendar_service import get_calendar_service, check_availability, create_booking_event, delete_booking_event

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BookingRequest(BaseModel):
    service: str
    date: str
    time: str
    address: str
    cost: int

def init_db():
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, 
                  service TEXT, 
                  date TEXT, 
                  time TEXT, 
                  address TEXT, 
                  cost INTEGER, 
                  event_id TEXT,
                  cancel_token TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Initialize calendar service globally
cal_service = get_calendar_service()

@app.post("/api/book")
async def create_booking(booking: BookingRequest):
    # 1. Enforce strict 3:50 PM to 5:00 PM business hours
    req_time = datetime.strptime(booking.time, '%H:%M').time()
    start_bound = time(15, 50)
    end_bound = time(17, 0)
    
    if not (start_bound <= req_time <= end_bound):
        raise HTTPException(status_code=400, detail="Bookings only allowed between 3:50 PM and 5:00 PM.")

    # Determine duration based on service
    duration = 30 # default
    if booking.service == "walk15":
        duration = 15
    elif booking.service == "indoor":
        duration = 60

    # 2. Check Google Calendar API for conflicts
    if not cal_service:
        raise HTTPException(status_code=500, detail="Calendar service not configured.")
        
    is_available = check_availability(cal_service, booking.date, booking.time, duration)
    if not is_available:
        raise HTTPException(status_code=409, detail="This time slot is already booked or blocked.")

    # 3. Write event to Google Calendar to lock in the booking
    event_id = create_booking_event(
        cal_service, 
        booking.date, 
        booking.time, 
        duration, 
        {"service": booking.service, "address": booking.address, "cost": booking.cost}
    )

    if not event_id:
        raise HTTPException(status_code=500, detail="Failed to create calendar event.")

    # 4. Generate a secure token for cancellation
    cancel_token = str(uuid.uuid4())

    # 5. Log to database for analytics and cancellation mapping
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute("""INSERT INTO bookings 
                 (service, date, time, address, cost, event_id, cancel_token) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (booking.service, booking.date, booking.time, booking.address, booking.cost, event_id, cancel_token))
    
    booking_id = c.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "success", 
        "message": "Booking confirmed!",
        "booking_id": booking_id,
        "cancel_token": cancel_token
    }

@app.delete("/api/cancel/{cancel_token}")
async def cancel_booking(cancel_token: str):
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    
    # 1. Find the booking using the secure token
    c.execute("SELECT id, event_id FROM bookings WHERE cancel_token = ?", (cancel_token,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid cancellation token or booking not found.")
        
    db_id, event_id = result

    # 2. Remove from Google Calendar
    if event_id:
        success = delete_booking_event(cal_service, event_id)
        if not success:
            conn.close()
            raise HTTPException(status_code=500, detail="Failed to remove event from calendar.")

    # 3. Remove from local database
    c.execute("DELETE FROM bookings WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Booking successfully cancelled."}

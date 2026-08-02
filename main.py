from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime, time

app = FastAPI()

# Allow requests from your GitHub Pages domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to your github.io URL in production
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
    # Simple analytics/tracking for bookings
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, service TEXT, date TEXT, time TEXT, address TEXT, cost INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.post("/api/book")
async def create_booking(booking: BookingRequest):
    # 1. Enforce strict timing on the backend (never trust the frontend alone)
    req_time = datetime.strptime(booking.time, '%H:%M').time()
    start_bound = time(15, 50)
    end_bound = time(17, 0)
    
    if not (start_bound <= req_time <= end_bound):
        raise HTTPException(status_code=400, detail="Bookings only allowed between 3:50 PM and 5:00 PM.")

    # 2. Check Google Calendar API for conflicts here
    # (Pseudocode) is_busy = check_gcal_availability(booking.date, booking.time)
    # if is_busy: raise HTTPException(status_code=409, detail="Time slot taken")

    # 3. Log to database for your analytics
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute("INSERT INTO bookings (service, date, time, address, cost) VALUES (?, ?, ?, ?, ?)",
              (booking.service, booking.date, booking.time, booking.address, booking.cost))
    conn.commit()
    conn.close()

    # 4. Write event to Google Calendar to block future bookings
    # create_gcal_event(...)

    return {"status": "success", "message": "Booking confirmed!"}

# Run locally with: uvicorn main:app --reload

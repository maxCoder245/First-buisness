import uuid
# ... existing imports ...
from calendar_service import delete_booking_event

def init_db():
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    # ADDED: event_id and cancel_token columns. 
    # (Note: In a real app, you'd use a migration tool like Alembic if the DB already exists, 
    # but for this SQLite file you can just delete bookings.db and let it recreate)
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

@app.post("/api/book")
async def create_booking(booking: BookingRequest):
    # ... (Keep existing time enforcement and availability checks) ...

    # 1. Lock in the booking
    event_id = create_booking_event(cal_service, booking.date, booking.time, duration, {"service": booking.service, "address": booking.address, "cost": booking.cost})
    
    if not event_id:
        raise HTTPException(status_code=500, detail="Failed to create calendar event.")

    # 2. Generate a secure token for cancellation
    cancel_token = str(uuid.uuid4())

    # 3. Log everything to the database
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute("""INSERT INTO bookings 
                 (service, date, time, address, cost, event_id, cancel_token) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (booking.service, booking.date, booking.time, booking.address, booking.cost, event_id, cancel_token))
    
    booking_id = c.lastrowid
    conn.commit()
    conn.close()

    # 4. Return the token to the frontend so they can save it or display it
    return {
        "status": "success", 
        "message": "Booking confirmed!",
        "booking_id": booking_id,
        "cancel_token": cancel_token
    }

# NEW CANCELLATION ENDPOINT
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

    # 3. Remove from local database (or you could update a 'status' column to 'cancelled')
    c.execute("DELETE FROM bookings WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Booking successfully cancelled."}

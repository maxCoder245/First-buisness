import { useState, useEffect } from 'react';

const services = {
  cleanup: { name: 'Dog Waste Cleanup', basePrice: 5 },
  walk15: { name: 'Dog Walking (15 min)', basePrice: 15 },
  walk30: { name: 'Dog Walking (30 min)', basePrice: 20 },
  indoor: { name: 'Indoor House Cleaning', basePrice: 20 },
};

export default function BookingForm() {
  const [selectedService, setSelectedService] = useState('cleanup');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('15:50');
  const [address, setAddress] = useState('');
  const [totalCost, setTotalCost] = useState(services.cleanup.basePrice);
  
  // New state to manage an existing booking
  const [activeBooking, setActiveBooking] = useState(null);

  // Check for an existing booking when the component mounts
  useEffect(() => {
    const savedBooking = localStorage.getItem('neighborhood_booking');
    if (savedBooking) {
      setActiveBooking(JSON.parse(savedBooking));
    }
  }, []);

  // Dynamic Pricing Calculator
  useEffect(() => {
    setTotalCost(services[selectedService].basePrice);
  }, [selectedService]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://localhost:8000/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service: selectedService,
          date,
          time,
          address,
          cost: totalCost
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Save the token and display details locally
        const bookingDetails = {
          token: data.cancel_token,
          serviceName: services[selectedService].name,
          date,
          time
        };
        
        localStorage.setItem('neighborhood_booking', JSON.stringify(bookingDetails));
        setActiveBooking(bookingDetails);
        alert('Booking requested successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'That time slot is unavailable.'}`);
      }
    } catch (error) {
      alert('Failed to connect to the server.');
    }
  };

  const handleCancel = async () => {
    if (!window.confirm("Are you sure you want to cancel your booking?")) return;

    try {
      const response = await fetch(`http://localhost:8000/api/cancel/${activeBooking.token}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Clear local storage and reset UI
        localStorage.removeItem('neighborhood_booking');
        setActiveBooking(null);
        alert('Booking successfully cancelled.');
      } else {
        alert('Failed to cancel the booking. It may have already been removed.');
        // If it's already gone from the server, clear it locally anyway
        localStorage.removeItem('neighborhood_booking');
        setActiveBooking(null);
      }
    } catch (error) {
      alert('Failed to connect to the server.');
    }
  };

  // --- RENDER ACTIVE BOOKING VIEW ---
  if (activeBooking) {
    return (
      <div className="booking-container" style={{ maxWidth: '400px', margin: 'auto', padding: '20px', textAlign: 'center', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Your Upcoming Appointment</h2>
        <p><strong>Service:</strong> {activeBooking.serviceName}</p>
        <p><strong>Date:</strong> {activeBooking.date}</p>
        <p><strong>Time:</strong> {activeBooking.time}</p>
        
        <button 
          onClick={handleCancel} 
          style={{ padding: '10px', marginTop: '15px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', width: '100%' }}>
          Cancel Booking
        </button>
      </div>
    );
  }

  // --- RENDER BOOKING FORM VIEW ---
  return (
    <div className="booking-container" style={{ maxWidth: '400px', margin: 'auto', padding: '20px' }}>
      <h2>Book a Service</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
        <label>Service:
          <select value={selectedService} onChange={(e) => setSelectedService(e.target.value)} style={{ width: '100%' }}>
            {Object.entries(services).map(([key, svc]) => (
              <option key={key} value={key}>{svc.name} - ${svc.basePrice}</option>
            ))}
          </select>
        </label>

        <label>Date:
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required style={{ width: '100%' }} />
        </label>

        <label>Time (Between 3:50 PM - 5:00 PM):
          <input 
            type="time" 
            min="15:50" 
            max="17:00" 
            value={time} 
            onChange={(e) => setTime(e.target.value)} 
            required 
            style={{ width: '100%' }}
          />
        </label>

        <label>Address:
          <textarea value={address} onChange={(e) => setAddress(e.target.value)} required style={{ width: '100%' }}></textarea>
        </label>

        <div style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
          Total Cost: ${totalCost}
        </div>

        <button type="submit" style={{ padding: '10px', background: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
          Confirm Booking
        </button>
      </form>
    </div>
  );
}

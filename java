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

  // Dynamic Pricing Calculator
  useEffect(() => {
    setTotalCost(services[selectedService].basePrice);
  }, [selectedService]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // In production, point this to your deployed FastAPI URL
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
      alert('Booking requested successfully!');
    } else {
      alert('That time slot is unavailable or blocked.');
    }
  };

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

        <button type="submit" style={{ padding: '10px', background: '#007bff', color: 'white', border: 'none', borderRadius: '5px' }}>
          Confirm Booking
        </button>
      </form>
    </div>
  );
}

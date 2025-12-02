import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import './patient.css';

function PatientPage() {
  const { patientId } = useParams();
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (input.trim() === '') return;
    setMessages([...messages, { sender: 'user', text: input }]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: input, 
          login_id: patientId,
          user_type: "patient"
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(msgs => [
          ...msgs,
          { sender: 'bot', text: data.response }
        ]);
      } else {
        setMessages(msgs => [
          ...msgs,
          { sender: 'bot', text: 'Sorry, there was an error.' }
        ]);
      }
    } catch {
      setMessages(msgs => [
        ...msgs,
        { sender: 'bot', text: 'Network error.' }
      ]);
    }
    setInput('');
    setLoading(false);
  };

  return (
    <div className="patient-layout">
      <div className="sidebar">
        <h3>Patient Menu</h3>
        <ul>
          <li>Dashboard</li>
          <li>Profile</li>
          <li>Appointments</li>
          <li>Logout</li>
        </ul>
      </div>
      <div className="main-content">
        <h2>Welcome Patient: {patientId}</h2>
        <div className="chat-box">
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={msg.sender === 'user' ? 'chat-user' : 'chat-bot'}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="chat-bot">Bot is typing...</div>}
          </div>
          <form className="chat-input" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
            />
            <button type="submit" disabled={loading}>Send</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default PatientPage;
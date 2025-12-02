import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import './doctor.css';

function DoctorPage() {
  const { doctorId } = useParams();
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello Doctor! How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (input.trim() === '') return;
    setMessages([...messages, { sender: 'user', text: input }]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat-doctor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, login_id: doctorId }),
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

  const handleGenerateReport = async () => {
  setLoading(true);
  setMessages(msgs => [...msgs, { sender: 'user', text: '📊 Generate Report' }]);
  
  try {
    const response = await fetch('http://localhost:8000/generate-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        login_id: doctorId,
        send_to_slack: true  // Send to Slack
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      setMessages(msgs => [
        ...msgs,
        { sender: 'bot', text: `${data.report}\n\n📤 ${data.slack_status}` }
      ]);
    } else {
      setMessages(msgs => [
        ...msgs,
        { sender: 'bot', text: 'Error generating report.' }
      ]);
    }
  } catch {
    setMessages(msgs => [
      ...msgs,
      { sender: 'bot', text: 'Network error.' }
    ]);
  }
  setLoading(false);
};

  return (
    <div className="doctor-layout">
      <div className="sidebar">
        <h3>Doctor Menu</h3>
        <ul>
          <li>Dashboard</li>
          <li>Profile</li>
          <li>Appointments</li>
          <li>Patients</li>
          <li>Logout</li>
        </ul>
        
        <div className="report-section">
          <button 
            className="report-btn" 
            onClick={handleGenerateReport} 
            disabled={loading}
          >
            📊 Generate Report
          </button>
        </div>
      </div>
      
      <div className="main-content">
        <h2>Welcome Doctor: {doctorId}</h2>
        <div className="chat-box">
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={msg.sender === 'user' ? 'chat-user' : 'chat-bot'}>
                <pre>{msg.text}</pre>
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

export default DoctorPage;
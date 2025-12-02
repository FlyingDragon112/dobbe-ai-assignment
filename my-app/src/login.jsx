import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './login.css';

function LoginPage() {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('Patient');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: loginId, password, type: activeTab }),
    });
    if (response.ok) {
      const data = await response.json();
      setMessage(`Welcome, ${data.login_id}! Type: ${data.type}`);
      if (data.type === 'Patient') {
        navigate(`/patient/${data.login_id}`);
      } else if (data.type === 'Doctor') {
        navigate(`/doctor/${data.login_id}`);
      }
    } else {
      setMessage('Invalid credentials');
    }
  };

  return (
    <div className="login-wrapper">
      <div className="brand-section">
        <h1 className="brand-title">Dobbe AI</h1>
        <p className="brand-subtitle">AI for Dentists</p>
      </div>
      
      <div className="login-container">
        <div className="tab-container">
          <button
            className={activeTab === 'Patient' ? 'active-tab' : ''}
            onClick={() => setActiveTab('Patient')}
          >
            Patient
          </button>
          <button
            className={activeTab === 'Doctor' ? 'active-tab' : ''}
            onClick={() => setActiveTab('Doctor')}
          >
            Doctor
          </button>
        </div>
        <h2>{activeTab} Login</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Login ID"
            value={loginId}
            onChange={e => setLoginId(e.target.value)}
            required
          />
          <br />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          <br />
          <button type="submit">Login</button>
        </form>
        <p>{message}</p>
      </div>
      <p className="footer-credit">Created by Arnav Agarwal</p>
    </div>
  );
}

export default LoginPage;
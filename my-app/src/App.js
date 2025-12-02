import React from 'react';
import { BrowserRouter, Routes, Route} from 'react-router-dom';
import LoginPage from './login';
import PatientPage from './patient';
import DoctorPage from './doctor';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/patient/:patientId" element={<PatientPage />} />
        <Route path="/doctor/:doctorId" element={<DoctorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
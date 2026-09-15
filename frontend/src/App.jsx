import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import MapPage from './pages/MapPage';
import ReportsPage from './pages/ReportsPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/reports/:id" element={<ResultsPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route
            path="*"
            element={
              <div className="card" style={{ textAlign: 'center', margin: '4rem auto', maxWidth: 500 }}>
                <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>404</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>Page not found.</p>
                <Link to="/" className="btn btn-primary">Return Home</Link>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

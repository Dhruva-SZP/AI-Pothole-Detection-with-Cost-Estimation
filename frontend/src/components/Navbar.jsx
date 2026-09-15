import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Camera, MapPin, BarChart3, AlertCircle, Database, Layers } from 'lucide-react';
import potholeService from '../api/potholeService';

export default function Navbar() {
  const [dbStatus, setDbStatus] = useState({ online: false, checking: true, latency: null, server: '' });

  useEffect(() => {
    let isMounted = true;

    async function checkHealth() {
      try {
        const res = await potholeService.checkDatabaseHealth();
        if (isMounted) {
          setDbStatus({
            online: true,
            checking: false,
            latency: res.data?.latency_ms,
            server: res.data?.server || 'SQL Server',
          });
        }
      } catch (err) {
        if (isMounted) {
          setDbStatus({
            online: false,
            checking: false,
            latency: null,
            server: 'Offline',
          });
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Poll every 30s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="navbar">
      <div className="nav-inner">
        {/* Brand */}
        <NavLink to="/" className="nav-brand">
          <div className="nav-brand-icon">
            <AlertCircle size={20} color="#fff" />
          </div>
          <span>
            Pothole<span style={{ color: 'var(--accent-orange)' }}>AI</span>
          </span>
        </NavLink>

        {/* Navigation Links */}
        <nav className="nav-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Camera size={17} />
            <span>Upload & Detect</span>
          </NavLink>

          <NavLink
            to="/map"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <MapPin size={17} />
            <span>GIS Map View</span>
          </NavLink>

          <NavLink
            to="/reports"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <Layers size={17} />
            <span>Reports Feed</span>
          </NavLink>

          <NavLink
            to="/admin"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <BarChart3 size={17} />
            <span>Admin Analytics</span>
          </NavLink>
        </nav>

        {/* Database Health Badge */}
        <div className="db-badge-container">
          {dbStatus.checking ? (
            <div className="db-pill" style={{ opacity: 0.7 }}>
              <div className="db-dot" />
              <span>Checking DB...</span>
            </div>
          ) : dbStatus.online ? (
            <div className="db-pill" title={`Connected to ${dbStatus.server}`}>
              <div className="db-dot" />
              <span>SQL Server Connected ({dbStatus.latency}ms)</span>
            </div>
          ) : (
            <div className="db-pill offline" title="Database connection failed">
              <div className="db-dot" />
              <span>SQL Server Offline</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

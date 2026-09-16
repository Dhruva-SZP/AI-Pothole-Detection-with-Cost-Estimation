import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  Filter, 
  MapPin, 
  Layers, 
  AlertTriangle, 
  DollarSign, 
  Calendar, 
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Eye,
  Navigation,
  Crosshair,
  Loader2
} from 'lucide-react';
import potholeService from '../api/potholeService';
import { getMediaUrl } from '../api/client';
import useGeolocation from '../hooks/useGeolocation';

// User current location pulsating blue pin
function createUserLocationIcon() {
  const html = `
    <div style="
      position: relative;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: #38bdf8;
        opacity: 0.35;
        animation: pulse 1.5s infinite ease-out;
      "></div>
      <div style="
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #0284c7;
        border: 2.5px solid #ffffff;
        box-shadow: 0 0 12px rgba(2, 132, 199, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
      ">
        📍
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-user-location-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });
}

// Fix for custom DivIcon markers styled by severity
function createSeverityIcon(severity, status) {
  const isRepaired = status === 'Repaired';
  let color = '#10b981'; // Low (Green)
  if (severity === 'Critical') color = '#f43f5e'; // Red
  else if (severity === 'High') color = '#f97316'; // Orange
  else if (severity === 'Medium') color = '#f59e0b'; // Amber

  if (isRepaired) {
    color = '#64748b'; // Slate gray for resolved
  }

  const html = `
    <div style="
      position: relative;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: ${color};
        opacity: 0.25;
        animation: pulse 2s infinite ease-out;
      "></div>
      <div style="
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: ${color};
        border: 2px solid #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 800;
        font-size: 10px;
      ">
        ${isRepaired ? '✓' : '!'}
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-leaflet-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
}

// Map Controller Component for dynamic viewport auto-centering
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.flyTo(center, zoom, { duration: 1.2 });
    }
  }, [center, zoom, map]);
  return null;
}

export default function MapPage() {
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Selected map focus
  const [activeMarker, setActiveMarker] = useState(null);
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]); // Default: Bangalore
  const [mapZoom, setMapZoom] = useState(13);

  // User Geolocation Detection
  const { coords: userCoords, loading: locatingUser, error: geoError, getPosition: locateUser } = useGeolocation();
  const [userLocation, setUserLocation] = useState(null);
  const [locationNotice, setLocationNotice] = useState(null);

  const handleLocateMe = () => {
    setLocationNotice('Detecting your location...');
    locateUser((pos) => {
      const lat = parseFloat(pos.latitude);
      const lng = parseFloat(pos.longitude);
      if (!isNaN(lat) && !isNaN(lng)) {
        setUserLocation([lat, lng]);
        setMapCenter([lat, lng]);
        setMapZoom(15);
        setLocationNotice(`Location set: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        setTimeout(() => setLocationNotice(null), 4000);
      }
    });
  };

  useEffect(() => {
    loadMarkers();
  }, []);

  const loadMarkers = async () => {
    try {
      setLoading(true);
      const res = await potholeService.getMapMarkers();
      const data = res.data || [];
      setMarkers(data);
      if (data.length > 0) {
        setMapCenter([data[0].lat, data[0].lng]);
      }
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to retrieve geospatial marker coordinates.');
    } finally {
      setLoading(false);
    }
  };

  const filteredMarkers = useMemo(() => {
    return markers.filter((m) => {
      const matchSeverity = selectedSeverity === 'ALL' || m.severity === selectedSeverity;
      const matchStatus = selectedStatus === 'ALL' || m.status === selectedStatus;
      const matchSearch = !searchQuery || 
        (m.address && m.address.toLowerCase().includes(searchQuery.toLowerCase())) ||
        m.report_uid.toLowerCase().includes(searchQuery.toLowerCase());
      return matchSeverity && matchStatus && matchSearch;
    });
  }, [markers, selectedSeverity, selectedStatus, searchQuery]);

  const handleSelectPothole = (marker) => {
    setActiveMarker(marker);
    setMapCenter([marker.lat, marker.lng]);
    setMapZoom(16);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', gap: '1rem' }}>
      {/* Top Filter & Metrics Bar */}
      <div className="card" style={{ padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Search Box */}
          <input
            type="text"
            placeholder="Search address or UID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input"
            style={{ width: 220, padding: '0.5rem 0.8rem', fontSize: '0.85rem' }}
          />

          {/* Severity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Severity:</span>
            {['ALL', 'Critical', 'High', 'Medium', 'Low'].map((sev) => (
              <button
                key={sev}
                type="button"
                onClick={() => setSelectedSeverity(sev)}
                className={`badge ${selectedSeverity === sev ? (sev === 'ALL' ? 'btn-primary' : `severity-${sev.toLowerCase()}`) : 'btn-secondary'}`}
                style={{ cursor: 'pointer', padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            {['ALL', 'Reported', 'Verified', 'In_Progress', 'Repaired'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setSelectedStatus(st)}
                className={`badge ${selectedStatus === st ? 'btn-primary' : 'btn-secondary'}`}
                style={{ cursor: 'pointer', padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Counter & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {locationNotice && (
            <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>
              {locationNotice}
            </span>
          )}
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Showing <span style={{ color: '#fff', fontWeight: 800 }}>{filteredMarkers.length}</span> of {markers.length} potholes
          </span>
          <button
            type="button"
            onClick={handleLocateMe}
            disabled={locatingUser}
            className="btn btn-primary"
            style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            title="Detect my current location"
          >
            {locatingUser ? <Loader2 size={14} className="spin" /> : <Navigation size={14} />}
            <span>Locate Me</span>
          </button>
          <button
            type="button"
            onClick={loadMarkers}
            disabled={loading}
            className="btn btn-secondary"
            style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
            title="Reload marker data"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main Content Layout: Map (Left) + Sidebar Directory (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '1rem', flex: 1, minHeight: 0 }}>
        {/* Leaflet Map Surface */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'relative', height: '100%' }}>
          {/* Floating My Location Button on Map */}
          <div style={{ position: 'absolute', top: 12, right: 12, zIndex: 1000 }}>
            <button
              type="button"
              onClick={handleLocateMe}
              disabled={locatingUser}
              className="btn btn-primary"
              style={{
                boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
                padding: '0.5rem 0.85rem',
                fontSize: '0.82rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'var(--accent-orange)'
              }}
              title="Detect current location"
            >
              {locatingUser ? <Loader2 size={15} className="spin" /> : <Crosshair size={15} />}
              <span>{locatingUser ? 'Locating...' : 'My Location'}</span>
            </button>
          </div>

          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            scrollWheelZoom={true}
            style={{ width: '100%', height: '100%' }}
          >
            <MapController center={mapCenter} zoom={mapZoom} />

            {/* CartoDB Dark Matter Tile Layer */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
              maxZoom={19}
            />

            {/* User Current Location Marker */}
            {userLocation && (
              <Marker
                position={userLocation}
                icon={createUserLocationIcon()}
              >
                <Popup className="custom-leaflet-popup">
                  <div style={{ padding: '0.4rem', textAlign: 'center' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#38bdf8', marginBottom: '0.2rem' }}>
                      📍 Your Current Location
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                      {userLocation[0].toFixed(5)}, {userLocation[1].toFixed(5)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Pothole Markers */}
            {filteredMarkers.map((marker) => (
              <Marker
                key={marker.id}
                position={[marker.lat, marker.lng]}
                icon={createSeverityIcon(marker.severity, marker.status)}
                eventHandlers={{
                  click: () => setActiveMarker(marker),
                }}
              >
                <Popup className="custom-leaflet-popup" minWidth={280}>
                  <div style={{ padding: '0.25rem' }}>
                    {/* Thumbnail Image */}
                    {marker.annotated_image_url && (
                      <div style={{ borderRadius: '6px', overflow: 'hidden', marginBottom: '0.75rem', background: '#090d16', textAlign: 'center' }}>
                        <img
                          src={getMediaUrl(marker.annotated_image_url)}
                          alt="Pothole detection overlay"
                          style={{ width: '100%', maxHeight: 150, objectFit: 'cover' }}
                        />
                      </div>
                    )}

                    {/* Popup Details */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <span className={`badge severity-${marker.severity.toLowerCase()}`}>
                        {marker.severity} Severity
                      </span>
                      <span className={`badge badge-${marker.status.toLowerCase()}`}>
                        {marker.status}
                      </span>
                    </div>

                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0.4rem 0 0.2rem 0', color: '#fff' }}>
                      {marker.address || `Inspection #${marker.id}`}
                    </h4>

                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.6rem' }}>
                      <div>Potholes: <strong style={{ color: '#fff' }}>{marker.total_potholes}</strong></div>
                      <div>Repair Est: <strong style={{ color: 'var(--accent-emerald)' }}>${marker.total_estimated_cost.toFixed(2)}</strong></div>
                    </div>

                    {/* Link to Full Report */}
                    <Link
                      to={`/reports/${marker.id}`}
                      className="btn btn-primary"
                      style={{ width: '100%', padding: '0.45rem', fontSize: '0.8rem', justifyContent: 'center' }}
                    >
                      <Eye size={14} />
                      <span>View Detailed Analysis</span>
                    </Link>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

        {/* Right Sidebar: Pothole Inventory List */}
        <div className="card" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <MapPin size={16} color="var(--accent-orange)" />
              <span>Location Feed</span>
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click to focus</span>
          </div>

          {filteredMarkers.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No potholes match the selected filters.
            </div>
          ) : (
            <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.65rem', flex: 1 }}>
              {filteredMarkers.map((marker) => {
                const isSelected = activeMarker?.id === marker.id;
                return (
                  <div
                    key={marker.id}
                    onClick={() => handleSelectPothole(marker)}
                    style={{
                      background: isSelected ? 'rgba(249, 115, 22, 0.12)' : '#0b111e',
                      border: `1px solid ${isSelected ? 'var(--accent-orange)' : 'var(--border-color)'}`,
                      borderRadius: '8px',
                      padding: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                      <span className={`badge severity-${marker.severity.toLowerCase()}`} style={{ fontSize: '0.65rem' }}>
                        {marker.severity}
                      </span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                        ${marker.total_estimated_cost.toFixed(0)}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff', marginBottom: '0.2rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {marker.address || `Pothole Report #${marker.id}`}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      <span>{marker.total_potholes} cavity(ies)</span>
                      <span>{marker.lat.toFixed(4)}, {marker.lng.toFixed(4)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

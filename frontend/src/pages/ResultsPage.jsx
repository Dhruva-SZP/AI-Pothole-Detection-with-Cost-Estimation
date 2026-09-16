import React, { useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { 
  ArrowLeft, 
  MapPin, 
  Calendar, 
  DollarSign, 
  AlertTriangle, 
  Layers, 
  CheckCircle, 
  Clock, 
  Eye, 
  Maximize2,
  TrendingUp,
  FileSpreadsheet,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import potholeService from '../api/potholeService';
import { getMediaUrl } from '../api/client';

export default function ResultsPage() {
  const { id } = useParams();
  const location = useLocation();
  const [report, setReport] = useState(location.state?.report || null);
  const [loading, setLoading] = useState(!location.state?.report);
  const [error, setError] = useState(null);
  const [activeImageTab, setActiveImageTab] = useState('annotated'); // 'annotated' or 'original'
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    if (!location.state?.report) {
      fetchReportDetails();
    }
  }, [id]);

  const fetchReportDetails = async () => {
    try {
      setLoading(true);
      const res = await potholeService.getReportById(id);
      setReport(res.data);
      setError(null);
    } catch (err) {
      setError(err.message || `Failed to retrieve inspection report #${id}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      setUpdatingStatus(true);
      const res = await potholeService.updateReportStatus(id, newStatus);
      setReport(prev => ({ ...prev, status: res.data.status, notes: res.data.notes }));
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 0' }}>
        <RefreshCw size={36} className="spin" style={{ color: 'var(--accent-orange)', marginBottom: '1rem' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Loading inspection analysis...</h3>
        <p style={{ color: 'var(--text-muted)' }}>Retrieving photogrammetric metrics and detected bounding boxes.</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="card" style={{ maxWidth: 600, margin: '3rem auto', textAlign: 'center' }}>
        <AlertTriangle size={48} color="#fb7185" style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Report Not Found</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>{error || 'The requested inspection record does not exist.'}</p>
        <Link to="/" className="btn btn-primary">
          <ArrowLeft size={16} />
          <span>Back to Upload</span>
        </Link>
      </div>
    );
  }

  const detections = report.detections || [];
  const rawUrl = getMediaUrl(report.original_image_path);
  const annUrl = getMediaUrl(report.annotated_image_path);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Top Breadcrumb & Status Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <Link to="/reports" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 600 }}>
          <ArrowLeft size={16} />
          <span>All Reports</span>
        </Link>

        {/* Status Lifecycle Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Status:</span>
          {['Reported', 'Verified', 'In_Progress', 'Repaired'].map((st) => (
            <button
              key={st}
              onClick={() => handleStatusChange(st)}
              disabled={updatingStatus}
              className={`badge badge-${st.toLowerCase()}`}
              style={{
                cursor: 'pointer',
                opacity: report.status === st ? 1 : 0.45,
                transform: report.status === st ? 'scale(1.05)' : 'scale(1)',
                transition: 'all 0.2s ease',
              }}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Hero Header */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Inspection #{report.id || report.report_id || 1}</h1>
              <span className={`badge severity-${(report.severity_level || 'low').toLowerCase()}`}>
                {report.severity_level || 'Low'} Severity
              </span>
              <span className={`badge badge-${(report.status || 'reported').toLowerCase()}`}>
                {report.status}
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <span>UID: <code>{report.report_uid}</code></span>
              {report.address && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                  <MapPin size={14} color="var(--accent-orange)" />
                  {report.address}
                </span>
              )}
              {report.created_at && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Calendar size={14} />
                  {new Date(report.created_at).toLocaleString()}
                </span>
              )}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/map" className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
              <MapPin size={16} color="var(--accent-blue)" />
              <span>Locate on Map</span>
            </Link>
            <Link to="/" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
              <span>New Inspection</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 4 KPI Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(249, 115, 22, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Layers size={24} color="var(--accent-orange)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL POTHOLES</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{report.total_potholes}</div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <DollarSign size={24} color="var(--accent-emerald)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>PREDICTED REPAIR COST</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
              ${Number(report.total_estimated_cost).toFixed(2)}
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={24} color="var(--accent-blue)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>MAX CAVITY DEPTH</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>
              {detections.length > 0 ? Math.max(...detections.map(d => d.estimated_depth_cm)).toFixed(1) : '0.0'} cm
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(244, 63, 94, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AlertTriangle size={24} color="#f43f5e" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL CAVITY AREA</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>
              {detections.length > 0 ? (detections.reduce((acc, cur) => acc + cur.estimated_area_sq_cm, 0) / 10000).toFixed(3) : '0.000'} m²
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Visual Analysis Left + Granular Inventory Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1.2fr) minmax(350px, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Visual Annotation Viewer */}
        <div className="card" style={{ padding: '1.25rem' }}>
          {/* Tab Selector */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', background: '#0b111e', padding: '0.25rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <button
                type="button"
                onClick={() => setActiveImageTab('annotated')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '6px',
                  border: 'none',
                  background: activeImageTab === 'annotated' ? 'var(--accent-orange)' : 'transparent',
                  color: '#fff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                AI Annotated Overlay
              </button>
              <button
                type="button"
                onClick={() => setActiveImageTab('original')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '6px',
                  border: 'none',
                  background: activeImageTab === 'original' ? 'var(--accent-orange)' : 'transparent',
                  color: '#fff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Original Raw Photo
              </button>
            </div>

            <a
              href={activeImageTab === 'annotated' ? annUrl : rawUrl}
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem' }}
            >
              <ExternalLink size={14} />
              <span>Full Res</span>
            </a>
          </div>

          {/* Image Display */}
          <div style={{ background: '#090d16', borderRadius: '10px', overflow: 'hidden', textAlign: 'center', border: '1px solid var(--border-color)' }}>
            <img
              src={activeImageTab === 'annotated' ? annUrl : rawUrl}
              alt={activeImageTab === 'annotated' ? 'Annotated Pothole Detection' : 'Original Road Surface'}
              style={{
                width: '100%',
                maxHeight: 520,
                objectFit: 'contain',
                display: 'block'
              }}
            />
          </div>

          {/* Notes Card */}
          {report.notes && (
            <div style={{ marginTop: '1rem', padding: '0.9rem 1rem', background: '#0b111e', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
              <span style={{ fontWeight: 700, color: 'var(--accent-orange)' }}>Inspection Notes: </span>
              <span style={{ color: 'var(--text-main)' }}>{report.notes}</span>
            </div>
          )}
        </div>

        {/* Right Column: Individual Pothole Cavities Inventory */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Pothole Cavities ({detections.length})</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Calibrated Monocular Sizing</span>
          </div>

          {detections.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
              <CheckCircle size={36} color="var(--accent-emerald)" style={{ marginBottom: '0.75rem' }} />
              <h4>No Critical Potholes Detected</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Pavement condition appears within acceptable safety limits.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {detections.map((det, index) => {
                const depthPct = Math.min(100, Math.round((det.estimated_depth_cm / 15.0) * 100));
                return (
                  <div key={det.id || index} className="card" style={{ padding: '1.25rem', borderLeft: `4px solid ${
                    det.severity === 'Critical' ? 'var(--accent-rose)' :
                    det.severity === 'High' ? 'var(--accent-orange)' :
                    det.severity === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)'
                  }` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>Cavity #{index + 1}</span>
                        <span className={`badge severity-${det.severity.toLowerCase()}`} style={{ fontSize: '0.7rem' }}>
                          {det.severity}
                        </span>
                      </div>
                      <div style={{ fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '1.1rem' }}>
                        ${Number(det.estimated_cost).toFixed(2)}
                      </div>
                    </div>

                    {/* Dimensions & Depth Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', background: '#0b111e', padding: '0.75rem', borderRadius: '8px', marginBottom: '0.75rem', textAlign: 'center' }}>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DIMENSIONS</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                          {det.estimated_width_cm.toFixed(0)} × {det.estimated_length_cm.toFixed(0)} cm
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>DEPTH</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-orange)' }}>
                          {det.estimated_depth_cm.toFixed(1)} cm
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SURFACE AREA</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                          {det.estimated_area_sq_cm.toFixed(0)} cm²
                        </div>
                      </div>
                    </div>

                    {/* Depth Meter Visual Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                        <span>Depth Hazard Meter:</span>
                        <span>{det.estimated_depth_cm.toFixed(1)} cm (Volume: {det.estimated_volume_cu_cm.toFixed(0)} cm³)</span>
                      </div>
                      <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${depthPct}%`,
                            background: det.severity === 'Critical' ? 'var(--accent-rose)' :
                                        det.severity === 'High' ? 'var(--accent-orange)' :
                                        det.severity === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                            borderRadius: '3px'
                          }}
                        />
                      </div>
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

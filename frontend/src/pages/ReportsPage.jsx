import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Layers, 
  Calendar, 
  MapPin, 
  DollarSign, 
  Download, 
  Trash2, 
  Eye, 
  RefreshCw,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';
import potholeService from '../api/potholeService';
import { getMediaUrl } from '../api/client';

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter and search state
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('newest'); // 'newest', 'cost_high', 'potholes_high'

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const res = await potholeService.getReports();
      setReports(res.data || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load reports feed.');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (reportId, newStatus) => {
    try {
      await potholeService.updateReportStatus(reportId, newStatus);
      setReports(prev =>
        prev.map(r => (r.id === reportId ? { ...r, status: newStatus } : r))
      );
    } catch (err) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm(`Are you sure you want to permanently delete Report #${reportId}?`)) {
      return;
    }
    try {
      await potholeService.deleteReport(reportId);
      setReports(prev => prev.filter(r => r.id !== reportId));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  // Filter and sort computation
  const filteredReports = useMemo(() => {
    return reports
      .filter(r => {
        const matchStatus = statusFilter === 'ALL' || r.status === statusFilter;
        const matchSeverity = severityFilter === 'ALL' || r.severity_level === severityFilter;
        const matchSearch = !search || 
          (r.address && r.address.toLowerCase().includes(search.toLowerCase())) ||
          r.report_uid.toLowerCase().includes(search.toLowerCase()) ||
          (r.notes && r.notes.toLowerCase().includes(search.toLowerCase()));
        return matchStatus && matchSeverity && matchSearch;
      })
      .sort((a, b) => {
        if (sortBy === 'cost_high') return b.total_estimated_cost - a.total_estimated_cost;
        if (sortBy === 'potholes_high') return b.total_potholes - a.total_potholes;
        return new Date(b.created_at) - new Date(a.created_at); // default: newest
      });
  }, [reports, statusFilter, severityFilter, search, sortBy]);

  // Export CSV generator
  const exportToCSV = () => {
    if (filteredReports.length === 0) {
      alert('No records available to export.');
      return;
    }
    const headers = ['ID', 'UID', 'Latitude', 'Longitude', 'Address', 'Status', 'Severity', 'Total_Potholes', 'Estimated_Cost', 'Created_At'];
    const rows = filteredReports.map(r => [
      r.id,
      r.report_uid,
      r.latitude,
      r.longitude,
      `"${(r.address || '').replace(/"/g, '""')}"`,
      r.status,
      r.severity_level,
      r.total_potholes,
      Number(r.total_estimated_cost).toFixed(2),
      r.created_at
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `pothole_reports_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '0.25rem' }}>Inspection Reports Feed</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Historical inventory of verified road cavities, spatial coordinates, and municipal cost forecasts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            onClick={exportToCSV}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            <Download size={15} />
            <span>Export CSV</span>
          </button>
          <Link to="/" className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
            <span>New Inspection</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', flex: 1 }}>
            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: 260 }}>
              <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: 12, top: 12 }} />
              <input
                type="text"
                placeholder="Search address, notes, or UID..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="form-input"
                style={{ paddingLeft: '2.4rem', fontSize: '0.85rem' }}
              />
            </div>

            {/* Severity Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Severity:</span>
              {['ALL', 'Critical', 'High', 'Medium', 'Low'].map(sev => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setSeverityFilter(sev)}
                  className={`badge ${severityFilter === sev ? (sev === 'ALL' ? 'btn-primary' : `severity-${sev.toLowerCase()}`) : 'btn-secondary'}`}
                  style={{ cursor: 'pointer', padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                >
                  {sev}
                </button>
              ))}
            </div>

            {/* Status Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Status:</span>
              {['ALL', 'Reported', 'Verified', 'In_Progress', 'Repaired'].map(st => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setStatusFilter(st)}
                  className={`badge ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ cursor: 'pointer', padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Sort Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Sort by:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              className="form-input"
              style={{ padding: '0.45rem 0.8rem', fontSize: '0.85rem', width: 'auto' }}
            >
              <option value="newest">Newest First</option>
              <option value="cost_high">Highest Cost</option>
              <option value="potholes_high">Most Potholes</option>
            </select>
            <button
              type="button"
              onClick={loadReports}
              disabled={loading}
              className="btn btn-secondary"
              style={{ padding: '0.45rem', marginLeft: '0.25rem' }}
              title="Refresh feed"
            >
              <RefreshCw size={15} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Reports Data Table */}
      {loading && reports.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 0' }}>
          <RefreshCw size={32} className="spin" style={{ color: 'var(--accent-orange)', marginBottom: '0.75rem' }} />
          <p style={{ color: 'var(--text-muted)' }}>Loading inspection records from SQL Server...</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <AlertTriangle size={36} color="var(--accent-orange)" style={{ marginBottom: '0.75rem' }} />
          <h3>No Reports Found</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            No records matched your search and filter parameters.
          </p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ background: '#0b111e', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '1rem 1.25rem' }}>Inspection</th>
                  <th style={{ padding: '1rem 1.25rem' }}>Location / Address</th>
                  <th style={{ padding: '1rem 1.25rem' }}>Severity</th>
                  <th style={{ padding: '1rem 1.25rem' }}>Potholes</th>
                  <th style={{ padding: '1rem 1.25rem' }}>Est. Cost</th>
                  <th style={{ padding: '1rem 1.25rem' }}>Status Lifecycle</th>
                  <th style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map(report => (
                  <tr
                    key={report.id}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    {/* Thumbnail + UID */}
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                        {report.annotated_image_path ? (
                          <img
                            src={getMediaUrl(report.annotated_image_path)}
                            alt="Thumbnail"
                            style={{ width: 44, height: 44, objectFit: 'cover', borderRadius: 6, border: '1px solid var(--border-color)' }}
                          />
                        ) : (
                          <div style={{ width: 44, height: 44, borderRadius: 6, background: '#1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Layers size={18} color="var(--text-muted)" />
                          </div>
                        )}
                        <div>
                          <Link to={`/reports/${report.id}`} style={{ fontWeight: 700, color: '#fff' }}>
                            #{report.id}
                          </Link>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Recent'}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Address & GPS */}
                    <td style={{ padding: '1rem 1.25rem', maxWidth: 260 }}>
                      <div style={{ fontWeight: 600, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {report.address || 'Location Coordinates'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {Number(report.latitude).toFixed(4)}, {Number(report.longitude).toFixed(4)}
                      </div>
                    </td>

                    {/* Severity */}
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <span className={`badge severity-${(report.severity_level || 'low').toLowerCase()}`}>
                        {report.severity_level || 'Low'}
                      </span>
                    </td>

                    {/* Potholes count */}
                    <td style={{ padding: '1rem 1.25rem', fontWeight: 700 }}>
                      {report.total_potholes}
                    </td>

                    {/* Repair Cost */}
                    <td style={{ padding: '1rem 1.25rem', fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
                      ${Number(report.total_estimated_cost).toFixed(2)}
                    </td>

                    {/* Status Dropdown Selector */}
                    <td style={{ padding: '1rem 1.25rem' }}>
                      <select
                        value={report.status}
                        onChange={e => handleStatusChange(report.id, e.target.value)}
                        className={`badge badge-${report.status.toLowerCase()}`}
                        style={{
                          background: 'transparent',
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                          outline: 'none'
                        }}
                      >
                        <option value="Reported" style={{ background: '#111827', color: '#38bdf8' }}>Reported</option>
                        <option value="Verified" style={{ background: '#111827', color: '#c084fc' }}>Verified</option>
                        <option value="In_Progress" style={{ background: '#111827', color: '#fbbf24' }}>In Progress</option>
                        <option value="Repaired" style={{ background: '#111827', color: '#34d399' }}>Repaired</option>
                        <option value="Rejected" style={{ background: '#111827', color: '#fb7185' }}>Rejected</option>
                      </select>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Link
                          to={`/reports/${report.id}`}
                          className="btn btn-secondary"
                          style={{ padding: '0.4rem 0.65rem', fontSize: '0.8rem' }}
                          title="View Details"
                        >
                          <Eye size={14} />
                        </Link>
                        <button
                          type="button"
                          onClick={() => handleDeleteReport(report.id)}
                          className="btn btn-secondary"
                          style={{ padding: '0.4rem 0.65rem', fontSize: '0.8rem', color: '#fb7185' }}
                          title="Delete Report"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

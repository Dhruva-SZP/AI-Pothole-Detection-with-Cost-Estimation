import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  DollarSign, 
  Layers, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Sliders, 
  Save, 
  RefreshCw, 
  ExternalLink,
  ShieldCheck
} from 'lucide-react';
import potholeService from '../api/potholeService';

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [costParams, setCostParams] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingParams, setSavingParams] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, paramsRes, recentRes] = await Promise.all([
        potholeService.getAdminStats(),
        potholeService.getCostParameters(),
        potholeService.getReports({ limit: 5 })
      ]);
      setStats(statsRes.data);
      setCostParams(paramsRes.data);
      setRecentReports(recentRes.data || []);
      setFeedbackMsg(null);
    } catch (err) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to load admin analytics.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCostParameters = async (e) => {
    e.preventDefault();
    try {
      setSavingParams(true);
      const res = await potholeService.updateCostParameters(costParams);
      setCostParams(res.data);
      setFeedbackMsg({ type: 'success', text: 'Municipal repair cost parameters successfully updated in SQL Server!' });
    } catch (err) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Failed to update cost parameters.' });
    } finally {
      setSavingParams(false);
    }
  };

  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 0' }}>
        <RefreshCw size={36} className="spin" style={{ color: 'var(--accent-orange)', marginBottom: '1rem' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Loading municipal admin dashboard...</h3>
        <p style={{ color: 'var(--text-muted)' }}>Aggregating repair metrics and querying SQL Server cost profiles.</p>
      </div>
    );
  }

  const kpis = stats?.kpis || {};
  const statusDist = stats?.status_distribution || {};
  const severityDist = stats?.severity_distribution || {};

  const totalSeverityCount = 
    (severityDist.Critical || 0) + 
    (severityDist.High || 0) + 
    (severityDist.Medium || 0) + 
    (severityDist.Low || 0);

  const getPct = (val) => (totalSeverityCount > 0 ? ((val / totalSeverityCount) * 100).toFixed(1) : 0);

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '0.25rem' }}>
            Municipal Operations Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            City-wide road condition KPIs, repair budget forecasting, and asphalt pricing calibration.
          </p>
        </div>

        <button
          type="button"
          onClick={loadDashboardData}
          disabled={loading}
          className="btn btn-secondary"
          style={{ fontSize: '0.85rem' }}
        >
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      {feedbackMsg && (
        <div style={{
          padding: '0.9rem 1.25rem',
          borderRadius: '10px',
          marginBottom: '1.5rem',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          background: feedbackMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          border: `1px solid ${feedbackMsg.type === 'success' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(244, 63, 94, 0.35)'}`,
          color: feedbackMsg.type === 'success' ? '#34d399' : '#fb7185'
        }}>
          {feedbackMsg.type === 'success' ? <ShieldCheck size={18} /> : <AlertTriangle size={18} />}
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* 5 Executive KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Total Reports Logged
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800 }}>{kpis.total_reports || 0}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--accent-blue)', marginTop: '0.25rem' }}>
            {kpis.total_potholes_detected || 0} cavities detected
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Estimated Repair Budget
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            ${Number(kpis.total_repair_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            HMA Material + Crew Labor
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Repaired & Resolved
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            {kpis.repaired_reports || 0}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Confirmed closed work orders
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Pending Maintenance
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
            {kpis.pending_reports || 0}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--accent-amber)', marginTop: '0.25rem' }}>
            Awaiting road crew triage
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Resolution Rate
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
            {kpis.resolution_rate_percent || 0}%
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Repaired vs Reported ratio
          </div>
        </div>
      </div>

      {/* Grid: Visual Distribution Analysis (Left) + Cost Parameters Form (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 1.2fr) minmax(350px, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Visual Charts & Status Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Severity Distribution Gauge */}
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>ASTM Severity Distribution</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Proportion of road defects classified by pavement distress impact.
            </p>

            {/* Stacked Proportional Bar */}
            <div style={{ height: '14px', borderRadius: '7px', display: 'flex', overflow: 'hidden', background: '#1e293b', marginBottom: '1.25rem' }}>
              <div style={{ width: `${getPct(severityDist.Critical)}%`, background: 'var(--accent-rose)' }} title={`Critical: ${severityDist.Critical || 0}`} />
              <div style={{ width: `${getPct(severityDist.High)}%`, background: 'var(--accent-orange)' }} title={`High: ${severityDist.High || 0}`} />
              <div style={{ width: `${getPct(severityDist.Medium)}%`, background: 'var(--accent-amber)' }} title={`Medium: ${severityDist.Medium || 0}`} />
              <div style={{ width: `${getPct(severityDist.Low)}%`, background: 'var(--accent-emerald)' }} title={`Low: ${severityDist.Low || 0}`} />
            </div>

            {/* Legend Breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
              <div style={{ padding: '0.6rem', background: '#0b111e', borderRadius: '8px', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
                <div style={{ fontSize: '0.7rem', color: '#f43f5e', fontWeight: 700 }}>CRITICAL</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{severityDist.Critical || 0}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getPct(severityDist.Critical)}%</div>
              </div>

              <div style={{ padding: '0.6rem', background: '#0b111e', borderRadius: '8px', border: '1px solid rgba(249, 115, 22, 0.3)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--accent-orange)', fontWeight: 700 }}>HIGH</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{severityDist.High || 0}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getPct(severityDist.High)}%</div>
              </div>

              <div style={{ padding: '0.6rem', background: '#0b111e', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--accent-amber)', fontWeight: 700 }}>MEDIUM</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{severityDist.Medium || 0}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getPct(severityDist.Medium)}%</div>
              </div>

              <div style={{ padding: '0.6rem', background: '#0b111e', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)', fontWeight: 700 }}>LOW</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{severityDist.Low || 0}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getPct(severityDist.Low)}%</div>
              </div>
            </div>
          </div>

          {/* Maintenance Pipeline Cards */}
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Maintenance Workflow Funnel</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Work order progression across operational stages.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
              <div style={{ padding: '0.8rem', background: '#0b111e', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600 }}>Reported</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '0.2rem' }}>{statusDist.Reported || 0}</div>
              </div>
              <div style={{ padding: '0.8rem', background: '#0b111e', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#c084fc', fontWeight: 600 }}>Verified</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '0.2rem' }}>{statusDist.Verified || 0}</div>
              </div>
              <div style={{ padding: '0.8rem', background: '#0b111e', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#fbbf24', fontWeight: 600 }}>In Progress</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '0.2rem' }}>{statusDist.In_Progress || 0}</div>
              </div>
              <div style={{ padding: '0.8rem', background: '#0b111e', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>Repaired</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '0.2rem' }}>{statusDist.Repaired || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Municipal Cost Configuration Form */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Sliders size={20} color="var(--accent-orange)" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Municipal Cost Configuration</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Calibrate unit rates stored in SQL Server used by the AI cost estimation model.
          </p>

          {costParams ? (
            <form onSubmit={handleSaveCostParameters}>
              <div className="form-group">
                <label className="form-label">Material Rate (Hot-Mix Asphalt per m³)</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    step="0.5"
                    value={costParams.material_cost_per_cu_meter}
                    onChange={e => setCostParams({ ...costParams, material_cost_per_cu_meter: parseFloat(e.target.value) || 0 })}
                    className="form-input"
                    style={{ paddingLeft: '2rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Base Mobilization Fee (per visit / road site)</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    step="0.5"
                    value={costParams.labor_cost_base}
                    onChange={e => setCostParams({ ...costParams, labor_cost_base: parseFloat(e.target.value) || 0 })}
                    className="form-input"
                    style={{ paddingLeft: '2rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Pavement Prep & Compaction Labor Rate (per m²)</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    step="0.5"
                    value={costParams.labor_cost_per_sq_meter}
                    onChange={e => setCostParams({ ...costParams, labor_cost_per_sq_meter: parseFloat(e.target.value) || 0 })}
                    className="form-input"
                    style={{ paddingLeft: '2rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Equipment & Plate Compactor Overhead ($)</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    step="0.5"
                    value={costParams.equipment_overhead}
                    onChange={e => setCostParams({ ...costParams, equipment_overhead: parseFloat(e.target.value) || 0 })}
                    className="form-input"
                    style={{ paddingLeft: '2rem' }}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Currency Symbol</label>
                <input
                  type="text"
                  value={costParams.currency || 'USD'}
                  onChange={e => setCostParams({ ...costParams, currency: e.target.value })}
                  className="form-input"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={savingParams}
                className="btn btn-primary"
                style={{ width: '100%', padding: '0.8rem', marginTop: '0.5rem' }}
              >
                {savingParams ? (
                  <>
                    <RefreshCw size={16} className="spin" />
                    <span>Saving to SQL Server...</span>
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    <span>Save Parameters</span>
                  </>
                )}
              </button>
            </form>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Could not load cost parameters.</p>
          )}
        </div>
      </div>

      {/* Recent Inspections Activity Table */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Recent Inspection Activity</h3>
          <Link to="/reports" style={{ fontSize: '0.85rem', color: 'var(--accent-orange)', fontWeight: 600 }}>
            View All Reports &rarr;
          </Link>
        </div>

        {recentReports.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No recent inspections logged.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem' }}>ID</th>
                  <th style={{ padding: '0.75rem' }}>Address</th>
                  <th style={{ padding: '0.75rem' }}>Severity</th>
                  <th style={{ padding: '0.75rem' }}>Potholes</th>
                  <th style={{ padding: '0.75rem' }}>Cost Estimate</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentReports.slice(0, 5).map(r => (
                  <tr key={r.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 700 }}>#{r.id}</td>
                    <td style={{ padding: '0.75rem', maxWidth: 220, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.address || `${Number(r.latitude).toFixed(4)}, ${Number(r.longitude).toFixed(4)}`}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={`badge severity-${(r.severity_level || 'low').toLowerCase()}`} style={{ fontSize: '0.65rem' }}>
                        {r.severity_level}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{r.total_potholes}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                      ${Number(r.total_estimated_cost).toFixed(2)}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={`badge badge-${r.status.toLowerCase()}`} style={{ fontSize: '0.65rem' }}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <Link to={`/reports/${r.id}`} className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

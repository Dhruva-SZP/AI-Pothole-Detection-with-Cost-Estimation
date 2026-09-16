import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  MapPin, 
  FileText, 
  Sliders, 
  AlertTriangle, 
  CheckCircle2, 
  Loader2, 
  Image as ImageIcon,
  X
} from 'lucide-react';
import potholeService from '../api/potholeService';
import useGeolocation from '../hooks/useGeolocation';

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const { coords, setCoords, loading: geoLoading, error: geoError, getPosition } = useGeolocation();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [address, setAddress] = useState('');
  const [notes, setNotes] = useState('');
  const [confidence, setConfidence] = useState(0.25);
  const [isDragging, setIsDragging] = useState(false);

  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiError, setApiError] = useState(null);

  const handleFileSelection = (file) => {
    if (!file) return;
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setApiError('Please select a valid image file (JPG, PNG, or WEBP).');
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setApiError('Image exceeds the 25 MB maximum upload limit.');
      return;
    }
    setApiError(null);
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setApiError('Please upload or capture a road image before submitting.');
      return;
    }

    const lat = coords.latitude ? parseFloat(coords.latitude) : 12.9716;
    const lng = coords.longitude ? parseFloat(coords.longitude) : 77.5946;

    setIsProcessing(true);
    setUploadProgress(0);
    setApiError(null);

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('latitude', lat.toString());
    formData.append('longitude', lng.toString());
    formData.append('address', address.trim());
    formData.append('notes', notes.trim());
    formData.append('confidence', confidence.toString());

    try {
      const response = await potholeService.uploadAndAnalyze(formData, (percent) => {
        setUploadProgress(percent);
      });

      const reportData = response.data || {};
      const reportId = reportData.report_id || reportData.id || 1;
      navigate(`/reports/${reportId}`, { state: { report: reportData } });
    } catch (err) {
      setApiError(err.message || 'Inspection processing failed.');
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '0.5rem' }}>
          Road Pothole Inspection & Sizing
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', maxWidth: 640, margin: '0 auto' }}>
          Upload pavement imagery to execute YOLOv8 detection, measure physical cavity dimensions and depth,
          and forecast municipal repair costs.
        </p>
      </div>

      {apiError && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.35)',
          padding: '1rem 1.25rem',
          borderRadius: '10px',
          color: '#fb7185',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <AlertTriangle size={20} />
          <span>{apiError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
        {/* Dropzone */}
        <div className="form-group">
          <label className="form-label" style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>
            Pavement Image <span style={{ color: 'var(--accent-orange)' }}>*</span>
          </label>

          {!previewUrl ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${isDragging ? 'var(--accent-orange)' : 'var(--border-color)'}`,
                borderRadius: '12px',
                padding: '3rem 1.5rem',
                textAlign: 'center',
                cursor: 'pointer',
                background: isDragging ? 'rgba(249, 115, 22, 0.05)' : '#0b111e',
                transition: 'all 0.2s ease',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileSelection(e.target.files[0]);
                }}
              />
              <div style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'rgba(249, 115, 22, 0.1)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem'
              }}>
                <UploadCloud size={28} color="var(--accent-orange)" />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                Click to upload or drag and drop
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Supports high-resolution JPG, PNG, WEBP (Up to 25 MB)
              </p>
            </div>
          ) : (
            <div style={{
              position: 'relative',
              borderRadius: '12px',
              overflow: 'hidden',
              border: '1px solid var(--border-color)',
              background: '#090d16',
              textAlign: 'center',
              padding: '1rem'
            }}>
              <button
                type="button"
                onClick={clearSelectedFile}
                disabled={isProcessing}
                style={{
                  position: 'absolute',
                  top: '1.25rem',
                  right: '1.25rem',
                  background: 'rgba(0, 0, 0, 0.7)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: '#fff',
                  borderRadius: '50%',
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
                title="Remove image"
              >
                <X size={16} />
              </button>
              <img
                src={previewUrl}
                alt="Upload preview"
                style={{
                  maxHeight: 380,
                  maxWidth: '100%',
                  objectFit: 'contain',
                  borderRadius: '8px'
                }}
              />
              <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </div>
            </div>
          )}
        </div>

        {/* GPS Location Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <label className="form-label" style={{ margin: 0 }}>Latitude</label>
              <button
                type="button"
                onClick={getPosition}
                disabled={geoLoading || isProcessing}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                {geoLoading ? <Loader2 size={13} className="spin" /> : <MapPin size={13} />}
                <span>Auto-Detect GPS</span>
              </button>
            </div>
            <input
              type="text"
              placeholder="e.g. 12.9715987"
              value={coords.latitude}
              onChange={(e) => setCoords({ ...coords, latitude: e.target.value })}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Longitude</label>
            <input
              type="text"
              placeholder="e.g. 77.5945627"
              value={coords.longitude}
              onChange={(e) => setCoords({ ...coords, longitude: e.target.value })}
              className="form-input"
            />
          </div>
        </div>

        {geoError && (
          <div style={{ fontSize: '0.8rem', color: '#fb7185', marginTop: '-0.5rem', marginBottom: '1rem' }}>
            {geoError}
          </div>
        )}

        {/* Street Address */}
        <div className="form-group">
          <label className="form-label">Street / Landmark Address (Optional)</label>
          <input
            type="text"
            placeholder="e.g. Outer Ring Road, Near Junction 7, Sector 4"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="form-input"
          />
        </div>

        {/* Detection Confidence Threshold Slider */}
        <div className="form-group" style={{ background: '#0b111e', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={15} color="var(--accent-orange)" />
              <span>YOLOv8 Confidence Threshold</span>
            </span>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-orange)' }}>
              {Math.round(confidence * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.80"
            step="0.05"
            value={confidence}
            onChange={(e) => setConfidence(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent-orange)', cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            <span>Sensitive (10%)</span>
            <span>Balanced (30%)</span>
            <span>Strict (80%)</span>
          </div>
        </div>

        {/* Inspection Notes */}
        <div className="form-group">
          <label className="form-label">Inspector / Citizen Notes (Optional)</label>
          <textarea
            rows="2"
            placeholder="e.g. Severe erosion following monsoon rainfall, risk to two-wheelers."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="form-input"
            style={{ resize: 'vertical' }}
          />
        </div>

        {/* Upload / Progress Bar */}
        {isProcessing && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem', color: 'var(--text-muted)' }}>
              <span>
                {uploadProgress < 100 ? `Uploading image (${uploadProgress}%)...` : 'Running YOLOv8 inference & photogrammetry calculations...'}
              </span>
              <span>{uploadProgress}%</span>
            </div>
            <div style={{ height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${uploadProgress}%`,
                  background: 'linear-gradient(90deg, #ea580c, #f97316)',
                  transition: 'width 0.2s ease',
                }}
              />
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isProcessing || !selectedFile}
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.9rem', fontSize: '1rem', opacity: isProcessing || !selectedFile ? 0.6 : 1 }}
        >
          {isProcessing ? (
            <>
              <Loader2 size={20} className="spin" />
              <span>Analyzing Potholes & Estimating Cost...</span>
            </>
          ) : (
            <>
              <CheckCircle2 size={20} />
              <span>Run Detection & Cost Analysis</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

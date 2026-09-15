import apiClient from './client';

/**
 * Service methods for Pothole Detection, Geospatial Feeds, and Administration.
 */
export const potholeService = {
  /**
   * Uploads an image with GPS coordinates and triggers YOLO inference + sizing + cost calculations.
   */
  async uploadAndAnalyze(formData, onUploadProgress) {
    return apiClient.post('/reports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
  },

  /**
   * Retrieves list of all pothole reports with optional filtering.
   */
  async getReports(params = {}) {
    return apiClient.get('/reports', { params });
  },

  /**
   * Fetches single inspection report detail including granular detections array.
   */
  async getReportById(reportId) {
    return apiClient.get(`/reports/${reportId}`);
  },

  /**
   * Updates report status lifecycle (Reported -> Verified -> In_Progress -> Repaired -> Rejected).
   */
  async updateReportStatus(reportId, status, notes = '') {
    return apiClient.patch(`/reports/${reportId}/status`, { status, notes });
  },

  /**
   * Deletes a report and associated images.
   */
  async deleteReport(reportId) {
    return apiClient.delete(`/reports/${reportId}`);
  },

  /**
   * Retrieves lightweight marker feed for Leaflet map display.
   */
  async getMapMarkers(params = {}) {
    return apiClient.get('/map/markers', { params });
  },

  /**
   * Retrieves GeoJSON FeatureCollection for GIS overlay.
   */
  async getMapGeoJSON() {
    return apiClient.get('/map/geojson');
  },

  /**
   * Retrieves aggregated KPI analytics, status distribution, and severity breakdown.
   */
  async getAdminStats() {
    return apiClient.get('/admin/stats');
  },

  /**
   * Fetches active municipal repair cost parameters.
   */
  async getCostParameters() {
    return apiClient.get('/admin/cost-parameters');
  },

  /**
   * Updates active municipal repair cost parameters.
   */
  async updateCostParameters(parameters) {
    return apiClient.put('/admin/cost-parameters', parameters);
  },

  /**
   * Pings the backend and Microsoft SQL Server to check database readiness.
   */
  async checkDatabaseHealth() {
    return apiClient.get('/health/db');
  },
};

export default potholeService;

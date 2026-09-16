import axios from 'axios';

/**
 * Centralized Axios HTTP Client configured with baseURL and response interceptors.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 90000, // 90 seconds to accommodate heavy model inference
  headers: {
    'Accept': 'application/json',
  },
});

// Response Interceptor for uniform error parsing
apiClient.interceptors.response.use(
  (response) => {
    // Backend wraps payloads in { success: true, data: ..., message: ... }
    return response.data;
  },
  (error) => {
    let errorMsg = 'An unexpected network error occurred.';
    let details = null;
    let statusCode = null;

    if (error.response) {
      statusCode = error.response.status;
      const data = error.response.data;
      if (data && data.message) {
        errorMsg = data.message;
      } else if (typeof data === 'string') {
        errorMsg = data;
      }
      details = data?.details || null;
    } else if (error.request) {
      errorMsg = 'Cannot reach the backend server. Verify the Flask API is running on port 5000.';
    } else {
      errorMsg = error.message;
    }

    const enhancedError = new Error(errorMsg);
    enhancedError.statusCode = statusCode;
    enhancedError.details = details;
    return Promise.reject(enhancedError);
  }
);

export const getMediaUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const backendBase = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${backendBase}${cleanPath}`;
};

export default apiClient;

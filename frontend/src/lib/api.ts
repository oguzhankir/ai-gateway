/** API client for backend communication */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// Admin API key - MUST be set via environment variable in production
// This fallback is for local development only
const ADMIN_API_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY || (process.env.NODE_ENV === 'production' ? '' : 'dev-key-change-in-production');

// Initialize API key in localStorage if not set
if (typeof window !== 'undefined') {
  const storedKey = localStorage.getItem('api_key');
  if (!storedKey && ADMIN_API_KEY) {
    localStorage.setItem('api_key', ADMIN_API_KEY);
  }
}

const apiClient = axios.create({
  baseURL: `${API_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth headers if needed)
apiClient.interceptors.request.use((config) => {
  // Always use admin API key for dashboard access
  let apiKey = null;
  if (typeof window !== 'undefined') {
    apiKey = localStorage.getItem('api_key');
    // If no key in localStorage, set it from ADMIN_API_KEY
    if (!apiKey && ADMIN_API_KEY) {
      localStorage.setItem('api_key', ADMIN_API_KEY);
      apiKey = ADMIN_API_KEY;
    }
  }
  // Fallback to hardcoded admin key if available
  if (!apiKey && ADMIN_API_KEY) {
    apiKey = ADMIN_API_KEY;
  }
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  } else {
    console.warn('No API key available for request');
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.detail || error.response.data?.message || error.message;
      
      if (status === 401) {
        console.error('Authentication failed. Please check your API key.');
        // Try to use admin key if available and not already retried
        if (ADMIN_API_KEY && typeof window !== 'undefined' && !error.config._retry) {
          error.config._retry = true;
          localStorage.setItem('api_key', ADMIN_API_KEY);
          // Update the authorization header
          error.config.headers.Authorization = `Bearer ${ADMIN_API_KEY}`;
          // Retry the request
          return apiClient.request(error.config);
        }
      }
      
      console.error(`API Error (${status}):`, message);
    } else if (error.request) {
      // Request was made but no response received
      console.error('API Error: No response received from server');
    } else {
      // Something else happened
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Analytics
  getOverviewStats: async (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await apiClient.get(`/analytics/overview?${params}`);
    return response.data;
  },

  getProviderStats: async (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await apiClient.get(`/analytics/providers?${params}`);
    return response.data;
  },

  getUserStats: async (startDate?: string, endDate?: string, limit = 100) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('limit', limit.toString());
    const response = await apiClient.get(`/analytics/users?${params}`);
    return response.data;
  },

  getTimeline: async (
    startDate: string,
    endDate: string,
    granularity: 'hour' | 'day' | 'week' | 'month' = 'hour'
  ) => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    params.append('granularity', granularity);
    const response = await apiClient.get(`/analytics/timeline?${params}`);
    return response.data;
  },

  getRecentRequests: async (limit = 10) => {
    const response = await apiClient.get(`/analytics/recent?limit=${limit}`);
    return response.data;
  },

  getLiveStats: async () => {
    const response = await apiClient.get('/analytics/live');
    return response.data;
  },

  // Guardrails
  getGuardrailViolations: async (limit = 100) => {
    const response = await apiClient.get(`/guardrails/violations?limit=${limit}`);
    return response.data;
  },
};

export default api;


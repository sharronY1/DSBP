/**
 * DSBP HTTP Client
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const http = {};

// Helper to get auth token from localStorage
const getAuthToken = () => {
  const token = localStorage.getItem('dsbp_access_token');
  return token ? `Bearer ${token}` : null;
};

// Helper to build headers
const buildHeaders = (customHeaders = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };
  
  const token = getAuthToken();
  if (token) {
    headers.Authorization = token;
  }
  
  return headers;
};

// HTTP methods
['GET', 'POST', 'PATCH', 'DELETE'].forEach((method) => {
  http[method.toLowerCase()] = async (url, data = null, customHeaders = {}) => {
    const options = {
      method,
      headers: buildHeaders(customHeaders),
    };
    
    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${API_BASE_URL}/api${url}`, options);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw error;
    }
    
    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }
    
    return response.json();
  };
});

export default http;


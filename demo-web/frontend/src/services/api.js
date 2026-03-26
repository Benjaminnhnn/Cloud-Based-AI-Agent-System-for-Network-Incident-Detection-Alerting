import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token if unauthorized
      localStorage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

// User Service
export const userService = {
  register: (userData) => api.post('/api/users/register', userData),
  getUser: (userId) => api.get(`/api/users/${userId}`),
  listUsers: (skip = 0, limit = 10) => api.get('/api/users', { params: { skip, limit } }),
  updateUser: (userId, userData) => api.put(`/api/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/api/users/${userId}`),
};

// Health Check
export const healthCheck = () => api.get('/api/health');

export default api;

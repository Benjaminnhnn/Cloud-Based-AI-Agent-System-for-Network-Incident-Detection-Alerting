import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const ERROR_TRANSLATIONS = {
  'Network Error': 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại kết nối.',
  'Email already registered': 'Email này đã được đăng ký.',
  'Username already taken': 'Tên đăng nhập đã được sử dụng.',
  'Invalid email or password': 'Email hoặc mật khẩu không chính xác.',
  'User not found': 'Không tìm thấy người dùng.',
  'Source account not found': 'Không tìm thấy tài khoản nguồn.',
  'Recipient user not found': 'Không tìm thấy người nhận.',
  'Recipient account not found': 'Không tìm thấy tài khoản người nhận.',
  'Cannot transfer to the same account': 'Không thể chuyển tiền đến cùng một tài khoản.',
  'Currency mismatch': 'Loại tiền tệ của hai tài khoản không phù hợp.',
  'Insufficient balance': 'Số dư tài khoản không đủ để thực hiện giao dịch.',
};

export const getApiErrorMessage = (error, fallback = 'Đã xảy ra lỗi. Vui lòng thử lại.') => {
  const detail = error?.response?.data?.detail || error?.message;
  if (typeof detail === 'string') return ERROR_TRANSLATIONS[detail] || fallback;
  if (Array.isArray(detail)) return 'Thông tin nhập vào chưa hợp lệ. Vui lòng kiểm tra lại.';
  return fallback;
};

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
  login: (credentials) => api.post('/api/users/login', credentials),
  getUser: (userId) => api.get(`/api/users/${userId}`),
  getUserByEmail: (email) => api.get('/api/users/lookup/by-email', { params: { email } }),
  listUsers: (skip = 0, limit = 10) => api.get('/api/users', { params: { skip, limit } }),
  updateUser: (userId, userData) => api.put(`/api/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/api/users/${userId}`),
};

export const bankingService = {
  listAccounts: (userId) => api.get('/api/accounts', { params: { user_id: userId } }),
  lookupAccount: (accountNumber) => api.get(`/api/accounts/lookup/${accountNumber}`),
  listTransactions: (params = {}) => api.get('/api/transactions', { params }),
  createTransfer: (transferData) => api.post('/api/transfers', transferData),
};

export const notificationService = {
  list: (userId, params = {}) => api.get('/api/notifications', { params: { user_id: userId, ...params } }),
  unreadCount: (userId) => api.get('/api/notifications/unread-count', { params: { user_id: userId } }),
  markRead: (userId, notificationId) => api.patch(`/api/notifications/${notificationId}/read`, null, { params: { user_id: userId } }),
  markAllRead: (userId) => api.patch('/api/notifications/read-all', null, { params: { user_id: userId } }),
};

// Health Check
export const healthCheck = () => api.get('/api/health');

export default api;

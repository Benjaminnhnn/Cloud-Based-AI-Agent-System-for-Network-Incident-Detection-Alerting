import React, { useState } from 'react';
import { FaEnvelope, FaLock, FaUser } from 'react-icons/fa';
import '../styles/login.css';

export default function Login({ onLogin, isRegister, setIsRegister }) {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    fullName: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDemoLogin = (e) => {
    e.preventDefault();
    const mockUser = {
      id: 1,
      email: 'demo@example.com',
      username: 'demo_user',
      full_name: 'Demo User',
      name: 'Demo User'
    };
    localStorage.setItem('user', JSON.stringify(mockUser));
    localStorage.setItem('token', 'demo-token-' + Date.now());
    onLogin(mockUser);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isRegister) {
        // Register logic
        const response = await fetch('http://localhost:8000/api/users/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            username: formData.username,
            password: formData.password,
            full_name: formData.fullName,
          }),
        });

        if (!response.ok) throw new Error('Registration failed');
        
        const user = await response.json();
        localStorage.setItem('user', JSON.stringify(user));
        onLogin(user);
      } else {
        // Login simulated for demo
        const mockUser = {
          id: 1,
          email: formData.email,
          username: formData.username,
          full_name: 'Demo User',
        };
        localStorage.setItem('user', JSON.stringify(mockUser));
        localStorage.setItem('token', 'demo-token-' + Date.now());
        onLogin(mockUser);
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>💳 AIOps Bank</h1>
          <p>{isRegister ? 'Tạo tài khoản' : 'Chào mừng quay lại'}</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="form-group">
                <label>Full Name</label>
                <div className="input-group">
                  <FaUser className="input-icon" />
                  <input
                    type="text"
                    name="fullName"
                    placeholder="Enter your full name"
                    value={formData.fullName}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Username</label>
                <div className="input-group">
                  <FaUser className="input-icon" />
                  <input
                    type="text"
                    name="username"
                    placeholder="Choose a username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </>
          )}

          <div className="form-group">
            <label>Email</label>
            <div className="input-group">
              <FaEnvelope className="input-icon" />
              <input
                type="email"
                name="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-group">
              <FaLock className="input-icon" />
              <input
                type="password"
                name="password"
                placeholder="Enter password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button 
            type="submit" 
            className="login-btn"
            disabled={loading}
          >
            {loading ? 'Loading...' : (isRegister ? 'Sign Up' : 'Sign In')}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {isRegister ? 'Already have an account?' : 'Don\'t have an account?'}
            <button 
              className="toggle-btn"
              onClick={() => setIsRegister(!isRegister)}
            >
              {isRegister ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>

        <div className="demo-credentials">
          <p><strong>Thử demo:</strong></p>
          <p>Email: demo@example.com</p>
          <p>Mật khẩu: demo123</p>
          <button 
            type="button"
            className="demo-btn"
            onClick={handleDemoLogin}
          >
            🚀 Đăng nhập Demo
          </button>
        </div>
      </div>
    </div>
  );
}

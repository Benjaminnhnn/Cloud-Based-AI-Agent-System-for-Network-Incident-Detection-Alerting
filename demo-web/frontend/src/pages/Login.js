import React, { useState } from 'react';
import { FaEnvelope, FaLock, FaUser, FaShieldAlt, FaMobileAlt, FaHeadset } from 'react-icons/fa';
import { getApiErrorMessage, userService } from '../services/api';
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
      full_name: 'Khách hàng Demo',
      name: 'Khách hàng Demo'
    };
    localStorage.setItem('user', JSON.stringify(mockUser));
    localStorage.setItem('token', `demo-token-${Date.now()}`);
    onLogin(mockUser);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isRegister) {
        const response = await userService.register({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.fullName,
        });
        const user = response.data;
        localStorage.setItem('user', JSON.stringify(user));
        onLogin(user);
      } else {
        const response = await userService.login({
          email: formData.email,
          password: formData.password,
        });
        localStorage.setItem('user', JSON.stringify(response.data));
        localStorage.setItem('token', `demo-token-${Date.now()}`);
        onLogin(response.data);
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-container">
      <section className="login-brand-panel">
        <div className="login-brand">
          <img className="login-brand-mark" src="/viettien-logo.svg" alt="" />
          <div>
            <strong>VietTien</strong>
            <small>Ngân hàng số</small>
          </div>
        </div>
        <div className="login-brand-content">
          <h1>Quản lý tài chính an toàn, thuận tiện mỗi ngày</h1>
          <p>Truy cập tài khoản, chuyển tiền và theo dõi giao dịch trên một nền tảng ngân hàng số.</p>
          <p className="brand-tagline">Tận tâm · Tận tình · Tiên tiến</p>
          <div className="login-benefits">
            <div><FaShieldAlt /><span>Bảo mật giao dịch nhiều lớp</span></div>
            <div><FaMobileAlt /><span>Trải nghiệm nhất quán trên mọi thiết bị</span></div>
            <div><FaHeadset /><span>Hỗ trợ khách hàng 24/7</span></div>
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-card">
          <div className="login-header">
            <p className="login-eyebrow">{isRegister ? 'MỞ TÀI KHOẢN TRỰC TUYẾN' : 'NGÂN HÀNG SỐ'}</p>
            <h2>{isRegister ? 'Đăng ký tài khoản' : 'Đăng nhập'}</h2>
            <p>{isRegister ? 'Nhập thông tin để tạo tài khoản mới' : 'Chào mừng bạn quay trở lại'}</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            {isRegister && (
              <>
                <div className="form-group">
                  <label>Họ và tên</label>
                  <div className="input-group">
                    <FaUser className="input-icon" />
                    <input
                      type="text"
                      name="fullName"
                      placeholder="Nguyễn Văn A"
                      value={formData.fullName}
                      onChange={handleChange}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Tên đăng nhập</label>
                  <div className="input-group">
                    <FaUser className="input-icon" />
                    <input
                      type="text"
                      name="username"
                      placeholder="Tên đăng nhập"
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
                  placeholder="email@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Mật khẩu</label>
              <div className="input-group">
                <FaLock className="input-icon" />
                <input
                  type="password"
                  name="password"
                  placeholder="Nhập mật khẩu"
                  value={formData.password}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? 'Đang xử lý...' : (isRegister ? 'Đăng ký' : 'Đăng nhập')}
            </button>
          </form>

          <div className="login-footer">
            <span>{isRegister ? 'Bạn đã có tài khoản?' : 'Bạn chưa có tài khoản?'}</span>
            <button className="toggle-btn" type="button" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Đăng nhập' : 'Đăng ký ngay'}
            </button>
          </div>

          <div className="demo-credentials">
            <div>
              <strong>Tài khoản trải nghiệm</strong>
              <span>demo@example.com / demo123</span>
            </div>
            <button type="button" className="demo-btn" onClick={handleDemoLogin}>Dùng tài khoản demo</button>
          </div>
        </div>
      </section>
    </main>
  );
}

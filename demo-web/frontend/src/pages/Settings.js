import React, { useState } from 'react';
import { FaBell, FaLock, FaToggleOn, FaToggleOff, FaMobileAlt, FaShieldAlt, FaKey } from 'react-icons/fa';
import '../styles/settings.css';

export default function Settings() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    twoFactorAuth: true,
    autoLogout: true,
    biometricLogin: false,
  });

  const toggleSetting = (key) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const settingItem = (key, icon, title, description) => (
    <div className="setting-item" key={key}>
      <div className="setting-info">
        <span className="setting-icon">{icon}</span>
        <div>
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
      </div>
      <button
        type="button"
        className={`toggle ${settings[key] ? 'on' : 'off'}`}
        onClick={() => toggleSetting(key)}
        aria-label={`${settings[key] ? 'Tắt' : 'Bật'} ${title}`}
      >
        {settings[key] ? <FaToggleOn /> : <FaToggleOff />}
      </button>
    </div>
  );

  return (
    <div className="settings">
      <header className="settings-header">
        <p className="page-eyebrow">TÀI KHOẢN</p>
        <h1>Cài đặt</h1>
        <p>Quản lý thông báo, bảo mật và tùy chọn đăng nhập.</p>
      </header>

      <div className="settings-container">
        <section className="settings-section">
          <div className="settings-section-heading">
            <h2>Thông báo</h2>
            <p>Chọn cách bạn nhận thông tin về hoạt động tài khoản.</p>
          </div>
          {settingItem('emailNotifications', <FaBell />, 'Thông báo qua email', 'Nhận thông báo về giao dịch và hoạt động quan trọng.')}
          {settingItem('pushNotifications', <FaMobileAlt />, 'Thông báo trên thiết bị', 'Nhận thông báo tức thời trên thiết bị đang sử dụng.')}
        </section>

        <section className="settings-section">
          <div className="settings-section-heading">
            <h2>Bảo mật đăng nhập</h2>
            <p>Tăng cường bảo vệ tài khoản của bạn.</p>
          </div>
          {settingItem('twoFactorAuth', <FaShieldAlt />, 'Xác thực hai lớp', 'Yêu cầu thêm bước xác thực khi đăng nhập hoặc giao dịch.')}
          {settingItem('biometricLogin', <FaLock />, 'Đăng nhập sinh trắc học', 'Sử dụng vân tay hoặc nhận diện khuôn mặt trên thiết bị hỗ trợ.')}
          {settingItem('autoLogout', <FaKey />, 'Tự động đăng xuất', 'Tự động đăng xuất sau 30 phút không hoạt động.')}
        </section>

        <section className="settings-section account-security">
          <div className="settings-section-heading">
            <h2>Quản lý tài khoản</h2>
            <p>Cập nhật thông tin bảo mật hoặc gửi yêu cầu hỗ trợ.</p>
          </div>
          <div className="security-action">
            <div><h4>Đổi mật khẩu</h4><p>Nên thay đổi mật khẩu định kỳ để bảo vệ tài khoản.</p></div>
            <button type="button">Cập nhật mật khẩu</button>
          </div>
          <div className="security-action">
            <div><h4>Yêu cầu khóa tài khoản</h4><p>Liên hệ hỗ trợ khi phát hiện hoạt động bất thường.</p></div>
            <button type="button" className="danger">Gửi yêu cầu</button>
          </div>
        </section>
      </div>
    </div>
  );
}

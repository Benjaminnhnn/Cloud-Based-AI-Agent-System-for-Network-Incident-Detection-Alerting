import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaBell,
  FaSearch,
  FaQuestionCircle,
  FaSignOutAlt,
  FaExchangeAlt,
  FaChevronDown,
  FaCheckDouble,
  FaMoneyBillWave
} from 'react-icons/fa';
import '../styles/navbar.css';

export default function Navbar({
  user,
  onLogout,
  notifications = [],
  unreadCount = 0,
  onNotificationRead,
  onAllNotificationsRead,
}) {
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  const formatNotificationTime = (value) => {
    if (!value) return '';
    return new Date(value).toLocaleString('vi-VN');
  };

  const handleNotificationClick = (notification) => {
    onNotificationRead?.(notification.id);
    setShowNotifications(false);
    navigate('/transactions');
  };

  return (
    <nav className="navbar">
      <div className="navbar-search">
        <FaSearch className="search-icon" />
        <input type="text" placeholder="Tìm kiếm giao dịch, dịch vụ..." aria-label="Tìm kiếm" />
      </div>

      <div className="navbar-actions">
        <div className="notification-menu">
          <button
            className="nav-icon-btn"
            type="button"
            aria-label="Thông báo"
            title="Thông báo"
            onClick={() => {
              setShowNotifications((value) => !value);
              setShowMenu(false);
            }}
          >
            <FaBell />
            {unreadCount > 0 && <span className="notification-count">{unreadCount > 99 ? '99+' : unreadCount}</span>}
          </button>

          {showNotifications && (
            <div className="notification-panel">
              <div className="notification-header">
                <div>
                  <strong>Thông báo</strong>
                  <small>{unreadCount} thông báo chưa đọc</small>
                </div>
                <button type="button" onClick={onAllNotificationsRead} disabled={unreadCount === 0}>
                  <FaCheckDouble /> Đọc tất cả
                </button>
              </div>
              <div className="notification-list">
                {notifications.length > 0 ? notifications.map((notification) => (
                  <button
                    type="button"
                    key={notification.id}
                    className={`notification-item ${notification.is_read ? '' : 'unread'}`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <span className="notification-icon"><FaMoneyBillWave /></span>
                    <span className="notification-copy">
                      <strong>{notification.title}</strong>
                      <span>{notification.message}</span>
                      <small>{formatNotificationTime(notification.created_at)}</small>
                    </span>
                  </button>
                )) : (
                  <div className="notification-empty">Bạn chưa có thông báo nào.</div>
                )}
              </div>
            </div>
          )}
        </div>
        <button className="nav-icon-btn" type="button" aria-label="Trợ giúp" title="Trợ giúp">
          <FaQuestionCircle />
        </button>

        <button className="action-btn transfer-action-btn" type="button" onClick={() => navigate('/transfer')}>
          <FaExchangeAlt /> Chuyển tiền
        </button>

        <div className="user-menu">
          <button
            className="user-btn"
            onClick={() => {
              setShowMenu(!showMenu);
              setShowNotifications(false);
            }}
            aria-expanded={showMenu}
          >
            <span className="user-avatar">
              {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
            </span>
            <span className="user-meta">
              <strong>{user?.full_name || user?.username || 'Oripio'}</strong>
              <small>@{user?.username || 'oripio'}</small>
            </span>
            <FaChevronDown className="user-chevron" />
          </button>

          {showMenu && (
            <div className="dropdown-menu">
              <button type="button" onClick={() => navigate('/profile')}>Hồ sơ</button>
              <button type="button" onClick={() => navigate('/settings')}>Cài đặt</button>
              <button type="button" onClick={handleLogout} className="logout-link">
                <FaSignOutAlt /> Đăng xuất
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

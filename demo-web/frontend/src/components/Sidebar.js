import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaThLarge, FaExchangeAlt, FaHistory, FaUser, FaCog, FaHeadset } from 'react-icons/fa';
import '../styles/sidebar.css';

export default function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard', label: 'Tổng quan', icon: FaThLarge },
    { path: '/transfer', label: 'Chuyển tiền', icon: FaExchangeAlt },
    { path: '/transactions', label: 'Lịch sử giao dịch', icon: FaHistory },
    { path: '/profile', label: 'Thông tin cá nhân', icon: FaUser },
    { path: '/settings', label: 'Cài đặt', icon: FaCog },
  ];

  return (
    <aside className="sidebar">
      <Link to="/dashboard" className="sidebar-brand" aria-label="Ngân hàng số VietTien">
        <img className="brand-mark" src="/viettien-logo.svg" alt="" />
        <span className="brand-copy">
          <strong>VietTien</strong>
          <small>Ngân hàng số</small>
        </span>
      </Link>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const IconComponent = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
              title={item.label}
            >
              <IconComponent className="sidebar-icon" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-link support-link" type="button" title="Hỗ trợ khách hàng">
          <FaHeadset className="sidebar-icon" />
          <span>Hỗ trợ</span>
        </button>
      </div>
    </aside>
  );
}

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaThLarge, FaExchangeAlt, FaHistory, FaUser, FaCog, FaLink } from 'react-icons/fa';
import '../styles/sidebar.css';

export default function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: FaThLarge },
    { path: '/transfer', label: 'Transfer', icon: FaExchangeAlt },
    { path: '/transactions', label: 'Transactions', icon: FaHistory },
    { path: '/profile', label: 'Profile', icon: FaUser },
    { path: '/settings', label: 'Settings', icon: FaCog },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">VB</div>

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
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-link" type="button" title="Connect">
          <FaLink className="sidebar-icon" />
        </button>
      </div>
    </aside>
  );
}

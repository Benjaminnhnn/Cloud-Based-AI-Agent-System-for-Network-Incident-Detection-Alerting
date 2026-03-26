import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaBell, FaSearch, FaQuestionCircle, FaSignOutAlt, FaPlus } from 'react-icons/fa';
import '../styles/navbar.css';

export default function Navbar({ user, onLogout }) {
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-search">
        <FaSearch className="search-icon" />
        <input type="text" placeholder="Search product" />
      </div>

      <div className="navbar-actions">
        <button className="nav-icon-btn" type="button" aria-label="Notifications">
          <FaBell />
        </button>
        <button className="nav-icon-btn" type="button" aria-label="Help">
          <FaQuestionCircle />
        </button>

        <button className="action-btn withdraw-btn" type="button">
          Withdraw
        </button>
        <button className="action-btn deposit-btn" type="button">
          <FaPlus /> Deposit
        </button>

        <div className="user-menu">
          <button className="user-btn" onClick={() => setShowMenu(!showMenu)}>
            <span className="user-avatar">
              {(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}
            </span>
            <span className="user-meta">
              <strong>{user?.full_name || user?.username || 'Oripio'}</strong>
              <small>@{user?.username || 'oripio'}</small>
            </span>
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

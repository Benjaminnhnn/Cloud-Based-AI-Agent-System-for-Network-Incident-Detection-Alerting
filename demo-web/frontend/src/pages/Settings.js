import React, { useState } from 'react';
import { FaBell, FaLock, FaToggleOn, FaToggleOff } from 'react-icons/fa';
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
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your account preferences and security</p>
      </div>

      <div className="settings-container">
        {/* Notifications */}
        <div className="settings-section">
          <h3>Notifications</h3>
          
          <div className="setting-item">
            <div className="setting-info">
              <FaBell className="setting-icon" />
              <div>
                <h4>Email Notifications</h4>
                <p>Receive alerts for important account activity</p>
              </div>
            </div>
            <button
              className={`toggle ${settings.emailNotifications ? 'on' : 'off'}`}
              onClick={() => toggleSetting('emailNotifications')}
            >
              {settings.emailNotifications ? <FaToggleOn /> : <FaToggleOff />}
            </button>
          </div>

          <div className="setting-item">
            <div className="setting-info">
              <FaBell className="setting-icon" />
              <div>
                <h4>Push Notifications</h4>
                <p>Get instant alerts on your mobile device</p>
              </div>
            </div>
            <button
              className={`toggle ${settings.pushNotifications ? 'on' : 'off'}`}
              onClick={() => toggleSetting('pushNotifications')}
            >
              {settings.pushNotifications ? <FaToggleOn /> : <FaToggleOff />}
            </button>
          </div>
        </div>

        {/* Security */}
        <div className="settings-section">
          <h3>Security</h3>
          
          <div className="setting-item">
            <div className="setting-info">
              <FaLock className="setting-icon" />
              <div>
                <h4>Two-Factor Authentication</h4>
                <p>Add extra security to your account</p>
              </div>
            </div>
            <button
              className={`toggle ${settings.twoFactorAuth ? 'on' : 'off'}`}
              onClick={() => toggleSetting('twoFactorAuth')}
            >
              {settings.twoFactorAuth ? <FaToggleOn /> : <FaToggleOff />}
            </button>
          </div>

          <div className="setting-item">
            <div className="setting-info">
              <FaLock className="setting-icon" />
              <div>
                <h4>Biometric Login</h4>
                <p>Use fingerprint or face recognition</p>
              </div>
            </div>
            <button
              className={`toggle ${settings.biometricLogin ? 'on' : 'off'}`}
              onClick={() => toggleSetting('biometricLogin')}
            >
              {settings.biometricLogin ? <FaToggleOn /> : <FaToggleOff />}
            </button>
          </div>

          <div className="setting-item">
            <div className="setting-info">
              <FaLock className="setting-icon" />
              <div>
                <h4>Auto Logout</h4>
                <p>Automatically log out after 30 minutes of inactivity</p>
              </div>
            </div>
            <button
              className={`toggle ${settings.autoLogout ? 'on' : 'off'}`}
              onClick={() => toggleSetting('autoLogout')}
            >
              {settings.autoLogout ? <FaToggleOn /> : <FaToggleOff />}
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="settings-section danger-zone">
          <h3>Danger Zone</h3>
          
          <div className="danger-action">
            <h4>Change Password</h4>
            <button className="danger-btn">Update Password</button>
          </div>

          <div className="danger-action">
            <h4>Close Account</h4>
            <button className="danger-btn delete">Delete Account</button>
          </div>
        </div>
      </div>
    </div>
  );
}

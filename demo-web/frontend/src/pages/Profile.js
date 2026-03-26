import React, { useState } from 'react';
import { FaUser, FaEnvelope, FaPhone, FaMapMarkerAlt, FaCalendar, FaPencilAlt, FaSave } from 'react-icons/fa';
import '../styles/profile.css';

export default function Profile() {
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    fullName: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 (555) 123-4567',
    address: '123 Main Street, Anytown, ST 12345',
    dateOfBirth: '1990-05-15',
    accountCreated: '2020-03-15',
    accountStatus: 'Active'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = () => {
    setIsEditing(false);
    // In real app, send data to backend
    console.log('Profile updated:', profileData);
  };

  return (
    <div className="profile">
      <div className="profile-header">
        <h1>My Profile</h1>
        <p>Manage your account information</p>
      </div>

      <div className="profile-container">
        {/* Profile Avatar Section */}
        <div className="profile-avatar-section">
          <div className="avatar">
            <FaUser />
          </div>
          <div className="avatar-info">
            <h2>{profileData.fullName}</h2>
            <p className="status-badge">{profileData.accountStatus}</p>
          </div>
        </div>

        {/* Edit Button */}
        <div className="profile-actions">
          <button
            className={`edit-btn ${isEditing ? 'save' : ''}`}
            onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
          >
            {isEditing ? (
              <>
                <FaSave /> Save Changes
              </>
            ) : (
              <>
                <FaPencilAlt /> Edit Profile
              </>
            )}
          </button>
        </div>

        {/* Personal Information */}
        <div className="profile-section">
          <h3>Personal Information</h3>
          
          <div className="form-group">
            <label>Full Name</label>
            <div className="input-group">
              <FaUser className="input-icon" />
              <input
                type="text"
                name="fullName"
                value={profileData.fullName}
                onChange={handleChange}
                disabled={!isEditing}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Date of Birth</label>
            <div className="input-group">
              <FaCalendar className="input-icon" />
              <input
                type="date"
                name="dateOfBirth"
                value={profileData.dateOfBirth}
                onChange={handleChange}
                disabled={!isEditing}
              />
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="profile-section">
          <h3>Contact Information</h3>
          
          <div className="form-group">
            <label>Email Address</label>
            <div className="input-group">
              <FaEnvelope className="input-icon" />
              <input
                type="email"
                name="email"
                value={profileData.email}
                onChange={handleChange}
                disabled={!isEditing}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <div className="input-group">
              <FaPhone className="input-icon" />
              <input
                type="tel"
                name="phone"
                value={profileData.phone}
                onChange={handleChange}
                disabled={!isEditing}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Address</label>
            <div className="input-group">
              <FaMapMarkerAlt className="input-icon" />
              <input
                type="text"
                name="address"
                value={profileData.address}
                onChange={handleChange}
                disabled={!isEditing}
              />
            </div>
          </div>
        </div>

        {/* Account Information */}
        <div className="profile-section readonly">
          <h3>Account Information</h3>
          
          <div className="info-row">
            <span className="info-label">Account Created:</span>
            <span className="info-value">{profileData.accountCreated}</span>
          </div>

          <div className="info-row">
            <span className="info-label">Account Status:</span>
            <span className="info-value">{profileData.accountStatus}</span>
          </div>

          <div className="info-row">
            <span className="info-label">Last Login:</span>
            <span className="info-value">Today at 2:45 PM</span>
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useState } from 'react';
import { FaUser, FaEnvelope, FaPhone, FaMapMarkerAlt, FaCalendar, FaPencilAlt, FaSave, FaTimes } from 'react-icons/fa';
import { getApiErrorMessage, userService } from '../services/api';
import '../styles/profile.css';

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}');
  } catch {
    return {};
  }
}

export default function Profile({ user, onUserChange }) {
  const currentUser = useMemo(() => {
    if (user?.id || user?.email) return user;
    return getStoredUser();
  }, [user]);
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    fullName: currentUser.full_name || currentUser.name || currentUser.username || '',
    email: currentUser.email || '',
    phone: currentUser.phone || '',
    address: currentUser.address || '',
    dateOfBirth: currentUser.date_of_birth || '',
    accountCreated: currentUser.created_at || '',
    accountStatus: currentUser.is_active === false ? 'Tạm khóa' : 'Đang hoạt động'
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const formatDate = (value) => {
    if (!value) return 'Chưa cập nhật';
    return new Date(value).toLocaleDateString('vi-VN');
  };

  useEffect(() => {
    async function loadProfile() {
      if (!currentUser?.id && !currentUser?.email) {
        setError('Vui lòng đăng nhập để xem thông tin cá nhân.');
        return;
      }

      try {
        const response = currentUser.id
          ? await userService.getUser(currentUser.id)
          : await userService.getUserByEmail(currentUser.email);
        const user = response.data;
        const nextProfile = {
          fullName: user.full_name || user.username || '',
          email: user.email || '',
          phone: user.phone || '',
          address: user.address || '',
          dateOfBirth: user.date_of_birth || '',
          accountCreated: user.created_at || '',
          accountStatus: user.is_active ? 'Đang hoạt động' : 'Tạm khóa'
        };
        setProfileData(nextProfile);
        localStorage.setItem('user', JSON.stringify(user));
        onUserChange?.(user);
        setError('');
      } catch (err) {
        if (!currentUser?.email) {
          setError(getApiErrorMessage(err, 'Không thể tải thông tin cá nhân.'));
        }
      }
    }

    loadProfile();
  }, [currentUser?.email, currentUser?.id, onUserChange]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const storedUser = getStoredUser();
      let activeUser = currentUser?.id ? currentUser : storedUser;

      if (!activeUser?.id && (activeUser?.email || profileData.email)) {
        const lookupResponse = await userService.getUserByEmail(activeUser.email || profileData.email);
        activeUser = lookupResponse.data;
      }

      if (!activeUser?.id) {
        throw new Error('Vui lòng đăng nhập lại trước khi lưu thông tin.');
      }

      const payload = {
        full_name: profileData.fullName,
        phone: profileData.phone || null,
        address: profileData.address || null,
        date_of_birth: profileData.dateOfBirth || null,
      };
      const response = await userService.updateUser(activeUser.id, payload);
      const user = response.data;
      localStorage.setItem('user', JSON.stringify(user));
      onUserChange?.(user);
      setProfileData((prev) => ({
        ...prev,
        fullName: user.full_name || user.username || '',
        email: user.email || '',
        phone: user.phone || '',
        address: user.address || '',
        dateOfBirth: user.date_of_birth || '',
        accountCreated: user.created_at || prev.accountCreated,
        accountStatus: user.is_active ? 'Đang hoạt động' : 'Tạm khóa',
      }));
      setIsEditing(false);
    } catch (err) {
      console.error('Profile save failed:', err);
      setError(getApiErrorMessage(err, 'Không thể lưu thông tin cá nhân.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile">
      <header className="profile-header">
        <p className="page-eyebrow">TÀI KHOẢN</p>
        <h1>Thông tin cá nhân</h1>
        <p>Quản lý thông tin định danh và liên hệ của bạn.</p>
      </header>

      <div className="profile-container">
        <div className="profile-avatar-section">
          <div className="avatar">
            <FaUser />
          </div>
          <div className="avatar-info">
            <h2>{profileData.fullName}</h2>
            <p className="status-badge">{profileData.accountStatus}</p>
          </div>
        </div>

        <div className="profile-actions">
          {isEditing && (
            <button className="cancel-btn" type="button" disabled={saving} onClick={() => setIsEditing(false)}>
              <FaTimes /> Hủy
            </button>
          )}
          <button
            className={`edit-btn ${isEditing ? 'save' : ''}`}
            disabled={saving}
            onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
          >
            {isEditing ? (
              <>
                <FaSave /> {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
              </>
            ) : (
              <>
                <FaPencilAlt /> Chỉnh sửa
              </>
            )}
          </button>
        </div>

        {error && <div className="profile-error">{error}</div>}

        <div className="profile-section">
          <div className="profile-section-heading">
            <h3>Thông tin cá nhân</h3>
            <p>Thông tin được sử dụng để xác minh chủ tài khoản.</p>
          </div>

          <div className="form-group">
            <label>Họ và tên</label>
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
            <label>Ngày sinh</label>
            <div className="input-group">
              <FaCalendar className="input-icon" />
              <input
                type="date"
                name="dateOfBirth"
                value={profileData.dateOfBirth}
                onChange={handleChange}
                disabled={!isEditing}
                placeholder="Chưa cập nhật"
              />
            </div>
          </div>
        </div>

        <div className="profile-section">
          <div className="profile-section-heading">
            <h3>Thông tin liên hệ</h3>
            <p>Đảm bảo thông tin liên hệ luôn chính xác và cập nhật.</p>
          </div>

          <div className="form-group">
            <label>Email</label>
            <div className="input-group">
              <FaEnvelope className="input-icon" />
              <input
                type="email"
                name="email"
                value={profileData.email}
                onChange={handleChange}
                disabled
              />
            </div>
          </div>

          <div className="form-group">
            <label>Số điện thoại</label>
            <div className="input-group">
              <FaPhone className="input-icon" />
              <input
                type="tel"
                name="phone"
                value={profileData.phone}
                onChange={handleChange}
                disabled={!isEditing}
                placeholder="Chưa cập nhật"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Địa chỉ</label>
            <div className="input-group">
              <FaMapMarkerAlt className="input-icon" />
              <input
                type="text"
                name="address"
                value={profileData.address}
                onChange={handleChange}
                disabled={!isEditing}
                placeholder="Chưa cập nhật"
              />
            </div>
          </div>
        </div>

        <div className="profile-section readonly">
          <div className="profile-section-heading">
            <h3>Thông tin tài khoản</h3>
            <p>Thông tin hệ thống không thể chỉnh sửa trực tiếp.</p>
          </div>

          <div className="info-row">
            <span className="info-label">Ngày tạo tài khoản</span>
            <span className="info-value">{formatDate(profileData.accountCreated)}</span>
          </div>

          <div className="info-row">
            <span className="info-label">Trạng thái tài khoản</span>
            <span className="info-value">{profileData.accountStatus}</span>
          </div>

          <div className="info-row">
            <span className="info-label">Lần đăng nhập gần nhất</span>
            <span className="info-value">Hôm nay</span>
          </div>
        </div>
      </div>
    </div>
  );
}

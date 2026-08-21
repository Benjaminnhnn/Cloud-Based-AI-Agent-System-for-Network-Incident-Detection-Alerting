import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import './styles/global.css';
import './styles/layout.css';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transfer from './pages/Transfer';
import Transactions from './pages/Transactions';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import { notificationService } from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isRegister, setIsRegister] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [realtimeVersion, setRealtimeVersion] = useState(0);

  // Check if user is logged in on mount
  useEffect(() => {
    try {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        setUser(JSON.parse(savedUser));
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Error loading user from localStorage:', error);
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }
  }, []);

  useEffect(() => {
    if (!user?.id) {
      setNotifications([]);
      setUnreadCount(0);
      return undefined;
    }

    let active = true;
    let socket;
    let reconnectTimer;

    async function loadNotifications() {
      try {
        const [notificationsResponse, countResponse] = await Promise.all([
          notificationService.list(user.id, { limit: 30 }),
          notificationService.unreadCount(user.id),
        ]);
        if (active) {
          setNotifications(notificationsResponse.data || []);
          setUnreadCount(countResponse.data?.unread_count || 0);
        }
      } catch (error) {
        console.error('Unable to load notifications:', error);
      }
    }

    function connectRealtime() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(`${protocol}//${window.location.host}/api/ws/${user.id}`);

      socket.onopen = loadNotifications;

      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data);
          if (event.type !== 'banking.updated') return;

          setRealtimeVersion((version) => version + 1);
          if (event.notification) {
            setNotifications((current) => {
              if (current.some((item) => item.id === event.notification.id)) return current;
              return [event.notification, ...current].slice(0, 30);
            });
            if (!event.notification.is_read) {
              setUnreadCount((count) => count + 1);
            }
          }
        } catch (error) {
          console.error('Invalid realtime event:', error);
        }
      };

      socket.onclose = () => {
        if (active) reconnectTimer = window.setTimeout(connectRealtime, 2000);
      };
    }

    loadNotifications();
    connectRealtime();

    return () => {
      active = false;
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [user?.id]);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('user', JSON.stringify(userData));
    setIsRegister(false);
  };

  const handleLogout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('user');
  };

  const handleNotificationRead = async (notificationId) => {
    if (!user?.id) return;
    const notification = notifications.find((item) => item.id === notificationId);
    if (!notification || notification.is_read) return;
    try {
      await notificationService.markRead(user.id, notificationId);
      setNotifications((current) => current.map((item) => (
        item.id === notificationId ? { ...item, is_read: true } : item
      )));
      setUnreadCount((count) => Math.max(0, count - 1));
    } catch (error) {
      console.error('Unable to mark notification as read:', error);
    }
  };

  const handleAllNotificationsRead = async () => {
    if (!user?.id || unreadCount === 0) return;
    try {
      await notificationService.markAllRead(user.id);
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Unable to mark notifications as read:', error);
    }
  };

  return (
    <Router>
      {!isAuthenticated ? (
        <Routes>
          <Route
            path="/"
            element={
              <Login
                onLogin={handleLogin}
                isRegister={isRegister}
                setIsRegister={setIsRegister}
              />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      ) : (
        <div className="app-layout">
          <div className="navbar-wrapper">
            <Navbar
              user={user}
              onLogout={handleLogout}
              notifications={notifications}
              unreadCount={unreadCount}
              onNotificationRead={handleNotificationRead}
              onAllNotificationsRead={handleAllNotificationsRead}
            />
          </div>
          <div className="sidebar-wrapper">
            <Sidebar />
          </div>
          <div className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard user={user} realtimeVersion={realtimeVersion} />} />
              <Route path="/dashboard" element={<Dashboard user={user} realtimeVersion={realtimeVersion} />} />
              <Route path="/transfer" element={<Transfer realtimeVersion={realtimeVersion} />} />
              <Route path="/transactions" element={<Transactions realtimeVersion={realtimeVersion} />} />
              <Route path="/profile" element={<Profile user={user} onUserChange={setUser} />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      )}
    </Router>
  );
}

export default App;

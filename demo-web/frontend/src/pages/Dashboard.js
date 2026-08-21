import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FaArrowDown,
  FaArrowUp,
  FaEye,
  FaEyeSlash,
  FaWallet,
  FaExchangeAlt,
  FaHistory,
  FaFileInvoiceDollar,
  FaPiggyBank,
  FaCreditCard,
  FaShieldAlt
} from 'react-icons/fa';
import { bankingService } from '../services/api';
import '../styles/dashboard.css';

export default function Dashboard({ user, realtimeVersion = 0 }) {
  const [showBalance, setShowBalance] = useState(true);
  const [accounts, setAccounts] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [error, setError] = useState('');
  const currentUser = useMemo(() => {
    if (user) return user;
    try {
      return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
      return {};
    }
  }, [user]);

  useEffect(() => {
    async function loadDashboard() {
      if (!currentUser?.id) return;

      try {
        const [accountsResponse, transactionsResponse] = await Promise.all([
          bankingService.listAccounts(currentUser.id),
          bankingService.listTransactions({ user_id: currentUser.id, limit: 5 }),
        ]);

        setAccounts(accountsResponse.data || []);
        setRecentTransactions((transactionsResponse.data || []).map((item) => {
          const outgoing = item.transaction_type === 'transfer_out';
          return {
            id: item.id,
            description: item.description || item.reference_code,
            reference: item.reference_code,
            amount: outgoing ? -Number(item.amount) : Number(item.amount),
            date: new Date(item.created_at).toLocaleString('vi-VN'),
          };
        }));
        setError('');
      } catch {
        setError('Không thể tải dữ liệu tài khoản. Vui lòng thử lại sau.');
      }
    }

    loadDashboard();
  }, [currentUser?.id, realtimeVersion]);

  const formatCurrency = (value, currency = 'VND') =>
    `${Number(value || 0).toLocaleString('vi-VN')} ${currency}`;
  const totalBalance = accounts.reduce((sum, account) => sum + Number(account.balance), 0);
  const totalIncome = recentTransactions.filter((item) => item.amount > 0).reduce((sum, item) => sum + item.amount, 0);
  const totalExpense = recentTransactions.filter((item) => item.amount < 0).reduce((sum, item) => sum + Math.abs(item.amount), 0);
  const displayName = currentUser?.full_name || currentUser?.name || currentUser?.username || 'Quý khách';

  const quickActions = [
    { label: 'Chuyển tiền', icon: FaExchangeAlt, path: '/transfer' },
    { label: 'Lịch sử giao dịch', icon: FaHistory, path: '/transactions' },
    { label: 'Thanh toán hóa đơn', icon: FaFileInvoiceDollar, path: '/dashboard' },
    { label: 'Tiền gửi tiết kiệm', icon: FaPiggyBank, path: '/dashboard' },
  ];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="page-eyebrow">TỔNG QUAN TÀI CHÍNH</p>
          <h1>Xin chào, {displayName}</h1>
          <p>Quản lý tài khoản và giao dịch của bạn tại một nơi.</p>
        </div>
        <button className="balance-visibility-btn" type="button" onClick={() => setShowBalance((value) => !value)}>
          {showBalance ? <FaEyeSlash /> : <FaEye />}
          {showBalance ? 'Ẩn số dư' : 'Hiện số dư'}
        </button>
      </header>

      {error && <div className="dashboard-error">{error}</div>}

      <section className="balance-banner">
        <div>
          <span>Tổng số dư khả dụng</span>
          <strong>{showBalance ? formatCurrency(totalBalance) : '•••••••••• VND'}</strong>
          <small>Cập nhật theo dữ liệu tài khoản hiện tại</small>
        </div>
        <FaWallet className="balance-banner-icon" />
      </section>

      <section className="quick-actions" aria-label="Giao dịch nhanh">
        {quickActions.map(({ label, icon: Icon, path }) => (
          <Link to={path} className="quick-action" key={label}>
            <span><Icon /></span>
            <strong>{label}</strong>
          </Link>
        ))}
      </section>

      <section className="dashboard-content-grid">
        <div className="dashboard-primary">
          <article className="bank-panel account-panel">
            <div className="panel-heading">
              <div>
                <h2>Tài khoản thanh toán</h2>
                <p>Danh sách tài khoản đang hoạt động</p>
              </div>
              <FaCreditCard />
            </div>
            <div className="account-list">
              {accounts.length > 0 ? accounts.map((account) => (
                <div className="account-row" key={account.id}>
                  <div>
                    <span className="account-type">{account.account_type === 'checking' ? 'Tài khoản thanh toán' : account.account_type}</span>
                    <strong>{account.account_number}</strong>
                  </div>
                  <div className="account-balance">
                    <span>Số dư khả dụng</span>
                    <strong>{showBalance ? formatCurrency(account.balance, account.currency) : '••••••••'}</strong>
                  </div>
                </div>
              )) : <p className="empty-state">Chưa có tài khoản thanh toán.</p>}
            </div>
          </article>

          <article className="bank-panel">
            <div className="panel-heading">
              <div>
                <h2>Giao dịch gần đây</h2>
                <p>5 giao dịch mới nhất của bạn</p>
              </div>
              <Link to="/transactions">Xem tất cả</Link>
            </div>
            <div className="recent-transaction-list">
              {recentTransactions.length > 0 ? recentTransactions.map((transaction) => (
                <div className="recent-transaction-row" key={transaction.id}>
                  <span className={`transaction-direction ${transaction.amount > 0 ? 'in' : 'out'}`}>
                    {transaction.amount > 0 ? <FaArrowDown /> : <FaArrowUp />}
                  </span>
                  <div className="recent-transaction-copy">
                    <strong>{transaction.description}</strong>
                    <small>{transaction.date} · {transaction.reference}</small>
                  </div>
                  <strong className={transaction.amount > 0 ? 'positive' : 'negative'}>
                    {transaction.amount > 0 ? '+' : ''}{formatCurrency(transaction.amount)}
                  </strong>
                </div>
              )) : <p className="empty-state">Chưa có giao dịch nào.</p>}
            </div>
          </article>
        </div>

        <aside className="dashboard-secondary">
          <article className="bank-panel cash-flow-panel">
            <div className="panel-heading">
              <div>
                <h2>Dòng tiền gần đây</h2>
                <p>Tổng hợp từ các giao dịch mới nhất</p>
              </div>
            </div>
            <div className="cash-flow-row">
              <span className="cash-flow-icon income"><FaArrowDown /></span>
              <div><span>Tiền vào</span><strong>{formatCurrency(totalIncome)}</strong></div>
            </div>
            <div className="cash-flow-row">
              <span className="cash-flow-icon expense"><FaArrowUp /></span>
              <div><span>Tiền ra</span><strong>{formatCurrency(totalExpense)}</strong></div>
            </div>
          </article>

          <article className="bank-panel security-panel">
            <FaShieldAlt />
            <div>
              <h2>Bảo mật tài khoản</h2>
              <p>Không chia sẻ mật khẩu, mã OTP hoặc thông tin đăng nhập với bất kỳ ai.</p>
            </div>
          </article>
        </aside>
      </section>
    </div>
  );
}

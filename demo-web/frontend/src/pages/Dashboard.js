import React, { useState } from 'react';
import { FaArrowDown, FaArrowUp, FaEye, FaEyeSlash, FaWallet, FaCreditCard, FaPiggyBank } from 'react-icons/fa';
import '../styles/dashboard.css';

export default function Dashboard({ user }) {
  const [showBalance, setShowBalance] = useState(true);

  // Mock data - In real app, fetch from backend
  const accounts = [
    {
      id: 1,
      type: 'Tài khoản thanh toán',
      balance: 5432.87,
      accountNumber: '1234567890',
      currency: 'VND'
    },
    {
      id: 2,
      type: 'Tài khoản tiết kiệm',
      balance: 12500.0,
      accountNumber: '0987654321',
      currency: 'VND'
    },
    {
      id: 3,
      type: 'Tài khoản đầu tư',
      balance: 28750.5,
      accountNumber: '1122334455',
      currency: 'VND'
    }
  ];

  const recentTransactions = [
    {
      id: 1,
      type: 'transfer',
      description: 'Chuyển khoản cho Nguyễn Văn A',
      amount: -250.0,
      date: '23 tháng 3, 2024',
      icon: '📤'
    },
    {
      id: 2,
      type: 'deposit',
      description: 'Lương cuối tháng 3/2024',
      amount: 3500.0,
      date: '22 tháng 3, 2024',
      icon: '📥'
    },
    {
      id: 3,
      type: 'payment',
      description: 'Thanh toán hóa đơn điện nước',
      amount: -89.99,
      date: '21 tháng 3, 2024',
      icon: '💳'
    },
    {
      id: 4,
      type: 'withdraw',
      description: 'Rút tiền tại ATM',
      amount: -200.0,
      date: '20 tháng 3, 2024',
      icon: '🏧'
    },
    {
      id: 5,
      type: 'transfer',
      description: 'Chuyển khoản từ Mẹ',
      amount: 500.0,
      date: '19 tháng 3, 2024',
      icon: '💰'
    }
  ];

  const quickActions = [
    { label: 'Chuyển tiền', icon: '💸' },
    { label: 'Thanh toán', icon: '💳' },
    { label: 'Hóa đơn', icon: '📄' },
    { label: 'Tiết kiệm', icon: '🏦' }
  ];

  const featuredServices = [
    { name: 'Tín dụng online', icon: '📊', desc: 'Vay tiêu dùng lãi suất thấp' },
    { name: 'Thẻ tín dụng', icon: '💎', desc: 'Nhiều ưu đãi và quà tặng' },
    { name: 'Bảo hiểm', icon: '🛡️', desc: 'Bảo vệ tài chính gia đình' },
    { name: 'Đầu tư chứng chỉ', icon: '📈', desc: 'Lợi suất hấp dẫn' }
  ];

  const chartData = [16, 12, 11, 20, 24, 15, 28, 19, 6, 12, 24, 16];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const getTotalBalance = () => {
    return accounts.reduce((sum, acc) => sum + acc.balance, 0);
  };

  const formatCurrency = (value) => value.toLocaleString('vi-VN');

  const summaryCards = [
    {
      title: 'Total Balance',
      value: getTotalBalance(),
      subtitle: 'Overall Wealth Summary',
      icon: <FaWallet />
    },
    {
      title: 'Expenses',
      value: recentTransactions.filter((item) => item.amount < 0).reduce((a, b) => a + Math.abs(b.amount), 0),
      subtitle: 'Total Expenses',
      icon: <FaArrowDown />
    },
    {
      title: 'Income',
      value: recentTransactions.filter((item) => item.amount > 0).reduce((a, b) => a + b.amount, 0),
      subtitle: 'Total Income This Month',
      icon: <FaArrowUp />
    },
    {
      title: 'Savings',
      value: accounts[1].balance,
      subtitle: 'This Month Savings',
      icon: <FaPiggyBank />
    }
  ];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Good Morning, {user?.full_name || user?.name || user?.username || 'Oripio'}!</h1>
          <p>Here's an overview of your financial health and recent activity.</p>
        </div>
      </header>

      <section className="overview-grid">
        {summaryCards.map((item, idx) => (
          <article className="overview-card" key={idx}>
            <div className="overview-title-row">
              <p>{item.title}</p>
              <button type="button" className="ghost-dot-btn" aria-label="options">•••</button>
            </div>
            <div className="overview-bottom-row">
              <span className="overview-icon">{item.icon}</span>
              <div>
                <h3>{showBalance ? `$${formatCurrency(item.value)}` : '••••••'}</h3>
                <small>{item.subtitle}</small>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="dashboard-main-grid">
        <div className="dashboard-left">
          <article className="panel panel-chart">
            <div className="panel-header">
              <div>
                <h2>Transactions Overview</h2>
                <p className="panel-amount">${formatCurrency(getTotalBalance())}</p>
              </div>
              <div className="chip-group">
                <button className="chip chip-active" type="button">Monthly</button>
                <button className="chip" type="button">Yearly</button>
              </div>
            </div>

            <div className="bar-chart">
              {chartData.map((value, idx) => (
                <div key={months[idx]} className="bar-column">
                  <div
                    className={`bar ${months[idx] === 'Jul' ? 'highlight' : ''}`}
                    style={{ height: `${value * 8}px` }}
                    title={`${months[idx]}: ${value}k`}
                  />
                  <span>{months[idx]}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel panel-table">
            <div className="panel-header">
              <h2>Transactions</h2>
              <div className="chip-group">
                <button className="chip chip-active" type="button">All</button>
                <button className="chip" type="button">Income</button>
                <button className="chip" type="button">Outcome</button>
              </div>
            </div>

            <div className="table-list">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id} className="table-row">
                  <div className="table-name">
                    <span>{transaction.icon}</span>
                    <div>
                      <strong>{transaction.description}</strong>
                      <small>{transaction.date}</small>
                    </div>
                  </div>
                  <span className={transaction.amount > 0 ? 'positive' : 'negative'}>
                    {transaction.amount > 0 ? '+' : ''}{transaction.amount.toLocaleString('vi-VN')} VND
                  </span>
                </div>
              ))}
            </div>
          </article>
        </div>

        <aside className="dashboard-right">
          <article className="panel card-showcase">
            <div className="panel-header compact">
              <h2>Your cards</h2>
              <button className="circle-btn" type="button">+</button>
            </div>
            <div className="virtual-card">
              <div className="card-left">
                <p>VISA</p>
                <small>Exp 09/24</small>
              </div>
              <div className="card-right">
                <FaCreditCard />
                <strong>1253 5432 3521 3090</strong>
              </div>
            </div>
            <button className="balance-toggle" onClick={() => setShowBalance(!showBalance)} type="button">
              {showBalance ? <FaEyeSlash /> : <FaEye />} {showBalance ? 'Ẩn số dư' : 'Hiện số dư'}
            </button>
          </article>

          <article className="panel quick-transfer-panel">
            <div className="panel-header compact">
              <h2>Quick Transfer</h2>
              <a href="/transfer">View all</a>
            </div>
            <div className="quick-action-stack">
              {quickActions.map((action, idx) => (
                <button key={idx} className="quick-pill" type="button">
                  <span>{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>
          </article>

          <article className="panel services-panel">
            <h2>Dịch vụ nổi bật</h2>
            <div className="service-list">
              {featuredServices.map((service, idx) => (
                <div key={idx} className="service-item">
                  <span>{service.icon}</span>
                  <div>
                    <strong>{service.name}</strong>
                    <small>{service.desc}</small>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="panel account-mini-list">
            <h2>Tài khoản của tôi</h2>
            {accounts.map((account) => (
              <div key={account.id} className="mini-account-row">
                <div>
                  <strong>{account.type}</strong>
                  <small>•••• {account.accountNumber.slice(-4)}</small>
                </div>
                <span>{showBalance ? `${formatCurrency(account.balance)} ${account.currency}` : '••••••'}</span>
              </div>
            ))}
          </article>
        </aside>
      </section>
    </div>
  );
}

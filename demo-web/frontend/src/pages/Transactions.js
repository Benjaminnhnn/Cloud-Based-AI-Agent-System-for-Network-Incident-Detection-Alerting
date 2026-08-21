import React, { useEffect, useMemo, useState } from 'react';
import { FaSearch, FaFilter, FaDownload, FaCalendar, FaArrowDown, FaArrowUp } from 'react-icons/fa';
import { bankingService, getApiErrorMessage } from '../services/api';
import '../styles/transactions.css';

export default function Transactions({ realtimeVersion = 0 }) {
  const currentUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
      return {};
    }
  }, []);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });

  useEffect(() => {
    async function loadTransactions() {
      if (!currentUser?.id) {
        setError('Vui lòng đăng nhập để xem lịch sử giao dịch.');
        return;
      }

      try {
        const response = await bankingService.listTransactions({ user_id: currentUser.id, limit: 100 });
        setTransactions((response.data || []).map((item) => {
          const outgoing = item.transaction_type === 'transfer_out';
          return {
            id: item.id,
            description: item.description || item.reference_code,
            amount: outgoing ? -Number(item.amount) : Number(item.amount),
            createdAt: new Date(item.created_at),
            date: new Date(item.created_at).toLocaleString('vi-VN'),
            status: item.status,
            category: item.transaction_type,
            reference: item.reference_code,
          };
        }));
        setError('');
      } catch (err) {
        setError(getApiErrorMessage(err, 'Không thể tải lịch sử giao dịch.'));
      }
    }

    loadTransactions();
  }, [currentUser?.id, realtimeVersion]);

  const filterOptions = {
    all: 'Tất cả',
    income: 'Tiền vào',
    expenses: 'Tiền ra',
    transfer: 'Chuyển tiền',
    pending: 'Đang xử lý',
  };

  const statusLabels = {
    completed: 'Thành công',
    pending: 'Đang xử lý',
    failed: 'Thất bại',
  };

  const formatCurrency = (value) => `${Number(value || 0).toLocaleString('vi-VN')} VND`;

  const filteredTransactions = transactions.filter((transaction) => {
    if (filter === 'income' && transaction.amount <= 0) return false;
    if (filter === 'expenses' && transaction.amount >= 0) return false;
    if (filter === 'transfer' && !transaction.category.startsWith('transfer')) return false;
    if (filter === 'pending' && transaction.status !== 'pending') return false;
    if (searchTerm && !`${transaction.description} ${transaction.reference}`.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (dateRange.startDate && transaction.createdAt < new Date(`${dateRange.startDate}T00:00:00`)) return false;
    if (dateRange.endDate && transaction.createdAt > new Date(`${dateRange.endDate}T23:59:59`)) return false;
    return true;
  });

  const totalExpenses = filteredTransactions.filter((item) => item.amount < 0).reduce((sum, item) => sum + Math.abs(item.amount), 0);
  const totalIncome = filteredTransactions.filter((item) => item.amount > 0).reduce((sum, item) => sum + item.amount, 0);

  const handleExport = () => {
    const csv = [
      ['Thời gian', 'Mã giao dịch', 'Nội dung', 'Số tiền', 'Trạng thái'],
      ...filteredTransactions.map((item) => [item.date, item.reference, item.description, item.amount, statusLabels[item.status] || item.status])
    ].map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n');

    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'lich-su-giao-dich.csv';
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="transactions">
      <header className="transactions-header">
        <div>
          <p className="page-eyebrow">TÀI KHOẢN</p>
          <h1>Lịch sử giao dịch</h1>
          <p>Tra cứu các giao dịch phát sinh trên tài khoản của bạn.</p>
        </div>
        <button className="export-btn" type="button" onClick={handleExport}>
          <FaDownload /> Xuất CSV
        </button>
      </header>

      {error && <div className="transactions-error">{error}</div>}

      <section className="transaction-summary">
        <div><span>Tổng tiền vào</span><strong className="positive">{formatCurrency(totalIncome)}</strong><small>{filteredTransactions.filter((item) => item.amount > 0).length} giao dịch</small></div>
        <div><span>Tổng tiền ra</span><strong className="negative">{formatCurrency(totalExpenses)}</strong><small>{filteredTransactions.filter((item) => item.amount < 0).length} giao dịch</small></div>
        <div><span>Chênh lệch</span><strong>{formatCurrency(totalIncome - totalExpenses)}</strong><small>{filteredTransactions.length} giao dịch được hiển thị</small></div>
      </section>

      <section className="transaction-tools">
        <div className="search-box">
          <FaSearch />
          <input
            type="text"
            placeholder="Tìm theo nội dung hoặc mã giao dịch"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="date-range">
          <FaCalendar />
          <input type="date" value={dateRange.startDate} onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })} />
          <span>đến</span>
          <input type="date" value={dateRange.endDate} onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })} />
        </div>
      </section>

      <section className="transaction-content">
        <div className="filter-tabs">
          <FaFilter />
          {Object.entries(filterOptions).map(([key, label]) => (
            <button key={key} type="button" className={filter === key ? 'active' : ''} onClick={() => setFilter(key)}>
              {label}
            </button>
          ))}
        </div>

        <div className="transaction-list">
          {filteredTransactions.length > 0 ? filteredTransactions.map((transaction) => (
            <div className="transaction-item" key={transaction.id}>
              <span className={`transaction-icon ${transaction.amount > 0 ? 'income' : 'expense'}`}>
                {transaction.amount > 0 ? <FaArrowDown /> : <FaArrowUp />}
              </span>
              <div className="transaction-description">
                <strong>{transaction.description}</strong>
                <small>{transaction.date} · {transaction.reference}</small>
              </div>
              <span className={`status-badge status-${transaction.status}`}>
                {statusLabels[transaction.status] || transaction.status}
              </span>
              <strong className={transaction.amount > 0 ? 'positive' : 'negative'}>
                {transaction.amount > 0 ? '+' : ''}{formatCurrency(transaction.amount)}
              </strong>
            </div>
          )) : <div className="no-transactions">Không tìm thấy giao dịch phù hợp.</div>}
        </div>
      </section>
    </div>
  );
}

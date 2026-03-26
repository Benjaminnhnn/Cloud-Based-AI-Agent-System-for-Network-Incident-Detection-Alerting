import React, { useState } from 'react';
import { FaSearch, FaFilter, FaDownload, FaCalendar } from 'react-icons/fa';
import '../styles/transactions.css';

export default function Transactions() {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({
    startDate: '2024-01-01',
    endDate: '2024-03-23'
  });

  const allTransactions = [
    { id: 1, type: 'transfer-out', description: 'Transfer to John Smith', amount: -250.00, date: '2024-03-23 14:32', status: 'completed', category: 'transfer' },
    { id: 2, type: 'deposit', description: 'Salary Deposit', amount: 3500.00, date: '2024-03-22 09:15', status: 'completed', category: 'income' },
    { id: 3, type: 'payment', description: 'Online Shopping - Amazon', amount: -89.99, date: '2024-03-21 18:45', status: 'completed', category: 'shopping' },
    { id: 4, type: 'withdraw', description: 'ATM Withdrawal', amount: -200.00, date: '2024-03-20 22:30', status: 'completed', category: 'cash' },
    { id: 5, type: 'transfer-in', description: 'Transfer from Mom', amount: 500.00, date: '2024-03-19 11:20', status: 'completed', category: 'transfer' },
    { id: 6, type: 'payment', description: 'Electric Bill', amount: -125.50, date: '2024-03-18 08:00', status: 'completed', category: 'utilities' },
    { id: 7, type: 'deposit', description: 'Check Deposit', amount: 1200.00, date: '2024-03-17 15:00', status: 'completed', category: 'income' },
    { id: 8, type: 'payment', description: 'Netflix Subscription', amount: -15.99, date: '2024-03-16 00:05', status: 'completed', category: 'subscription' },
    { id: 9, type: 'withdraw', description: 'ATM Withdrawal', amount: -150.00, date: '2024-03-15 19:45', status: 'completed', category: 'cash' },
    { id: 10, type: 'transfer-out', description: 'Transfer to Sister', amount: -300.00, date: '2024-03-14 13:20', status: 'pending', category: 'transfer' },
    { id: 11, type: 'payment', description: 'Gas Station', amount: -52.75, date: '2024-03-13 17:30', status: 'completed', category: 'gas' },
    { id: 12, type: 'deposit', description: 'Freelance Payment', amount: 750.00, date: '2024-03-12 10:00', status: 'completed', category: 'income' },
  ];

  const filterOptions = {
    all: 'All Transactions',
    income: 'Income',
    expenses: 'Expenses',
    transfer: 'Transfers',
    pending: 'Pending',
    shopping: 'Shopping',
    utilities: 'Utilities'
  };

  const getFilteredTransactions = () => {
    let filtered = allTransactions;

    // Filter by type
    if (filter !== 'all') {
      if (filter === 'income') {
        filtered = filtered.filter(t => t.amount > 0);
      } else if (filter === 'expenses') {
        filtered = filtered.filter(t => t.amount < 0);
      } else if (filter === 'pending') {
        filtered = filtered.filter(t => t.status === 'pending');
      } else {
        filtered = filtered.filter(t => t.category === filter);
      }
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(t =>
        t.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  };

  const filteredTransactions = getFilteredTransactions();
  const totalExpenses = filteredTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const totalIncome = filteredTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);

  const handleExport = () => {
    const csv = [
      ['Date', 'Description', 'Type', 'Amount', 'Status'],
      ...filteredTransactions.map(t => [
        t.date,
        t.description,
        t.category,
        t.amount,
        t.status
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transactions.csv';
    a.click();
  };

  const getCategoryColor = (category) => {
    const colors = {
      income: 'category-green',
      transfer: 'category-blue',
      shopping: 'category-red',
      utilities: 'category-orange',
      gas: 'category-yellow',
      subscription: 'category-purple',
      cash: 'category-gray'
    };
    return colors[category] || 'category-gray';
  };

  return (
    <div className="transactions">
      <div className="transactions-header">
        <h1>Transactions</h1>
        <p>View and manage all your account transactions</p>
      </div>

      {/* Filters Section */}
      <div className="filters-section">
        <div className="search-box">
          <FaSearch className="search-icon" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="date-range">
          <FaCalendar className="calendar-icon" />
          <input
            type="date"
            value={dateRange.startDate}
            onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })}
          />
          <span>to</span>
          <input
            type="date"
            value={dateRange.endDate}
            onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })}
          />
        </div>

        <button className="export-btn" onClick={handleExport}>
          <FaDownload /> Export CSV
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button
          className={`tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          <FaFilter /> All
        </button>
        {Object.entries(filterOptions).slice(1).map(([key, label]) => (
          <button
            key={key}
            className={`tab ${filter === key ? 'active' : ''}`}
            onClick={() => setFilter(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card income">
          <h3>Total Income</h3>
          <p className="summary-amount">${totalIncome.toFixed(2)}</p>
          <p className="summary-count">{filteredTransactions.filter(t => t.amount > 0).length} transactions</p>
        </div>
        <div className="summary-card expense">
          <h3>Total Expenses</h3>
          <p className="summary-amount">${totalExpenses.toFixed(2)}</p>
          <p className="summary-count">{filteredTransactions.filter(t => t.amount < 0).length} transactions</p>
        </div>
        <div className="summary-card net">
          <h3>Net Flow</h3>
          <p className="summary-amount">${(totalIncome - totalExpenses).toFixed(2)}</p>
          <p className="summary-count">{filteredTransactions.length} total</p>
        </div>
      </div>

      {/* Transactions List */}
      <div className="transactions-list">
        {filteredTransactions.length > 0 ? (
          <div className="transaction-items">
            {filteredTransactions.map((transaction) => (
              <div key={transaction.id} className="transaction-item">
                <div className="transaction-icon">
                  <div className={`icon-circle ${getCategoryColor(transaction.category)}`}>
                    {transaction.amount > 0 ? '↓' : '↑'}
                  </div>
                </div>

                <div className="transaction-details">
                  <h4>{transaction.description}</h4>
                  <p>{transaction.date}</p>
                </div>

                <div className="transaction-status">
                  <span className={`badge badge-${transaction.status}`}>
                    {transaction.status}
                  </span>
                </div>

                <div className="transaction-amount">
                  <span className={transaction.amount > 0 ? 'positive' : 'negative'}>
                    {transaction.amount > 0 ? '+' : ''}{transaction.amount.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-transactions">
            <p>No transactions found</p>
          </div>
        )}
      </div>
    </div>
  );
}

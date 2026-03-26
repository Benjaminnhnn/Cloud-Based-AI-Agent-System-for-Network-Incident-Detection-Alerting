import React, { useState } from 'react';
import { FaUser, FaPhone, FaPaperPlane, FaCheckCircle } from 'react-icons/fa';
import '../styles/transfer.css';

export default function Transfer() {
  const [transferData, setTransferData] = useState({
    recipientName: '',
    recipientEmail: '',
    recipientPhone: '',
    amount: '',
    description: '',
    fromAccount: 'checking'
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const accounts = [
    { value: 'checking', label: 'Checking Account ($5,432.87)' },
    { value: 'savings', label: 'Savings Account ($12,500.00)' },
    { value: 'investment', label: 'Investment Account ($28,750.50)' },
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTransferData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      console.log('Transfer submitted:', transferData);
      setLoading(false);
      setSubmitted(true);
      
      // Reset form after 3 seconds
      setTimeout(() => {
        setTransferData({
          recipientName: '',
          recipientEmail: '',
          recipientPhone: '',
          amount: '',
          description: '',
          fromAccount: 'checking'
        });
        setSubmitted(false);
      }, 3000);
    }, 1500);
  };

  if (submitted) {
    return (
      <div className="transfer-success">
        <div className="success-card">
          <FaCheckCircle className="success-icon" />
          <h2>Transfer Successful!</h2>
          <p>${transferData.amount} has been transferred to {transferData.recipientName}</p>
          <p className="success-ref">Reference ID: TXN-{Date.now()}</p>
          <p className="success-time">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="transfer">
      <div className="transfer-header">
        <h1>Money Transfer</h1>
        <p>Send money securely to friends and family</p>
      </div>

      <div className="transfer-container">
        <div className="transfer-form-wrapper">
          <form className="transfer-form" onSubmit={handleSubmit}>
            {/* From Account */}
            <fieldset className="form-section">
              <legend>From</legend>
              <div className="form-group">
                <label>Select Account</label>
                <select
                  name="fromAccount"
                  value={transferData.fromAccount}
                  onChange={handleChange}
                  className="account-select"
                >
                  {accounts.map(account => (
                    <option key={account.value} value={account.value}>
                      {account.label}
                    </option>
                  ))}
                </select>
              </div>
            </fieldset>

            {/* Recipient Details */}
            <fieldset className="form-section">
              <legend>Recipient Details</legend>
              
              <div className="form-group">
                <label>Full Name</label>
                <div className="input-group">
                  <FaUser className="input-icon" />
                  <input
                    type="text"
                    name="recipientName"
                    placeholder="Recipient's full name"
                    value={transferData.recipientName}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    name="recipientEmail"
                    placeholder="recipient@email.com"
                    value={transferData.recipientEmail}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Phone Number</label>
                  <div className="input-group">
                    <FaPhone className="input-icon" />
                    <input
                      type="tel"
                      name="recipientPhone"
                      placeholder="+1 (555) 000-0000"
                      value={transferData.recipientPhone}
                      onChange={handleChange}
                    />
                  </div>
                </div>
              </div>
            </fieldset>

            {/* Transfer Amount */}
            <fieldset className="form-section">
              <legend>Transfer Amount</legend>
              
              <div className="form-group">
                <label>Amount (USD)</label>
                <div className="input-group amount-input">
                  <span className="currency-symbol">$</span>
                  <input
                    type="number"
                    name="amount"
                    placeholder="0.00"
                    value={transferData.amount}
                    onChange={handleChange}
                    step="0.01"
                    min="0"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description (Optional)</label>
                <textarea
                  name="description"
                  placeholder="e.g., Rent payment, Birthday gift..."
                  value={transferData.description}
                  onChange={handleChange}
                  rows="3"
                />
              </div>
            </fieldset>

            {/* Summary */}
            <div className="transfer-summary">
              <h3>Transfer Summary</h3>
              <div className="summary-item">
                <span>To Account:</span>
                <span>{transferData.recipientName || 'Not specified'}</span>
              </div>
              <div className="summary-item">
                <span>Amount:</span>
                <span className="amount-value">
                  ${parseFloat(transferData.amount || 0).toFixed(2)}
                </span>
              </div>
              <div className="summary-item">
                <span>Fee:</span>
                <span>Free</span>
              </div>
              <div className="summary-divider"></div>
              <div className="summary-item total">
                <span>Total Debit:</span>
                <span className="total-value">
                  ${parseFloat(transferData.amount || 0).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="form-actions">
              <button 
                type="submit" 
                className="transfer-btn"
                disabled={loading || !transferData.recipientName || !transferData.amount}
              >
                {loading ? 'Processing...' : (
                  <>
                    <FaPaperPlane /> Send Money
                  </>
                )}
              </button>
              <button type="reset" className="reset-btn">
                Clear Form
              </button>
            </div>
          </form>
        </div>

        {/* Info Panel */}
        <div className="transfer-info">
          <div className="info-card">
            <h3>⏱️ Transfer Speed</h3>
            <p>Most transfers are completed within 2-3 business days</p>
          </div>
          
          <div className="info-card">
            <h3>🔒 Security</h3>
            <p>All transfers are encrypted and secure. Your data is protected.</p>
          </div>
          
          <div className="info-card">
            <h3>💰 Limits</h3>
            <p>Daily limit: $10,000 | Monthly limit: $50,000</p>
          </div>

          <div className="recent-recipients">
            <h3>Recent Recipients</h3>
            <div className="recipient-list">
              {['John Smith', 'Sarah Johnson', 'Mike Davis'].map((name, idx) => (
                <button
                  key={idx}
                  className="recipient-btn"
                  onClick={() => setTransferData(prev => ({ ...prev, recipientName: name }))}
                >
                  {name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

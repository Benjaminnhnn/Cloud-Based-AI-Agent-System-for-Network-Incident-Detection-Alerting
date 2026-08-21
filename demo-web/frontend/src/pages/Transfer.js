import React, { useEffect, useMemo, useState } from 'react';
import {
  FaUniversity,
  FaPaperPlane,
  FaCheckCircle,
  FaShieldAlt,
  FaClock,
  FaInfoCircle,
  FaSearch,
  FaUserCheck
} from 'react-icons/fa';
import { bankingService, getApiErrorMessage } from '../services/api';
import '../styles/transfer.css';

const initialTransfer = {
  recipientAccountNumber: '',
  recipientName: '',
  amount: '',
  description: '',
};

export default function Transfer({ realtimeVersion = 0 }) {
  const currentUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
      return {};
    }
  }, []);
  const [transferData, setTransferData] = useState(initialTransfer);
  const [sourceAccount, setSourceAccount] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastTransfer, setLastTransfer] = useState(null);

  const formatCurrency = (value, currency = 'VND') =>
    `${Number(value || 0).toLocaleString('vi-VN')} ${currency}`;

  useEffect(() => {
    async function loadSourceAccount() {
      if (!currentUser?.id) {
        setError('Vui lòng đăng nhập để thực hiện chuyển tiền.');
        return;
      }

      try {
        const response = await bankingService.listAccounts(currentUser.id);
        const accounts = response.data || [];
        const primaryAccount = accounts.find((account) => account.is_primary) || accounts[0];
        if (!primaryAccount) {
          setError('Tài khoản của bạn chưa có tài khoản thanh toán.');
          return;
        }
        setSourceAccount(primaryAccount);
        setError('');
      } catch (err) {
        setError(getApiErrorMessage(err, 'Không thể tải tài khoản nguồn.'));
      }
    }

    loadSourceAccount();
  }, [currentUser?.id, realtimeVersion]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'recipientAccountNumber') {
      setTransferData((prev) => ({
        ...prev,
        recipientAccountNumber: value.replace(/\D/g, ''),
        recipientName: '',
      }));
      return;
    }
    setTransferData((prev) => ({ ...prev, [name]: value }));
  };

  const lookupRecipient = async () => {
    if (!transferData.recipientAccountNumber) return null;

    setLookupLoading(true);
    setError('');
    try {
      const response = await bankingService.lookupAccount(transferData.recipientAccountNumber);
      setTransferData((prev) => ({ ...prev, recipientName: response.data.account_name }));
      return response.data;
    } catch (err) {
      setTransferData((prev) => ({ ...prev, recipientName: '' }));
      setError(getApiErrorMessage(err, 'Không tìm thấy tài khoản người nhận.'));
      return null;
    } finally {
      setLookupLoading(false);
    }
  };

  const handleReset = () => {
    setTransferData(initialTransfer);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const recipient = transferData.recipientName ? true : await lookupRecipient();
      if (!recipient) return;

      const response = await bankingService.createTransfer({
        sender_user_id: currentUser.id,
        recipient_account_number: transferData.recipientAccountNumber,
        amount: transferData.amount,
        description: transferData.description || `Chuyển tiền đến ${transferData.recipientName}`,
      });

      const accountsResponse = await bankingService.listAccounts(currentUser.id);
      const accounts = accountsResponse.data || [];
      setSourceAccount(accounts.find((account) => account.is_primary) || accounts[0] || null);
      setLastTransfer(response.data);
      setSubmitted(true);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Giao dịch không thành công. Vui lòng kiểm tra lại thông tin.'));
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="transfer-success">
        <div className="success-card">
          <FaCheckCircle className="success-icon" />
          <h2>Chuyển tiền thành công</h2>
          <p>Bạn đã chuyển <strong>{formatCurrency(transferData.amount)}</strong> đến {transferData.recipientName}.</p>
          <div className="success-detail">
            <span>Mã giao dịch</span>
            <strong>{lastTransfer?.reference_code || 'Đang xử lý'}</strong>
          </div>
          <button
            type="button"
            onClick={() => {
              handleReset();
              setSubmitted(false);
              setLastTransfer(null);
            }}
          >
            Thực hiện giao dịch khác
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="transfer">
      <header className="transfer-header">
        <p className="page-eyebrow">GIAO DỊCH</p>
        <h1>Chuyển tiền</h1>
        <p>Chuyển tiền nhanh chóng bằng số tài khoản VietTien.</p>
      </header>

      <div className="transfer-container">
        <form className="transfer-form" onSubmit={handleSubmit}>
          <section className="transfer-section">
            <div className="section-heading">
              <span>1</span>
              <div><h2>Tài khoản nguồn</h2><p>Tài khoản chính của người dùng đang đăng nhập</p></div>
            </div>
            <div className="source-account-card">
              <span className="source-account-icon"><FaUniversity /></span>
              <div>
                <small>Tài khoản thanh toán</small>
                <strong>{sourceAccount?.account_number || 'Đang tải tài khoản...'}</strong>
              </div>
              <div className="source-account-balance">
                <small>Số dư khả dụng</small>
                <strong>{sourceAccount ? formatCurrency(sourceAccount.balance, sourceAccount.currency) : '---'}</strong>
              </div>
            </div>
          </section>

          <section className="transfer-section">
            <div className="section-heading">
              <span>2</span>
              <div><h2>Thông tin người nhận</h2><p>Nhập số tài khoản đã được cấp khi đăng ký</p></div>
            </div>
            <div className="form-group">
              <label>Số tài khoản người nhận</label>
              <div className="input-group account-number-input">
                <FaUniversity className="input-icon" />
                <input
                  type="text"
                  inputMode="numeric"
                  name="recipientAccountNumber"
                  placeholder="Nhập số tài khoản"
                  value={transferData.recipientAccountNumber}
                  onChange={handleChange}
                  onBlur={lookupRecipient}
                  maxLength="32"
                  required
                />
                <button type="button" onClick={lookupRecipient} disabled={lookupLoading || !transferData.recipientAccountNumber}>
                  <FaSearch /> {lookupLoading ? 'Đang tra cứu' : 'Tra cứu'}
                </button>
              </div>
            </div>
            {transferData.recipientName && (
              <div className="recipient-verified">
                <FaUserCheck />
                <div>
                  <span>Tên người nhận</span>
                  <strong>{transferData.recipientName}</strong>
                </div>
              </div>
            )}
          </section>

          <section className="transfer-section">
            <div className="section-heading">
              <span>3</span>
              <div><h2>Thông tin giao dịch</h2><p>Nhập số tiền và nội dung chuyển khoản</p></div>
            </div>
            <div className="form-group">
              <label>Số tiền</label>
              <div className="input-group amount-input">
                <input
                  type="number"
                  name="amount"
                  placeholder="0"
                  value={transferData.amount}
                  onChange={handleChange}
                  step="1"
                  min="1"
                  required
                />
                <span className="currency-symbol">VND</span>
              </div>
            </div>
            <div className="form-group">
              <label>Nội dung chuyển tiền</label>
              <textarea
                name="description"
                placeholder="Nhập nội dung chuyển tiền"
                value={transferData.description}
                onChange={handleChange}
                rows="3"
                maxLength="140"
              />
            </div>
          </section>

          {error && <div className="transfer-error">{error}</div>}

          <div className="form-actions">
            <button type="button" className="reset-btn" onClick={handleReset}>Làm lại</button>
            <button
              type="submit"
              className="transfer-btn"
              disabled={loading || !sourceAccount || !transferData.recipientAccountNumber || !transferData.recipientName || !transferData.amount}
            >
              <FaPaperPlane /> {loading ? 'Đang xử lý...' : 'Chuyển tiền'}
            </button>
          </div>
        </form>

        <aside className="transfer-sidebar">
          <section className="transfer-summary">
            <h2>Thông tin giao dịch</h2>
            <div><span>Từ tài khoản</span><strong>{sourceAccount?.account_number || 'Đang tải'}</strong></div>
            <div><span>Đến tài khoản</span><strong>{transferData.recipientAccountNumber || 'Chưa nhập'}</strong></div>
            <div><span>Người nhận</span><strong>{transferData.recipientName || 'Chưa tra cứu'}</strong></div>
            <div><span>Số tiền</span><strong className="summary-amount">{formatCurrency(transferData.amount)}</strong></div>
            <div><span>Phí giao dịch</span><strong>Miễn phí</strong></div>
          </section>

          <section className="transfer-note">
            <h2><FaShieldAlt /> An toàn giao dịch</h2>
            <p>Kiểm tra kỹ số tài khoản, tên người nhận và số tiền trước khi xác nhận.</p>
          </section>
          <section className="transfer-note">
            <h2><FaClock /> Thời gian xử lý</h2>
            <p>Giao dịch nội bộ được xử lý ngay sau khi hoàn tất.</p>
          </section>
          <section className="transfer-note">
            <h2><FaInfoCircle /> Hạn mức</h2>
            <p>Hạn mức giao dịch phụ thuộc vào cấu hình tài khoản của bạn.</p>
          </section>
        </aside>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { secureFetch } from '../api';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('teacher');
  const [temporaryPassword, setTemporaryPassword] = useState('');
  
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Mock list of staff for UI purposes
  const staffMembers = [
    { id: 1, name: "יגל אטיאס", role: "Principal (Admin)", color: "#e1bee7" },
    { id: 2, name: "הרב אברהם קופר", role: "Counselor", color: "#b2dfdb" },
    { id: 3, name: "נעמי כהן", role: "Teacher", color: "#ffcc80" }
  ];

  const handleOnboardSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      const response = await secureFetch('/admin/staff', {
        method: 'POST',
        body: JSON.stringify({
          email,
          full_name: fullName,
          role,
          temporary_password: temporaryPassword
        })
      });

      if (response.detail) {
        throw new Error(response.detail);
      }

      setMessage(`החשבון של ${fullName} נוצר בהצלחה עם הצפנת KEK/DEK מאובטחת!`);
      setEmail('');
      setFullName('');
      setTemporaryPassword('');
    } catch (err) {
      setError(err.message || 'אירעה שגיאה ביצירת החשבון');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-dashboard-wrapper">
      <div className="welcome-header">
        <h1>לוח בקרה ניהולי ⚙️</h1>
        <p>ניהול הרשאות, צוות והגדרות מערכת</p>
      </div>

      <div className="admin-2col">
        {/* Onboarding Form */}
        <div className="glass-panel admin-form-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-blue)' }}>
            <h3>הוספת איש צוות חדש (הצפנת קצה-לקצה)</h3>
          </div>
          <div className="panel-content">
            <form onSubmit={handleOnboardSubmit} className="onboard-form">
              <div className="form-group">
                <label>שם מלא</label>
                <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="לדוגמה: אברהם כהן" />
              </div>
              <div className="form-group">
                <label>דוא״ל / שם משתמש</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="teacher@yagel-yaakov.edu" />
              </div>
              <div className="form-group">
                <label>תפקיד</label>
                <select value={role} onChange={e => setRole(e.target.value)}>
                  <option value="teacher">מורה (Teacher)</option>
                  <option value="counselor">יועץ (Counselor)</option>
                  <option value="admin">מנהל (Admin)</option>
                </select>
              </div>
              <div className="form-group">
                <label>סיסמה זמנית (תשמש כ-KEK)</label>
                <input type="text" value={temporaryPassword} onChange={e => setTemporaryPassword(e.target.value)} required placeholder="סיסמה חזקה..." />
                <small>סיסמה זו תשמש ליצירת מפתח ההצפנה (KEK) עבור המורה.</small>
              </div>

              {error && <div className="admin-error">{error}</div>}
              {message && <div className="admin-success">{message}</div>}

              <button type="submit" disabled={isLoading} className="btn-submit-staff">
                {isLoading ? 'יוצר חשבון...' : 'צור חשבון והצפן מפתח'}
              </button>
            </form>
          </div>
        </div>

        {/* Staff List */}
        <div className="glass-panel staff-list-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-purple)' }}>
            <h3>צוות חינוכי (3)</h3>
          </div>
          <div className="panel-content">
            {staffMembers.map(s => (
              <div key={s.id} className="pill-card staff-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <div className="avatar" style={{ backgroundColor: s.color }}>{s.name.charAt(0)}</div>
                  <div>
                    <div style={{ fontWeight: '600' }}>{s.name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)' }}>{s.role}</div>
                  </div>
                </div>
                <button className="btn-manage-staff">ניהול</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

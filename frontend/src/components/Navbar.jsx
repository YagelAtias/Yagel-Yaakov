import React from 'react';
import './Navbar.css';

export default function Navbar({ role, activeTab, setActiveTab, onLogout }) {
  return (
    <nav className="navbar">
      {/* Brand */}
      <div className="navbar-brand">
        <div className="logo-placeholder">
          <span>YY</span>
        </div>
        <div className="navbar-title">
          <h2>יגל-יעקב</h2>
        </div>
      </div>
      
      {/* Links */}
      <div className="nav-links">
        {role === 'student' ? (
          <>
            <div className={`nav-link ${activeTab === 'ראשי' ? 'active' : ''}`} onClick={() => setActiveTab('ראשי')}>ראשי</div>
            <div className={`nav-link ${activeTab === 'הפניות שלי' ? 'active' : ''}`} onClick={() => setActiveTab('הפניות שלי')}>הפניות שלי</div>
            <div className={`nav-link ${activeTab === 'לוח מבחנים' ? 'active' : ''}`} onClick={() => setActiveTab('לוח מבחנים')}>לוח מבחנים</div>
          </>
        ) : (
          <>
            <div className={`nav-link ${activeTab === 'ראשי' ? 'active' : ''}`} onClick={() => setActiveTab('ראשי')}>ראשי</div>
            <div className={`nav-link ${activeTab === 'תלמידים' ? 'active' : ''}`} onClick={() => setActiveTab('תלמידים')}>תלמידים</div>
            <div className={`nav-link ${activeTab === 'כיתות' ? 'active' : ''}`} onClick={() => setActiveTab('כיתות')}>כיתות</div>
            <div className={`nav-link ${activeTab === 'יציאות' ? 'active' : ''}`} onClick={() => setActiveTab('יציאות')}>יציאות</div>
            <div className={`nav-link ${activeTab === 'מבחנים' ? 'active' : ''}`} onClick={() => setActiveTab('מבחנים')}>מבחנים</div>
            {role === 'admin' && (
              <div className={`nav-link ${activeTab === 'ניהול' ? 'active' : ''}`} onClick={() => setActiveTab('ניהול')}>ניהול צוות</div>
            )}
          </>
        )}
      </div>

      {/* Profile */}
      <div className="user-profile">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginLeft: '10px' }}>
          <span>{role === 'student' ? 'דניאל לוי' : 'צוות חינוכי'}</span>
          <span onClick={onLogout} style={{ fontSize: '0.75rem', color: '#e74c3c', cursor: 'pointer', fontWeight: 'bold' }}>התנתק 🚪</span>
        </div>
        <div className="avatar" style={{
          backgroundColor: role === 'student' ? '#b2dfdb' : '#e1bee7', 
          color: role === 'student' ? '#00695c' : '#6a1b9a', 
          width: '35px', 
          height: '35px'
        }}>
          {role === 'student' ? 'ד' : 'צ'}
        </div>
      </div>
    </nav>
  );
}

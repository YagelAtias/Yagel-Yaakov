import React from 'react';
import './Navbar.css';

export default function Navbar({ role }) {
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
            <div className="nav-link active">ראשי</div>
            <div className="nav-link">הפניות שלי</div>
            <div className="nav-link">לוח מבחנים</div>
          </>
        ) : (
          <>
            <div className="nav-link active">ראשי</div>
            <div className="nav-link">תלמידים</div>
            <div className="nav-link">כיתות</div>
            <div className="nav-link">יציאות</div>
            <div className="nav-link">מבחנים</div>
            <div className="nav-link">ניהול</div>
          </>
        )}
      </div>

      {/* Profile */}
      <div className="user-profile">
        <span>{role === 'student' ? 'דניאל לוי' : 'צוות חינוכי'}</span>
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

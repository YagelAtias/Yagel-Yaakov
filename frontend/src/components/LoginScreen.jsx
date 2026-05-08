import React, { useState } from 'react';
import { loginAPI } from '../api';
import './LoginScreen.css';

export default function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // 1. Send credentials to Python FastAPI Backend
      const response = await loginAPI(email, password);
      
      // 2. Save the secure JWT token to the browser's local storage
      localStorage.setItem('jwt_token', response.access_token);
      
      // 3. Transition to the correct dashboard based on backend response
      onLogin(response.role);
    } catch (err) {
      setError(err.message || 'אירעה שגיאה בהתחברות');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Huge Logo Placeholder */}
        <div className="login-logo">
          <span>YY</span>
        </div>
        
        <h1 className="login-title">מערכת יגל-יעקב</h1>
        <p className="login-subtitle">התחברות לצוות חינוכי ותלמידים</p>

        {error && <div style={{ color: 'white', backgroundColor: '#e74c3c', padding: '10px', borderRadius: '10px', width: '100%', textAlign: 'center', marginBottom: '15px' }}>{error}</div>}

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label>דוא״ל / שם משתמש</label>
            <input 
              type="email" 
              placeholder="you@school.edu" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              dir="ltr" /* Force LTR for email typing so English characters look right */
              style={{ textAlign: 'right' }} /* Keep cursor on the right */
            />
          </div>
          
          <div className="input-group">
            <label>סיסמה</label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              dir="ltr"
              style={{ textAlign: 'right' }}
            />
          </div>

          <button type="submit" className="login-button" disabled={isLoading} style={{ opacity: isLoading ? 0.7 : 1 }}>
            {isLoading ? 'מתחבר...' : 'התחבר למערכת'}
          </button>

          {/* TEMPORARY DEVELOPMENT BYPASS BUTTONS */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '15px', borderTop: '1px solid #e0e0e0', paddingTop: '15px' }}>
            <p style={{ fontSize: '0.8rem', textAlign: 'center', color: '#7f8c8d', margin: '0' }}>כפתורי עקיפה (זמני לפיתוח):</p>
            <button 
              type="button" 
              onClick={() => onLogin('teacher')} 
              className="login-button"
              style={{ padding: '10px', fontSize: '1rem', backgroundColor: '#e0e0e0', color: '#333', boxShadow: 'none' }}
            >
              התחבר כצוות חינוכי
            </button>
            <button 
              type="button" 
              onClick={() => onLogin('student')} 
              className="login-button" 
              style={{ padding: '10px', fontSize: '1rem', backgroundColor: '#e1bee7', color: '#6a1b9a', boxShadow: 'none' }}
            >
              התחבר כתלמיד
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

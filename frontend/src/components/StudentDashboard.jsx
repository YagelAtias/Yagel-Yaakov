import React, { useState } from 'react';
import './TeacherDashboard.css';

export default function StudentDashboard() {
  const [message, setMessage] = useState('');
  
  const handleSendMessage = (e) => {
    e.preventDefault();
    alert('הודעתך נשלחה לאיש הצוות בהצלחה! (נותחה ברקע על ידי DistressEngine)');
    setMessage('');
  };

  const exams = [
    { id: 201, subject: "מבחן אמצע במתמטיקה", date: "כ\"ד בחשוון | 4 נובמבר, 11:30" }
  ];

  const todaysSchedule = [
    { id: 1, period: "שיעור 1", time: "08:30 - 09:15", subject: "תלמוד (גמרא)", teacher: "הרב יעקב" },
    { id: 2, period: "שיעור 2", time: "09:15 - 10:00", subject: "מתמטיקה", teacher: "המורה דוד" },
    { id: 3, period: "שיעור 3", time: "10:15 - 11:00", subject: "היסטוריה", teacher: "המורה יעל" }
  ];

  const inputStyle = {
    width: '100%', 
    padding: '12px 16px', 
    borderRadius: '12px', 
    border: 'none',
    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
    marginTop: '6px', 
    fontFamily: 'inherit', 
    fontSize: '0.95rem',
    boxSizing: 'border-box',
    backgroundColor: '#ffffff'
  };

  const labelStyle = {
    fontSize: '0.9rem', 
    fontWeight: '700', 
    color: '#333'
  };

  return (
    <div className="dashboard-wrapper">
      <div className="welcome-header" style={{ textAlign: 'right', marginBottom: '30px' }}>
        <h1 style={{ color: '#ce93d8', fontSize: '2.8rem', fontWeight: '800', marginBottom: '5px' }}>שלום דניאל! 👋</h1>
        <p style={{ fontSize: '1.1rem', color: '#7f8c8d' }}>היום יום שני, י"ז בחשוון | 28 באוקטובר</p>
      </div>

      <div className="dashboard-3col">
        
        {/* Column 1 (Right in RTL): Messaging */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: '#b2dfdb', color: '#00695c' }}>
            <h3>הודעה לצוות (מדריך / יועץ)</h3>
          </div>
          <div className="panel-content" style={{ display: 'flex', flexDirection: 'column' }}>
            <p style={{ fontSize: '0.9rem', marginBottom: '20px', color: '#555' }}>
              צריך משהו? רוצה לשתף? אנחנו כאן בשבילך.
            </p>
            <form onSubmit={handleSendMessage} style={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
              <div style={{ marginBottom: '15px' }}>
                <label style={labelStyle}>שלח אל:</label>
                <select style={inputStyle}>
                  <option>בחר איש צוות...</option>
                  <option>הרב יעקב (מחנך כיתה)</option>
                  <option>אביתר (מדריך פנימייה)</option>
                  <option>אורי (יועץ בית הספר)</option>
                </select>
              </div>
              <textarea 
                style={{ 
                  ...inputStyle,
                  flexGrow: 1, 
                  minHeight: '120px', 
                  resize: 'none',
                  marginBottom: '20px'
                }}
                placeholder="כתוב כאן..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
              />
              <button type="submit" style={{ 
                padding: '14px', 
                borderRadius: '12px', 
                border: 'none', 
                fontWeight: '800', 
                fontSize: '1rem', 
                width: '100%', 
                cursor: 'pointer', 
                backgroundColor: '#b2dfdb', 
                color: '#00695c',
                marginTop: 'auto'
              }}>
                שלח הודעה
              </button>
            </form>
          </div>
        </div>

        {/* Column 2 (Middle): Leave Requests */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: '#bbdefb', color: '#1565c0' }}>
            <h3>בקשת יציאה מהפנימייה</h3>
          </div>
          <div className="panel-content">
            <form style={{ display: 'flex', flexDirection: 'column', gap: '18px', height: '100%' }}>
              <div>
                <label style={labelStyle}>סוג יציאה</label>
                <select style={inputStyle}>
                  <option>יציאה זמנית (מספר שעות)</option>
                  <option>שבת הביתה</option>
                  <option>אירוע משפחתי</option>
                  <option>תור לרופא</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>תאריכים / שעות</label>
                <input type="text" placeholder="לדוגמה: היום מ-14:00 עד 18:00" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>הערות / סיבה</label>
                <input type="text" placeholder="פירוט לבקשה..." style={inputStyle} />
              </div>
              <button type="button" style={{ 
                padding: '14px', 
                borderRadius: '12px', 
                border: 'none', 
                fontWeight: '800', 
                fontSize: '1rem', 
                marginTop: 'auto', 
                cursor: 'pointer', 
                backgroundColor: '#bbdefb', 
                color: '#1565c0'
              }}>
                הגש בקשה לאישור
              </button>
            </form>
          </div>
        </div>

        {/* Column 3 (Left in RTL): Schedule & Exams */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          
          {/* Sub-panel 1: Schedule */}
          <div className="glass-panel" style={{ flex: 1 }}>
            <div className="panel-header" style={{ backgroundColor: '#ffe0b2', color: '#e65100' }}>
              <h3>מערכת שעות - היום</h3>
            </div>
            <div className="panel-content">
              {todaysSchedule.map(s => (
                <div key={s.id} style={{ 
                  backgroundColor: '#ffffff', 
                  borderRadius: '12px', 
                  padding: '12px 16px', 
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px'
                }}>
                  <div>
                    <div style={{ fontWeight: '800', fontSize: '1rem', color: '#e65100' }}>{s.subject}</div>
                    <div style={{ fontSize: '0.85rem', color: '#7f8c8d' }}>{s.teacher}</div>
                  </div>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: '700', fontSize: '0.9rem' }}>{s.period}</div>
                    <div style={{ fontSize: '0.8rem', color: '#7f8c8d' }}>{s.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sub-panel 2: Exams */}
          <div className="glass-panel" style={{ flex: 1 }}>
            <div className="panel-header" style={{ backgroundColor: '#e1bee7', color: '#6a1b9a' }}>
              <h3>המבחנים שלי</h3>
            </div>
            <div className="panel-content">
              {exams.map(e => (
                <div key={e.id} style={{ 
                  backgroundColor: '#ffffff', 
                  borderRadius: '12px', 
                  padding: '16px', 
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontWeight: '800', fontSize: '1.1rem', color: '#6a1b9a' }}>{e.subject}</div>
                  <div style={{ fontSize: '0.9rem', color: '#7f8c8d', marginTop: '8px' }}>{e.date}</div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

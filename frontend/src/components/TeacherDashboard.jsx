import React from 'react';
import './TeacherDashboard.css';

export default function TeacherDashboard() {
  // Mock data mimicking the provided image's structure
  const students = [
    { id: 1, name: "שירה כהן", grade: "90", color: "#f8bbd0" },
    { id: 2, name: "נועם לוי", grade: "85", color: "#bbdefb" },
    { id: 3, name: "טליה ישראלי", grade: "95", color: "#e1bee7" },
    { id: 4, name: "איתי שמש", grade: "100", color: "#ffcc80" }
  ];

  const leaves = [
    { id: 101, name: "בנימין ג.", dates: "י\"ח-י\"ט בחשוון | 29-30 אוקטובר", type: "שבת הביתה", status: "ממתין", color: "#b2dfdb" },
    { id: 102, name: "אליעזר ר.", dates: "כ\"א-כ\"ג בחשוון | 1-3 נובמבר", type: "אירוע משפחתי", status: "ממתין", color: "#e1bee7" }
  ];

  const exams = [
    { id: 201, subject: "מבחן בהיסטוריה", date: "י\"ט בחשוון | 30 אוקטובר, 09:00", class: "כיתה י'" },
    { id: 202, subject: "מבחן אמצע במתמטיקה", date: "כ\"ד בחשוון | 4 נובמבר, 11:30", class: "כיתה י\"א" },
    { id: 203, subject: "חיבור באנגלית", date: "כ\"ז בחשוון | 7 נובמבר, 14:00", class: "כיתה י' 1" }
  ];

  return (
    <div className="dashboard-wrapper">
      <div className="welcome-header">
        <h1>ברוך שובך! 🌿</h1>
        <p>היום יום שני, י"ז בחשוון | 28 באוקטובר</p>
      </div>

      <div className="dashboard-3col">
        {/* Column 1: Students */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-mint)' }}>
            <h3>התלמידים שלי</h3>
          </div>
          <div className="panel-content">
            {students.map(s => (
              <div key={s.id} className="pill-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                  <div className="avatar" style={{ backgroundColor: s.color }}>{s.name.charAt(0)}</div>
                  <span style={{ fontWeight: '600' }}>{s.name}</span>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-sub)' }}>ממוצע</div>
                  <div style={{ fontWeight: 'bold' }}>{s.grade}</div>
                </div>
              </div>
            ))}
            <div className="panel-footer">כל התלמידים (32)</div>
          </div>
        </div>

        {/* Column 2: Leaves */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-blue)' }}>
            <h3>בקשות יציאה</h3>
          </div>
          <div className="panel-content">
            {leaves.map(l => (
              <div key={l.id} className="pill-card leave-card">
                <div className="leave-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div className="avatar" style={{ backgroundColor: l.color }}>{l.name.charAt(0)}</div>
                    <div>
                      <div style={{ fontWeight: '700' }}>{l.name}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)' }}>תאריכי יציאה: {l.dates}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)' }}>{l.type}</div>
                    </div>
                  </div>
                  <div className="status-tag">{l.status}</div>
                </div>
                <div className="leave-actions">
                  <button className="btn-approve">אשר</button>
                  <button className="btn-reject">סרב</button>
                  <button className="btn-details">פרטים</button>
                </div>
              </div>
            ))}
            <div className="panel-footer">2 בקשות ממתינות</div>
          </div>
        </div>

        {/* Column 3: Exams */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-purple)' }}>
            <h3>מבחנים קרובים</h3>
          </div>
          <div className="panel-content">
            {exams.map(e => (
              <div key={e.id} className="pill-card exam-card">
                <div>
                  <div style={{ fontWeight: '700' }}>{e.subject}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)', marginTop: '4px' }}>{e.date}</div>
                </div>
                <div style={{ fontWeight: '600' }}>{e.class}</div>
              </div>
            ))}
            <div className="panel-footer">צפה בלוח המלא</div>
          </div>
        </div>

      </div>
    </div>
  );
}

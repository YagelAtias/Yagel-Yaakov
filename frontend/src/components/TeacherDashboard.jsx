import React, { useState, useEffect } from 'react';
import { secureFetch } from '../api';
import './TeacherDashboard.css';

export default function TeacherDashboard({ permissions = [] }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedStudentId, setExpandedStudentId] = useState(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const result = await secureFetch('/dashboard/teacher');
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) return <div style={{ padding: '50px', textAlign: 'center' }}>טוען נתונים...</div>;
  if (error) return <div style={{ padding: '50px', color: 'red' }}>שגיאה: {error}</div>;

  const { students = [], pending_dorm_leaves = [], upcoming_exams = [], user_name } = data || {};

  return (
    <div className="dashboard-wrapper">
      <div className="welcome-header">
        <h1>ברוך שובך, {user_name}! 🌿</h1>
        <p>הנה סיכום הפעילות והפניות של התלמידים שלך</p>
      </div>

      <div className="dashboard-3col">
        {/* Column 1: Students & Conversations */}
        <div className="glass-panel" style={{ gridColumn: 'span 2' }}>
          <div className="panel-header" style={{ backgroundColor: 'var(--col-mint)' }}>
            <h3>התלמידים שלי ושיחות (לפי כיתות)</h3>
          </div>
          <div className="panel-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {students.length === 0 ? <p>אין תלמידים משויכים אליך.</p> : null}
            {students.map(s => (
              <div 
                key={s.id} 
                className="pill-card" 
                style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '10px', cursor: 'pointer' }}
                onClick={() => setExpandedStudentId(expandedStudentId === s.id ? null : s.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', width: '100%' }}>
                  <div className="avatar" style={{ backgroundColor: '#b2dfdb' }}>{s.name.charAt(0)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '600' }}>{s.name}</span>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <span style={{
                          backgroundColor: s.current_location === "בפנימייה" ? '#e8f5e9' : '#fff3e0',
                          color: s.current_location === "בפנימייה" ? '#2e7d32' : '#e65100',
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '0.75rem',
                          fontWeight: 'bold'
                        }}>
                          {s.current_location === "בפנימייה" ? "📍 בפנימייה" : `🏠 ${s.current_location}`}
                        </span>
                        {s.risk_profile && (
                          <div style={{ display: 'flex', gap: '15px', fontSize: '0.75rem', backgroundColor: 'rgba(0,0,0,0.03)', padding: '6px 12px', borderRadius: '12px' }}>
                            <span title="Baseline median distress score">חציון מצוקה: {(s.risk_profile.blended_baseline * 10).toFixed(1)}</span>
                            <span title="Academic trend multiplier">מגמה לימודית: {(s.risk_profile.multiplier_applied).toFixed(2)}x</span>
                            <strong style={{ color: s.risk_profile.global_risk_score > 0.6 ? '#d32f2f' : '#2e7d32' }}>
                              {s.risk_profile.global_risk_score > 0.6 && "דורש התערבות - "}סיכון כולל: {(s.risk_profile.global_risk_score * 10).toFixed(1)}/10
                            </strong>
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)', marginTop: '4px' }}>{s.class_name}</div>
                  </div>
                </div>
                
                {expandedStudentId === s.id && (
                  <div style={{ width: '100%', marginTop: '10px', padding: '15px', backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: '12px', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)' }}>
                    
                    {s.active_leave && (
                      <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#fff3e0', borderRadius: '8px', borderRight: '4px solid #ff9800' }}>
                        <div style={{ fontWeight: 'bold', color: '#e65100', marginBottom: '5px' }}>פרטי חופשה פעילה:</div>
                        <div style={{ fontSize: '0.85rem', marginBottom: '2px' }}><strong>יעד:</strong> {s.active_leave.destination}</div>
                        <div style={{ fontSize: '0.85rem', marginBottom: '2px' }}><strong>סיבה:</strong> {s.active_leave.reason || "לא צוין"}</div>
                        <div style={{ fontSize: '0.85rem' }}><strong>חזרה משוערת:</strong> {new Date(s.active_leave.return_date).toLocaleString('he-IL')}</div>
                      </div>
                    )}
                    
                    <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '10px', color: '#455a64' }}>היסטוריית שיחות אחרונות:</div>
                    {s.recent_conversations && s.recent_conversations.length > 0 ? (
                    s.recent_conversations.map(conv => (
                      <div key={conv.id} style={{ display: 'flex', flexDirection: 'column', fontSize: '0.8rem', padding: '8px 0', borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                          <span>תאריך: {conv.date}</span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ color: '#555', fontWeight: 'bold' }}>ציון: {(conv.score * 10).toFixed(1)}/10</span>
                            {conv.has_critical_alert && <span style={{ color: 'red', fontWeight: 'bold' }}>דורש התערבות</span>}
                            {!conv.isDecrypted && (
                              <button 
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  try {
                                    const result = await secureFetch(`/logs/${conv.id}/decrypt`);
                                    const updatedStudents = [...data.students];
                                    const st = updatedStudents.find(st => st.id === s.id);
                                    const cv = st.recent_conversations.find(c => c.id === conv.id);
                                    cv.isDecrypted = true;
                                    cv.decryptedText = result.decrypted_text;
                                    setData({...data, students: updatedStudents});
                                  } catch (error) {
                                    alert("שגיאה בפענוח הנתונים");
                                  }
                                }}
                                style={{ padding: '4px 8px', fontSize: '0.7rem', backgroundColor: '#00695c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                              >
                                צפה בשיחה
                              </button>
                            )}
                          </div>
                        </div>
                        {conv.isDecrypted && (
                          <div style={{ backgroundColor: '#e0f2f1', padding: '8px', borderRadius: '4px', borderLeft: '3px solid #009688', marginTop: '4px' }}>
                            <span style={{ fontWeight: 'normal', color: '#333', fontFamily: 'inherit', whiteSpace: 'pre-wrap' }}>
                              {conv.decryptedText || 'הודעה ריקה'}
                            </span>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-sub)' }}>אין שיחות קודמות</div>
                  )}
                </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Column 2: Leaves (Privilege Based) */}
        {permissions.includes("can_manage_leaves") && (
          <div className="glass-panel">
            <div className="panel-header" style={{ backgroundColor: 'var(--col-blue)' }}>
              <h3>בקשות יציאה</h3>
            </div>
            <div className="panel-content">
              {pending_dorm_leaves.length === 0 ? <p>אין בקשות יציאה ממתינות.</p> : null}
              {pending_dorm_leaves.map(l => (
                <div key={l.leave_id} className="pill-card leave-card">
                  <div className="leave-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                      <div className="avatar" style={{ backgroundColor: '#e1bee7' }}>{l.student_name ? l.student_name.charAt(0) : 'ת'}</div>
                      <div>
                        <div style={{ fontWeight: '700' }}>{l.student_name || "תלמיד לא ידוע"} <span style={{fontWeight:'normal', color:'#666'}}>({l.leave_type})</span></div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)', marginTop: '6px' }}>
                          <div><strong>יציאה:</strong> {new Date(l.departure_date).toLocaleDateString('he-IL')} | <strong>חזרה:</strong> {new Date(l.return_date).toLocaleDateString('he-IL')}</div>
                          <div style={{ marginTop: '2px' }}><strong>יעד:</strong> {l.destination}</div>
                          {l.reason && <div style={{ marginTop: '2px' }}><strong>סיבה:</strong> {l.reason}</div>}
                        </div>
                      </div>
                    </div>
                    <div className="status-tag">ממתין</div>
                  </div>
                  <div className="leave-actions">
                    <button className="btn-approve" onClick={async () => {
                      try {
                        await secureFetch(`/leaves/${l.leave_id}/status`, {
                          method: 'PUT',
                          body: JSON.stringify({ status: "approved", is_approved: true })
                        });
                        alert('בקשת היציאה אושרה בהצלחה!');
                        setData(prev => ({...prev, pending_dorm_leaves: prev.pending_dorm_leaves.filter(pl => pl.leave_id !== l.leave_id)}));
                      } catch (err) {
                        alert("שגיאה באשור הבקשה: " + err.message);
                      }
                    }}>אשר</button>
                    <button className="btn-reject" onClick={async () => {
                      try {
                        await secureFetch(`/leaves/${l.leave_id}/status`, {
                          method: 'PUT',
                          body: JSON.stringify({ status: "rejected", is_approved: false })
                        });
                        alert('בקשת היציאה סורבה.');
                        setData(prev => ({...prev, pending_dorm_leaves: prev.pending_dorm_leaves.filter(pl => pl.leave_id !== l.leave_id)}));
                      } catch (err) {
                        alert("שגיאה בסרוב הבקשה: " + err.message);
                      }
                    }}>סרב</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Column 3: Exams */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-purple)' }}>
            <h3>מבחנים קרובים</h3>
          </div>
          <div className="panel-content">
            {upcoming_exams.length === 0 ? <p>אין מבחנים קרובים.</p> : null}
            {upcoming_exams.map(e => (
              <div key={e.exam_id} className="pill-card exam-card">
                <div>
                  <div style={{ fontWeight: '700' }}>{e.subject}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)', marginTop: '4px' }}>
                    {new Date(e.date_scheduled).toLocaleDateString('he-IL')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

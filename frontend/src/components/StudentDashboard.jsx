import React, { useState, useEffect } from 'react';
import { secureFetch } from '../api';
import './TeacherDashboard.css';

export default function StudentDashboard() {
  const [message, setMessage] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  
  const [leaveType, setLeaveType] = useState('יציאה זמנית (מספר שעות)');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('');
  const [destination, setDestination] = useState('');
  
  useEffect(() => {
    async function loadDashboard() {
      try {
        const result = await secureFetch('/dashboard/student');
        setData(result);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message || !data?.student_id) return;
    
    try {
      await secureFetch('/analyze_all', {
        method: 'POST',
        body: JSON.stringify({
          text: message,
          student_id: data.student_id,
          latencies: []
        })
      });
      alert('הודעתך נשלחה לאיש הצוות בהצלחה! (נותחה ברקע על ידי DistressEngine)');
      setMessage('');
    } catch (error) {
      alert('אירעה שגיאה בשליחת ההודעה.');
      console.error(error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };
      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');
        formData.append('student_id', data.student_id);
        
        try {
          await secureFetch('/analyze_audio', {
            method: 'POST',
            body: formData
          });
          alert('ההודעה הקולית נשלחה ונותחה בהצלחה! תודה ששיתפת.');
        } catch(e) {
          alert('שגיאה בשליחת ההודעה הקולית: ' + e.message);
        }
      };
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch(err) {
      alert("שגיאה בגישה למיקרופון: " + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  const handleSubmitLeave = async (e) => {
    e.preventDefault();
    if (!departureDate || !returnDate || !destination) {
      alert("אנא מלא את כל שדות החובה");
      return;
    }
    
    try {
      await secureFetch('/leaves/', {
        method: 'POST',
        body: JSON.stringify({
          leave_type: leaveType,
          reason: leaveReason,
          destination: destination,
          departure_date: new Date(departureDate).toISOString(),
          return_date: new Date(returnDate).toISOString()
        })
      });
      alert('בקשת היציאה נשלחה בהצלחה לאישור הצוות!');
      setDepartureDate('');
      setReturnDate('');
      setLeaveReason('');
      setDestination('');
    } catch (err) {
      alert('שגיאה בשליחת בקשת יציאה: ' + err.message);
    }
  };

  if (loading) return <div style={{ padding: '50px', textAlign: 'center' }}>טוען נתונים...</div>;

  const staff = data?.staff || [];
  const exams = data?.exams || [];

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
        <h1 style={{ color: '#ce93d8', fontSize: '2.8rem', fontWeight: '800', marginBottom: '5px' }}>שלום {data?.user_name}!</h1>
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
                  {staff.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.role})</option>
                  ))}
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
              <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
                <button type="button" onClick={isRecording ? stopRecording : startRecording} style={{ 
                  padding: '14px', 
                  borderRadius: '12px', 
                  border: 'none', 
                  fontWeight: '800', 
                  fontSize: '1rem', 
                  cursor: 'pointer', 
                  backgroundColor: isRecording ? '#ffcdd2' : '#e0f7fa', 
                  color: isRecording ? '#c62828' : '#00838f',
                  flex: 1
                }}>
                  {isRecording ? "⏹️ סיים ושלח הודעה קולית" : "🎙️ שלח הודעה קולית"}
                </button>
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
                  flex: 1
                }}>
                  שלח טקסט
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Column 2 (Middle): Leave Requests */}
        <div className="glass-panel">
          <div className="panel-header" style={{ backgroundColor: '#bbdefb', color: '#1565c0' }}>
            <h3>בקשת יציאה מהפנימייה</h3>
          </div>
          <div className="panel-content">
            <form onSubmit={handleSubmitLeave} style={{ display: 'flex', flexDirection: 'column', gap: '18px', height: '100%' }}>
              <div>
                <label style={labelStyle}>סוג יציאה</label>
                <select style={inputStyle} value={leaveType} onChange={e => setLeaveType(e.target.value)}>
                  <option>יציאה זמנית (מספר שעות)</option>
                  <option>שבת הביתה</option>
                  <option>אירוע משפחתי</option>
                  <option>תור לרופא</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>תאריך יציאה</label>
                  <input type="datetime-local" style={inputStyle} value={departureDate} onChange={e => setDepartureDate(e.target.value)} required />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>תאריך חזרה</label>
                  <input type="datetime-local" style={inputStyle} value={returnDate} onChange={e => setReturnDate(e.target.value)} required />
                </div>
              </div>
              <div>
                <label style={labelStyle}>יעד (לאן יוצא?)</label>
                <input type="text" placeholder="לדוגמה: הביתה לירושלים..." style={inputStyle} value={destination} onChange={e => setDestination(e.target.value)} required />
              </div>
              <div>
                <label style={labelStyle}>הערות / סיבה</label>
                <input type="text" placeholder="פירוט לבקשה..." style={inputStyle} value={leaveReason} onChange={e => setLeaveReason(e.target.value)} />
              </div>
              <button type="submit" style={{ 
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
              {exams.length === 0 ? <p>אין מבחנים קרובים.</p> : null}
              {exams.map(e => (
                <div key={e.id} style={{ 
                  backgroundColor: '#ffffff', 
                  borderRadius: '12px', 
                  padding: '16px', 
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  textAlign: 'center',
                  marginBottom: '10px'
                }}>
                  <div style={{ fontWeight: '800', fontSize: '1.1rem', color: '#6a1b9a' }}>{e.subject}</div>
                  <div style={{ fontSize: '0.9rem', color: '#7f8c8d', marginTop: '8px' }}>{new Date(e.date).toLocaleDateString('he-IL')}</div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

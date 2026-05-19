import React, { useState, useEffect } from 'react';
import { secureFetch } from '../api';
import { HDate } from '@hebcal/core';

export default function ArchiveModal({ studentId, studentName, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);

  useEffect(() => {
    async function loadArchive() {
      try {
        const result = await secureFetch(`/students/${studentId}/logs`);
        setLogs(result.logs);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadArchive();
  }, [studentId]);

  // Group logs by Hebrew year
  const groupedLogs = {};
  logs.forEach(log => {
    // The backend now provides an ISO string with 'Z'
    const dateObj = new Date(log.timestamp);
    const hDate = new HDate(dateObj);
    const hYear = hDate.renderGematriya().split(' ').pop(); // e.g. תשפ"ה
    const hYearLabel = `שנת ${hYear}`;
    
    if (!groupedLogs[hYearLabel]) {
      groupedLogs[hYearLabel] = [];
    }
    
    groupedLogs[hYearLabel].push({
      ...log,
      dateObj,
      hDate
    });
  });

  const years = Object.keys(groupedLogs).sort((a, b) => b.localeCompare(a)); // Sort descending
  const currentYear = selectedYear || (years.length > 0 ? years[0] : null);

  const renderFormattedText = (text) => {
    if (!text) return 'הודעה ריקה';
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} style={{ color: '#d32f2f' }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <span key={index} style={{ opacity: 0.6, fontStyle: 'italic' }}>{part.slice(1, -1)}</span>;
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: '#fff', padding: '20px', borderRadius: '12px', width: '90%', maxWidth: '800px',
        maxHeight: '90vh', display: 'flex', flexDirection: 'column', direction: 'rtl'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '2px solid #eee', paddingBottom: '10px' }}>
          <h2 style={{ margin: 0, color: '#2c3e50' }}>ארכיון שיחות - {studentName}</h2>
          <button onClick={onClose} style={{ cursor: 'pointer', background: 'none', border: 'none', fontSize: '1.5rem' }}>&times;</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>טוען ארכיון...</div>
        ) : error ? (
          <div style={{ color: 'red', textAlign: 'center', padding: '50px' }}>שגיאה: {error}</div>
        ) : years.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>אין שיחות בארכיון לתלמיד זה.</div>
        ) : (
          <div style={{ display: 'flex', gap: '20px', overflow: 'hidden', flex: 1 }}>
            {/* Sidebar for Years */}
            <div style={{ width: '150px', borderLeft: '1px solid #eee', paddingLeft: '10px', overflowY: 'auto' }}>
              <h4 style={{ marginTop: 0, color: '#455a64' }}>סינון לפי שנה</h4>
              {years.map(year => (
                <button
                  key={year}
                  onClick={() => setSelectedYear(year)}
                  style={{
                    display: 'block', width: '100%', padding: '10px', marginBottom: '5px',
                    textAlign: 'right', border: 'none', borderRadius: '6px', cursor: 'pointer',
                    backgroundColor: currentYear === year ? '#e0f7fa' : 'transparent',
                    fontWeight: currentYear === year ? 'bold' : 'normal',
                    color: currentYear === year ? '#00838f' : '#333',
                    transition: 'background-color 0.2s'
                  }}
                >
                  {year}
                </button>
              ))}
            </div>
            
            {/* Main Content for Logs */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '10px' }}>
              <h3 style={{ marginTop: 0, color: '#00838f' }}>שיחות: {currentYear}</h3>
              {groupedLogs[currentYear].map(log => (
                <div key={log.id} style={{ marginBottom: '15px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '8px', border: '1px solid #e0e0e0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.85rem', color: '#555', borderBottom: '1px solid #ddd', paddingBottom: '8px' }}>
                    <div style={{ lineHeight: '1.6' }}>
                      <span style={{ display: 'inline-block', width: '90px' }}><strong>תאריך עברי:</strong></span> {log.hDate.renderGematriya()}<br/>
                      <span style={{ display: 'inline-block', width: '90px' }}><strong>תאריך לועזי:</strong></span> {log.dateObj.toLocaleDateString('he-IL')}<br/>
                      <span style={{ display: 'inline-block', width: '90px' }}><strong>שעה:</strong></span> {log.dateObj.toLocaleTimeString('he-IL', {hour: '2-digit', minute: '2-digit'})}
                    </div>
                    <div style={{ textAlign: 'left', backgroundColor: '#fff', padding: '8px', borderRadius: '6px', border: '1px solid #eee' }}>
                      <div><strong>ציון מצוקה:</strong> <span style={{ color: log.overall_score > 0.8 ? '#d32f2f' : '#2e7d32' }}>{(log.overall_score * 10).toFixed(1)}/10</span></div>
                      {log.has_critical_alert && <div style={{ color: '#d32f2f', fontWeight: 'bold', marginTop: '4px' }}>⚠️ דורש התערבות!</div>}
                    </div>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.95rem', color: '#2c3e50', lineHeight: '1.5' }}>
                    {renderFormattedText(log.decrypted_text)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

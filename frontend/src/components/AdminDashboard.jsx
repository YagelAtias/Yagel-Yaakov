import React, { useState, useEffect } from 'react';
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

  // Staff and course state
  const [staffMembers, setStaffMembers] = useState([]);
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseMessage, setCourseMessage] = useState('');
  const [courseError, setCourseError] = useState('');

  // Student assignment modal
  const [showStudentModal, setShowStudentModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [allStudents, setAllStudents] = useState([]);
  const [courseStudents, setCourseStudents] = useState([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState([]);

  useEffect(() => {
    loadStaff();
    loadCourses();
    loadAllStudents();
  }, []);

  const loadStaff = async () => {
    try {
      const result = await secureFetch('/admin/staff');
      setStaffMembers(result.staff || []);
    } catch (err) {
      console.error('Failed to load staff:', err);
    }
  };

  const loadCourses = async () => {
    try {
      const result = await secureFetch('/courses');
      setCourses(result.courses || []);
    } catch (err) {
      console.error('Failed to load courses:', err);
    }
  };

  const loadAllStudents = async () => {
    try {
      const result = await secureFetch('/students');
      setAllStudents(result.students || []);
    } catch (err) {
      console.error('Failed to load students:', err);
    }
  };

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
      loadStaff(); // Refresh staff list
    } catch (err) {
      setError(err.message || 'אירעה שגיאה ביצירת החשבון');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCourseSubmit = async (e) => {
    e.preventDefault();
    setCourseError('');
    setCourseMessage('');

    if (!courseName.trim() || !selectedTeacherId) {
      setCourseError('נא למלא את כל השדות');
      return;
    }

    try {
      if (editingCourse) {
        await secureFetch(`/courses/${editingCourse.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            name: courseName,
            teacher_id: parseInt(selectedTeacherId)
          })
        });
        setCourseMessage('הכיתה עודכנה בהצלחה!');
      } else {
        await secureFetch('/courses', {
          method: 'POST',
          body: JSON.stringify({
            name: courseName,
            teacher_id: parseInt(selectedTeacherId)
          })
        });
        setCourseMessage('הכיתה נוצרה בהצלחה!');
      }

      setCourseName('');
      setSelectedTeacherId('');
      setEditingCourse(null);
      loadCourses();
    } catch (err) {
      setCourseError(err.message || 'אירעה שגיאה');
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את הכיתה?')) {
      return;
    }
    try {
      await secureFetch(`/courses/${courseId}`, {
        method: 'DELETE'
      });
      loadCourses();
      setCourseMessage('הכיתה נמחקה בהצלחה!');
    } catch (err) {
      setCourseError('שגיאה במחיקת הכיתה: ' + err.message);
    }
  };

  const startEditCourse = (course) => {
    setEditingCourse(course);
    setCourseName(course.name);
    setSelectedTeacherId(course.teacher_id || '');
  };

  const openStudentAssignmentModal = async (course) => {
    setSelectedCourse(course);
    setShowStudentModal(true);

    // Load current students in this course
    try {
      const result = await secureFetch(`/courses/${course.id}/students`);
      setCourseStudents(result.students || []);
      setSelectedStudentIds(result.students.map(s => s.id));
    } catch (err) {
      console.error('Failed to load course students:', err);
    }
  };

  const handleStudentAssignment = async () => {
    try {
      await secureFetch(`/courses/${selectedCourse.id}/students`, {
        method: 'POST',
        body: JSON.stringify({ student_ids: selectedStudentIds })
      });
      setShowStudentModal(false);
      alert('התלמידים שויכו בהצלחה!');
    } catch (err) {
      alert('שגיאה בשיוך התלמידים: ' + err.message);
    }
  };

  const toggleStudentSelection = (studentId) => {
    setSelectedStudentIds(prev => {
      if (prev.includes(studentId)) {
        return prev.filter(id => id !== studentId);
      } else {
        return [...prev, studentId];
      }
    });
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
            <h3>צוות חינוכי ({staffMembers.length})</h3>
          </div>
          <div className="panel-content">
            {staffMembers.length === 0 ? (
              <p>אין חברי צוות. השתמש בטופס כדי להוסיף איש צוות.</p>
            ) : (
              staffMembers.map(s => (
                <div key={s.id} className="pill-card staff-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div className="avatar" style={{ backgroundColor: s.role === 'admin' ? '#e1bee7' : s.role === 'counselor' ? '#b2dfdb' : '#ffcc80' }}>
                      {s.full_name.charAt(0)}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600' }}>{s.full_name}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)' }}>{s.role}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-sub)' }}>{s.email}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="admin-2col" style={{ marginTop: '20px' }}>
        {/* Course Creation Form */}
        <div className="glass-panel admin-form-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-mint)' }}>
            <h3>{editingCourse ? 'עריכת כיתה מקצועית' : 'הוספת כיתה מקצועית חדשה'}</h3>
          </div>
          <div className="panel-content">
            <form onSubmit={handleCourseSubmit} className="onboard-form">
              <div className="form-group">
                <label>שם הכיתה / קבוצה</label>
                <input
                  type="text"
                  value={courseName}
                  onChange={(e) => setCourseName(e.target.value)}
                  placeholder='לדוגמה: "מתמטיקה 4 יח״ל - קבוצה א"'
                  required
                />
              </div>
              <div className="form-group">
                <label>שיוך מורה</label>
                <select
                  value={selectedTeacherId}
                  onChange={(e) => setSelectedTeacherId(e.target.value)}
                  required
                >
                  <option value="">-- בחר מורה --</option>
                  {staffMembers.filter(s => s.role === 'teacher' || s.role === 'counselor' || s.role === 'admin').map(s => (
                    <option key={s.id} value={s.id}>{s.full_name} ({s.role})</option>
                  ))}
                </select>
              </div>

              {courseError && <div className="admin-error">{courseError}</div>}
              {courseMessage && <div className="admin-success">{courseMessage}</div>}

              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="btn-submit-staff" style={{ backgroundColor: 'var(--col-mint)' }}>
                  {editingCourse ? 'עדכן כיתה' : 'צור כיתה'}
                </button>
                {editingCourse && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingCourse(null);
                      setCourseName('');
                      setSelectedTeacherId('');
                      setCourseError('');
                      setCourseMessage('');
                    }}
                    className="btn-submit-staff"
                    style={{ backgroundColor: '#999' }}
                  >
                    ביטול
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        <div className="glass-panel staff-list-panel">
          <div className="panel-header" style={{ backgroundColor: 'var(--col-blue)' }}>
            <h3>כיתות מקצועיות קיימות ({courses.length})</h3>
          </div>
          <div className="panel-content">
            {courses.length === 0 ? (
              <p>אין כיתות מקצועיות. השתמש בטופס כדי ליצור כיתה ראשונה.</p>
            ) : (
              courses.map(c => {
                const teacher = staffMembers.find(s => s.id === c.teacher_id);
                return (
                  <div key={c.id} className="pill-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: '600' }}>{c.name}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-sub)' }}>
                        מורה: {teacher ? teacher.full_name : 'לא משויך'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                        onClick={() => openStudentAssignmentModal(c)}
                        style={{
                          padding: '6px 12px',
                          fontSize: '0.8rem',
                          backgroundColor: '#2196f3',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        ניהול תלמידים
                      </button>
                      <button
                        onClick={() => startEditCourse(c)}
                        style={{
                          padding: '6px 12px',
                          fontSize: '0.8rem',
                          backgroundColor: '#4caf50',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        ערוך
                      </button>
                      <button
                        onClick={() => handleDeleteCourse(c.id)}
                        style={{
                          padding: '6px 12px',
                          fontSize: '0.8rem',
                          backgroundColor: '#f44336',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        מחק
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Student Assignment Modal */}
      {showStudentModal && selectedCourse && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '12px',
            minWidth: '500px',
            maxHeight: '80vh',
            overflow: 'auto',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
          }}>
            <h3 style={{ marginBottom: '20px', textAlign: 'center' }}>
              ניהול תלמידים - {selectedCourse.name}
            </h3>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '10px' }}>
                סמן את התלמידים שישויכו לכיתה זו:
              </p>
              <div style={{ maxHeight: '400px', overflow: 'auto', border: '1px solid #ddd', borderRadius: '6px', padding: '10px' }}>
                {allStudents.length === 0 ? (
                  <p>אין תלמידים במערכת. צור תלמידים קודם.</p>
                ) : (
                  allStudents.map(student => (
                    <div key={student.id} style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '8px',
                      borderBottom: '1px solid #f0f0f0',
                      cursor: 'pointer',
                      backgroundColor: selectedStudentIds.includes(student.id) ? '#e3f2fd' : 'transparent'
                    }}
                    onClick={() => toggleStudentSelection(student.id)}
                    >
                      <input
                        type="checkbox"
                        checked={selectedStudentIds.includes(student.id)}
                        onChange={() => toggleStudentSelection(student.id)}
                        style={{ marginLeft: '10px', cursor: 'pointer' }}
                      />
                      <div>
                        <div style={{ fontWeight: '600' }}>
                          {student.first_name} {student.last_name}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#666' }}>
                          {student.email} • {student.grade_level}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowStudentModal(false);
                  setSelectedCourse(null);
                  setSelectedStudentIds([]);
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#f5f5f5',
                  color: '#333',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                ביטול
              </button>
              <button
                onClick={handleStudentAssignment}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#2196f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                שמור שיוך ({selectedStudentIds.length} תלמידים)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

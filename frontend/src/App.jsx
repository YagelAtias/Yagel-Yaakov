import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDashboard from './components/StudentDashboard';
import LoginScreen from './components/LoginScreen';
import AdminDashboard from './components/AdminDashboard';
import './App.css';

function App() {
  const [userRole, setUserRole] = useState(localStorage.getItem('user_role') || null);
  const [activeTab, setActiveTab] = useState('ראשי');
  const logoutTimer = useRef(null);

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user_role');
    setUserRole(null);
  };

  // Auto-logout after 15 minutes of inactivity
  useEffect(() => {
    if (!userRole) return;

    const resetTimer = () => {
      if (logoutTimer.current) clearTimeout(logoutTimer.current);
      // 15 minutes = 15 * 60 * 1000 ms = 900000
      logoutTimer.current = setTimeout(() => {
        handleLogout();
        alert("נותקת מהמערכת עקב חוסר פעילות מטעמי אבטחה.");
      }, 900000);
    };

    const events = ['mousemove', 'keydown', 'mousedown', 'touchstart', 'scroll'];
    events.forEach(event => window.addEventListener(event, resetTimer));
    
    // Initial start
    resetTimer();

    return () => {
      if (logoutTimer.current) clearTimeout(logoutTimer.current);
      events.forEach(event => window.removeEventListener(event, resetTimer));
    };
  }, [userRole]);

  // If not logged in, show the Login Screen!
  if (!userRole) {
    return <LoginScreen onLogin={(role) => {
      localStorage.setItem('user_role', role);
      setUserRole(role);
    }} />;
  }

  // Determine what to render based on activeTab and role
  let Content;
  if (userRole === 'student') {
    Content = <StudentDashboard />;
  } else {
    // Staff / Admin routing
    if (activeTab === 'ניהול' && userRole === 'admin') {
      Content = <AdminDashboard />;
    } else {
      // Default to TeacherDashboard for 'ראשי' or other tabs if not implemented
      Content = <TeacherDashboard />;
    }
  }

  // If logged in, show the appropriate Dashboard
  return (
    <div className="app-root">
      <Navbar role={userRole} activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} />
      {Content}
    </div>
  );
}

export default App;
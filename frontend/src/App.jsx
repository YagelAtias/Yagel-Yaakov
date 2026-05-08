import React, { useState } from 'react';
import Navbar from './components/Navbar';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDashboard from './components/StudentDashboard';
import LoginScreen from './components/LoginScreen';
import './App.css';

function App() {
  const [userRole, setUserRole] = useState(null);

  // If not logged in, show the Login Screen!
  if (!userRole) {
    return <LoginScreen onLogin={(role) => setUserRole(role)} />;
  }

  // If logged in, show the appropriate Dashboard
  return (
    <div className="app-root">
      <Navbar role={userRole} />
      {userRole === 'teacher' ? <TeacherDashboard /> : <StudentDashboard />}
    </div>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { AdminPanel, AdminLogin } from './features/admin';
import { useAdminAuth } from './features/admin/hooks/useAdminAuth';
import './App.css';

function App() {
  const { isAdmin, adminId, loading } = useAdminAuth();
  const [currentAdminId, setCurrentAdminId] = useState<number | null>(null);

  useEffect(() => {
    if (isAdmin && adminId) {
      setCurrentAdminId(adminId);
    }
  }, [isAdmin, adminId]);

  const handleLogin = (userId: number) => {
    setCurrentAdminId(userId);
  };

  const handleLogout = () => {
    localStorage.removeItem('current_user_id');
    setCurrentAdminId(null);
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Проверка прав доступа...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {currentAdminId ? (
        <>
          <div className="admin-header">
            <h1>🤖 Панель управления записями</h1>
            <button onClick={handleLogout} className="logout-btn">
              🔓 Выйти
            </button>
          </div>
          <AdminPanel adminId={currentAdminId} />
        </>
      ) : (
        <AdminLogin onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;

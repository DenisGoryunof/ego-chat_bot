
import React, { useState } from 'react';
import './AdminLogin.css';

interface AdminLoginProps {
  onLogin: (userId: number) => void;
}

const AdminLogin: React.FC<AdminLoginProps> = ({ onLogin }) => {
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');
  const [showInstructions, setShowInstructions] = useState(false);

  const handleLogin = () => {
    const id = parseInt(userId);
    if (isNaN(id)) {
      setError('Введите корректный ID пользователя');
      return;
    }

    localStorage.setItem('current_user_id', id.toString());
    onLogin(id);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleLogin();
  };

  return (
    <div className="admin-login">
      <div className="login-container">
        <div className="login-header">
          <h1>🤖 Панель администратора</h1>
          <h2>🔐 Вход в систему управления</h2>
        </div>
        
        <div className="login-card">
          <p className="login-description">
            Для доступа к панели администратора введите ваш User ID.
          </p>

          {error && <div className="login-error">{error}</div>}

          <div className="input-group">
            <label>🆔 User ID администратора:</label>
            <input
              type="number"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value);
                setError('');
              }}
              onKeyPress={handleKeyPress}
              placeholder="Введите ваш цифровой ID"
              className="user-id-input"
            />
          </div>

          <button onClick={handleLogin} className="login-btn">
            🔒 Войти в панель администратора
          </button>

          <div className="instructions-toggle">
            <button onClick={() => setShowInstructions(!showInstructions)} className="toggle-btn">
              {showInstructions ? '▲ Скрыть инструкции' : '▼ Как получить доступ?'}
            </button>
          </div>

          {showInstructions && (
            <div className="login-info">
              <h3>📋 Инструкция по получению доступа</h3>
              
              <div className="instruction-step">
                <h4>1. 📱 Получите ваш User ID в Telegram</h4>
                <p>Откройте Telegram и найдите бота <strong>@userinfobot</strong></p>
              </div>

              <div className="instruction-step">
                <h4>2. 🔐 Проверьте права доступа</h4>
                <p>Обратитесь к главному администратору для добавления вашего User ID</p>
              </div>

              <div className="instruction-step">
                <h4>3. 🎯 Войдите в систему</h4>
                <p>Введите ваш User ID в поле выше и нажмите "Войти"</p>
              </div>
            </div>
          )}

          <div className="quick-test">
            <h4>🧪 Тестовый доступ</h4>
            <div className="test-buttons">
              <button onClick={() => setUserId('1373071419')} className="test-btn">
                💅 Маникюр (1373071419)
              </button>
              <button onClick={() => setUserId('1094720117')} className="test-btn">
                ✨ Другие услуги (1094720117)
              </button>
              <button onClick={() => setUserId('130208292')} className="test-btn">
                👑 Главный (130208292)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;

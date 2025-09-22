
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { initializeMockData } from './utils/mockData';

// Инициализируем тестовые данные
initializeMockData().catch(console.error);

const container = document.getElementById('app');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// Экспортируем для доступа из консоли
(window as any).addTestData = initializeMockData;

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import WebApp from '@twa-dev/sdk'

// ==========================================
// EIDOS OS V2: INIT SEQUENCE
// ==========================================

// Конфигурация темы и TWA UI
try {
  if (WebApp.initData) {
    WebApp.expand();
    WebApp.ready();
    WebApp.disableVerticalSwipes();
    WebApp.setHeaderColor('#020304');
    WebApp.setBackgroundColor('#020304');
  } else {
    console.warn("/// CRITICAL: TWA Environment not detected. Injecting MOCK initData. ///");
  }
} catch (e) {
  console.warn("TWA Init failed:", e);
}

// Переопределяем WebApp для локальной среды
if (!window.Telegram?.WebApp?.initData) {
  const mockUser = encodeURIComponent(JSON.stringify({
    id: 123456789,
    first_name: "DevUser",
    last_name: "Mock",
    username: "dev_mock",
    language_code: "ru"
  }));
  const mockInitData = `query_id=mock123&user=${mockUser}&auth_date=${Math.floor(Date.now() / 1000)}&hash=devmock`;

  if (!window.Telegram) window.Telegram = {};
  window.Telegram.WebApp = {
    ...WebApp,
    initData: mockInitData,
    initDataUnsafe: {
      user: {
        id: 123456789,
        first_name: "DevUser",
        last_name: "Mock",
        username: "dev_mock",
        language_code: "ru"
      }
    }
  };
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

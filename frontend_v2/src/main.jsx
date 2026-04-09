import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// ==========================================
// EIDOS OS V2: INIT SEQUENCE
// ==========================================

// Конфигурация темы и TWA UI
try {
  if (window.Telegram?.WebApp?.initData) {
    window.Telegram?.WebApp?.expand();
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.disableVerticalSwipes();
    window.Telegram?.WebApp?.setHeaderColor('#020304');
    window.Telegram?.WebApp?.setBackgroundColor('#020304');
  } else {
    console.warn("/// CRITICAL: TWA Environment not detected. Injecting MOCK initData. ///");
  }
} catch (e) {
  console.warn("TWA Init failed:", e);
}



ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import WebApp from '@twa-dev/sdk'
import useStore from './store/useStore'

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



ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

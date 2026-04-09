import axios from 'axios';

// ==========================================
// EIDOS CORE V2 - Изолированный сетевой клиент
// ==========================================

export const eidosApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Глобальный перехватчик запросов
eidosApi.interceptors.request.use(
  (config) => {
    // Получаем строку initData из Telegram SDK.

    const initData = window.Telegram?.WebApp?.initData;

    if (initData) {
      config.headers['X-Telegram-Init-Data'] = initData;
    }

    // Для предотвращения кэширования AJAX-запросов (браузером на мобильных)
    config.params = { ...config.params, _t: new Date().getTime() };
    config.metadata = { startTime: new Date() };

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Глобальный перехватчик ответов
eidosApi.interceptors.response.use(
  (response) => {
    if (response.config.metadata) {
      const duration = new Date() - response.config.metadata.startTime;
      if (duration > 800) {
        import("../store/useStore").then(m => {
          m.default.getState().setGlitch(true);
          setTimeout(() => m.default.getState().setGlitch(false), 800);
        });
      }
    }
    return response.data;
  },
  (error) => {
    // В случае ошибок логгируем их в нашем стиле терминала EIDOS
    console.error('/// NETWORK ERROR ///', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

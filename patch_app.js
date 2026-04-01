const fs = require('fs');
const file = 'frontend_v2/src/App.jsx';
let content = fs.readFileSync(file, 'utf8');

const syncLogic = `
  useEffect(() => {
    const sendSyncSignal = () => {
      let uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
      if (uid) {
        const url = \`\${import.meta.env.VITE_API_URL || '/api'}/twa/sync\`;

        // Use sendBeacon for reliable delivery during page unload
        const data = JSON.stringify({ uid });
        const blob = new Blob([data], { type: 'application/json' });
        navigator.sendBeacon(url, blob);
      }
    };

    // Listen for page hide/unload to trigger sync
    window.addEventListener('pagehide', sendSyncSignal);
    window.addEventListener('beforeunload', sendSyncSignal);

    // Override WebApp close to send signal before closing
    if (window.Telegram?.WebApp) {
      const originalClose = window.Telegram.WebApp.close.bind(window.Telegram.WebApp);
      window.Telegram.WebApp.close = () => {
        sendSyncSignal();
        originalClose();
      };
    }

    return () => {
      window.removeEventListener('pagehide', sendSyncSignal);
      window.removeEventListener('beforeunload', sendSyncSignal);
    };
  }, []);
`;

const splitContent = content.split('  useEffect(() => {');
const newContent = splitContent[0] + syncLogic + '  useEffect(() => {' + splitContent[1] + '  useEffect(() => {' + splitContent[2];

fs.writeFileSync(file, newContent);
console.log("Patched App.jsx");

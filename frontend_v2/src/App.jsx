import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import useStore from './store/useStore';

// Components
import Layout from './components/Layout';
import IntroVideo from './components/IntroVideo';
import Hub from './pages/Hub';
import Inventory from './pages/Inventory';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5,
    },
  },
});

const Placeholder = ({ name }) => (
  <div className="flex flex-col items-center justify-center h-full text-center">
    <h2 className="text-2xl font-orbitron text-[var(--color-eidos-cyan)] mb-4 animate-pulse uppercase">
      {name} // OFFLINE
    </h2>
    <p className="font-share text-white/50 border border-white/20 p-4 clip-hex bg-black/50 uppercase">
      MODULE OFFLINE
    </p>
  </div>
);

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-[var(--color-eidos-bg)] text-[var(--color-eidos-red)] p-4 text-center clip-hex">
      <h2 className="text-xl font-bold font-orbitron mb-4 border-b border-[var(--color-eidos-red)] pb-2 text-glow-red">
        /// CRITICAL SYSTEM FAILURE ///
      </h2>
      <pre className="text-xs font-share bg-black/50 p-4 rounded text-left overflow-auto w-full max-w-md border border-[var(--color-eidos-red)] shadow-[0_0_15px_rgba(255,51,51,0.2)]">
        {error.message}
        <br />
        {error.stack}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-6 px-6 py-2 bg-[var(--color-eidos-red)]/20 border border-[var(--color-eidos-red)] font-orbitron hover:bg-[var(--color-eidos-red)]/40 transition-colors text-glow-red"
      >
        REBOOT SYSTEM
      </button>
    </div>
  );
}

function App() {
  const isLoading = useStore((state) => state.isLoading);
  const profile = useStore((state) => state.profile);
  const [currentView, setCurrentView] = useState('INTRO');

  useEffect(() => {
    console.log("/// EIDOS: Starting initialization sequence...");

    let uid = null;
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe) {
        uid = window.Telegram.WebApp.initDataUnsafe.user?.id;
    }

    if (!uid) {
        try {
            const hash = window.location.hash.substring(1);
            const params = new URLSearchParams(hash);
            const tgWebAppData = params.get('tgWebAppData');
            if (tgWebAppData) {
                const tgParams = new URLSearchParams(tgWebAppData);
                const userStr = tgParams.get('user');
                if (userStr) {
                    const userObj = JSON.parse(decodeURIComponent(userStr));
                    uid = userObj.id;
                }
            }
        } catch (e) {
            console.error("/// EIDOS: Hash parsing failed", e);
        }
    }

    if (!uid) {
        uid = new URLSearchParams(window.location.search).get('uid');
    }

    if (uid) {
        useStore.getState().fetchProfile(uid);
    } else {
        console.error("/// EIDOS FATAL: Could not determine UID from any source.");
    }
  }, []);

  useEffect(() => {
    // Manage Telegram BackButton visibility based on currentView
    const twa = window.Telegram?.WebApp;
    if (twa && twa.BackButton) {
      if (currentView !== 'HUB' && currentView !== 'INTRO') {
        twa.BackButton.show();
        twa.BackButton.onClick(() => {
          setCurrentView('HUB');
        });
      } else {
        twa.BackButton.hide();
      }
    }

    return () => {
        if (twa && twa.BackButton) {
            twa.BackButton.offClick();
        }
    }
  }, [currentView]);

  if (currentView === 'INTRO') {
    return <IntroVideo onComplete={() => setCurrentView('HUB')} />;
  }

  if (isLoading || !profile) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--color-eidos-bg)]">
        <div className="loading-screen text-center font-orbitron text-eidos-cyan text-xl animate-pulse text-glow-cyan">
          ESTABLISHING NEURAL LINK...
        </div>
      </div>
    );
  }

  const renderView = () => {
    switch (currentView) {
      case 'HUB':
        return <Hub setView={setCurrentView} />;
      case 'INVENTORY':
        return <Inventory />;
      default:
        return <Placeholder name={currentView} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Layout>
          {renderView()}
          {/* GLOBAL UI FRAME (Hidden on Start/Loading screen) */}
          {currentView !== 'INTRO' && currentView !== 'LOADING' && (
            <img
              src="/video/frame.png"
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                objectFit: 'fill',
                zIndex: 9999,
                pointerEvents: 'none'
              }}
              alt="UI Frame"
            />
          )}
        </Layout>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;

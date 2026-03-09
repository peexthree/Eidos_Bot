import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { Route, Switch } from 'wouter';

// Импорт компонентов
import Layout from './components/Layout';
import Nexus from './pages/Nexus';
import Inventory from './pages/Inventory';

// Инстанс для кэша и серверного состояния
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 минут
    },
  },
});

// Заглушка для ненайденных маршрутов или заглушек страниц
const Placeholder = ({ name }) => (
  <div className="flex flex-col items-center justify-center h-full text-center">
    <h2 className="text-2xl font-orbitron text-[var(--color-eidos-cyan)] mb-4 animate-pulse">
      {name} // ONLINE
    </h2>
    <p className="font-share text-white/50 border border-white/20 p-4 clip-hex bg-black/50">
      SYSTEM MODULE IN DEVELOPMENT...
    </p>
  </div>
);

// Custom Error Fallback Components (Терминал сбоя)
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
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        {/* Обертываем приложение главным слоем интерфейса */}
        <Layout>
          {/* Маршрутизация Wouter */}
          <Switch>
            {/* Главный хаб */}
            <Route path="/" component={Nexus} />

            {/* Модуль Инвентаря */}
            <Route path="/inventory" component={Inventory} />

            {/* Заглушки для основных модулей */}
            <Route path="/profile">
              <Placeholder name="PROFILE MODULE" />
            </Route>
            <Route path="/shop">
              <Placeholder name="MARKET MODULE" />
            </Route>
            <Route path="/arena">
              <Placeholder name="ARENA MODULE" />
            </Route>
            <Route path="/raids">
              <Placeholder name="RAIDS MODULE" />
            </Route>

            {/* Fallback маршрут (404) */}
            <Route>
              <div className="flex flex-col items-center justify-center h-full text-center">
                <h2 className="text-2xl font-orbitron text-[var(--color-eidos-red)] text-glow-red mb-4">
                  404 // MODULE NOT FOUND
                </h2>
                <p className="font-share text-white/50 border border-[var(--color-eidos-red)]/50 p-4 clip-hex bg-black/50">
                  INVALID ADDRESS MEMORY REGION
                </p>
              </div>
            </Route>
          </Switch>
        </Layout>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;

import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'

// Инстанс для кэша и серверного состояния
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 минут
    },
  },
})

// Custom Error Fallback Components (Терминал сбоя)
function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-[#020304] text-[#ff3333] p-4 text-center clip-hex">
      <h2 className="text-xl font-bold font-orbitron mb-4 border-b border-[#ff3333] pb-2 text-glow-red">
        /// CRITICAL SYSTEM FAILURE ///
      </h2>
      <pre className="text-xs font-share bg-black/50 p-4 rounded text-left overflow-auto w-full max-w-md border border-[#ff3333] shadow-[0_0_15px_rgba(255,51,51,0.2)]">
        {error.message}
        <br />
        {error.stack}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-6 px-6 py-2 bg-[#ff3333]/20 border border-[#ff3333] font-orbitron hover:bg-[#ff3333]/40 transition-colors text-glow-red"
      >
        REBOOT SYSTEM
      </button>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        {/* Главная обертка с glassmorphism и ограничителем скролла */}
        <div className="flex flex-col h-screen overflow-hidden bg-[#020304] text-white">
          <main className="flex-1 overflow-y-auto scroll-area flex items-center justify-center p-4 pt-[var(--spacing-safe-top)] pb-[var(--spacing-safe-bottom)] relative">

            {/* Анимация/Текст загрузки ядра */}
            <div className="text-center z-10 bg-glass p-8 rounded-sm clip-hex border border-[#00ff41]/30 shadow-[0_0_20px_rgba(0,255,65,0.1)]">
               <h1 className="text-3xl font-orbitron text-[#00ff41] text-glow-neon mb-2">
                 EIDOS CORE V2 ONLINE
               </h1>
               <p className="font-share text-[#66FCF1]/70 text-sm tracking-widest text-glow-cyan animate-pulse">
                 AWAITING SYSTEM INSTRUCTIONS...
               </p>
            </div>

            {/* Эффект scanlines на фоне (CSS-решение) */}
            <div className="absolute inset-0 pointer-events-none opacity-5 mix-blend-overlay" style={{ backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 1px, #fff 1px, #fff 2px)", backgroundSize: "100% 2px" }}></div>
          </main>
        </div>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App

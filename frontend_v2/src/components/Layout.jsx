import React from 'react';

export default function Layout({ children }) {
  return (
    <div className="flex flex-col h-[100dvh] overflow-hidden overscroll-none bg-[var(--color-eidos-bg)] text-white relative">
      {/*
        Фоновый эффект кибер-частиц (Nexus Grid).
        Используется абсолютное позиционирование с z-index: -1 и pointer-events: none,
        чтобы не блокировать взаимодействие с UI.
      */}
      <div
        className="absolute inset-0 z-[-1] pointer-events-none opacity-10 mix-blend-screen"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 19px, var(--color-eidos-cyan) 20px), repeating-linear-gradient(90deg, transparent, transparent 19px, var(--color-eidos-cyan) 20px)",
          backgroundSize: "20px 20px"
        }}
      />

      {/*
        Контейнер контента.
        Учитываем безопасные зоны iOS: pt-[env(safe-area-inset-top)].
        Класс scroll-area ограничивает скролл, предотвращая rubber-banding (bounce) на мобильных.
      */}
      <main className="flex-1 overflow-y-auto scroll-area w-full h-full relative z-[1] pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] flex flex-col items-center">
        <div className="w-full max-w-2xl px-4 py-6">
          {children}
        </div>
      </main>

      {/*
        Глобальный overlay-эффект Scanlines.
        Добавляет легкую ретро/кибер эстетику поверх всего интерфейса (z-index выше контента, но pointer-events-none).
      */}
      <div
        className="absolute inset-0 z-[100] pointer-events-none opacity-5 mix-blend-overlay sys-scanline"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 1px, #fff 1px, #fff 2px)",
          backgroundSize: "100% 2px"
        }}
      />
    </div>
  );
}

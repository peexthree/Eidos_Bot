import React, { useState, useEffect, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';
import WebApp from '@twa-dev/sdk';

const HoldToEquip = ({ onEquip }) => {
  const [isHolding, setIsHolding] = useState(false);
  const controls = useAnimation();
  const holdTimer = useRef(null);
  const hapticTimer = useRef(null);

  const HOLD_DURATION = 1500; // 1.5 секунды для экипировки
  const HAPTIC_INTERVAL = 150; // Интервал тактильной отдачи при удержании

  const startHold = () => {
    setIsHolding(true);
    controls.start({
      pathLength: 1,
      transition: { duration: HOLD_DURATION / 1000, ease: 'linear' }
    });

    // Легкая вибрация при начале
    WebApp.HapticFeedback.impactOccurred('light');

    // Периодическая вибрация во время удержания
    hapticTimer.current = setInterval(() => {
      WebApp.HapticFeedback.selectionChanged();
    }, HAPTIC_INTERVAL);

    // Таймер окончания удержания
    holdTimer.current = setTimeout(() => {
      clearInterval(hapticTimer.current);
      WebApp.HapticFeedback.impactOccurred('heavy'); // Сильная вибрация при успехе
      onEquip();
      setIsHolding(false);
    }, HOLD_DURATION);
  };

  const cancelHold = () => {
    if (isHolding) {
      setIsHolding(false);
      controls.stop();
      controls.set({ pathLength: 0 });
      clearTimeout(holdTimer.current);
      clearInterval(hapticTimer.current);
    }
  };

  useEffect(() => {
    return () => {
      clearTimeout(holdTimer.current);
      clearInterval(hapticTimer.current);
    };
  }, []);

  return (
    <div className="relative w-full flex justify-center items-center">
      {/* Кнопка */}
      <motion.button
        onPointerDown={startHold}
        onPointerUp={cancelHold}
        onPointerLeave={cancelHold}
        onContextMenu={(e) => e.preventDefault()} // Отключаем контекстное меню на мобилках
        whileTap={{ scale: 0.95 }}
        className={`relative z-10 px-8 py-4 bg-black/60 backdrop-blur-md border border-eidos-cyan/30 text-eidos-cyan font-orbitron uppercase tracking-widest text-lg overflow-hidden transition-colors ${
          isHolding ? 'bg-eidos-cyan/10' : ''
        }`}
        style={{
          clipPath: 'polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px)'
        }}
      >
        <span className="relative z-10">Экипировать</span>

        {/* Индикатор прогресса на фоне */}
        <motion.div
          initial={{ width: '0%' }}
          animate={{ width: isHolding ? '100%' : '0%' }}
          transition={{ duration: isHolding ? HOLD_DURATION / 1000 : 0.2, ease: 'linear' }}
          className="absolute left-0 top-0 bottom-0 bg-eidos-cyan/20 z-0"
        />
      </motion.button>

      {/* SVG кольцо прогресса (Neural Overcharge) */}
      <div className="absolute inset-0 pointer-events-none flex justify-center items-center">
        <svg width="180" height="80" viewBox="0 0 180 80" className="absolute -z-10 opacity-50">
          {/* Фоновое кольцо */}
          <path
            d="M 15 5 L 165 5 L 175 15 L 175 65 L 165 75 L 15 75 L 5 65 L 5 15 Z"
            fill="none"
            stroke="rgba(102, 252, 241, 0.1)"
            strokeWidth="2"
          />
          {/* Анимированное кольцо прогресса */}
          <motion.path
            d="M 15 5 L 165 5 L 175 15 L 175 65 L 165 75 L 15 75 L 5 65 L 5 15 Z"
            fill="none"
            stroke="#66FCF1"
            strokeWidth="2"
            initial={{ pathLength: 0 }}
            animate={controls}
            style={{
              filter: 'drop-shadow(0 0 8px rgba(102, 252, 241, 0.8))'
            }}
          />
        </svg>
      </div>

      {/* Текст-подсказка */}
      <div className="absolute -bottom-6 text-xs text-white/40 font-share-tech uppercase tracking-widest">
        Удерживайте
      </div>
    </div>
  );
};

export default HoldToEquip;

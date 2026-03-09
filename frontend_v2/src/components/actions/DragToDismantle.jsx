import React, { useRef } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import WebApp from '@twa-dev/sdk';

const DragToDismantle = ({ onDismantle }) => {
  const y = useMotionValue(0);
  const containerRef = useRef(null);

  // Трансформация цвета и прозрачности в зависимости от свайпа (0 до 100px)
  const opacity = useTransform(y, [0, 80], [1, 0.5]);
  const scale = useTransform(y, [0, 80], [1, 0.9]);
  const background = useTransform(y, [0, 80], ['rgba(0, 0, 0, 0.6)', 'rgba(255, 51, 51, 0.4)']); // eidos-red
  const borderColor = useTransform(y, [0, 80], ['rgba(255, 51, 51, 0.3)', 'rgba(255, 51, 51, 1)']);

  const handleDragEnd = (event, info) => {
    const offset = info.offset.y;
    const velocity = info.velocity.y;

    // Порог срабатывания: сдвиг больше 60px или быстрый свайп вниз
    if (offset > 60 || velocity > 500) {
      WebApp.HapticFeedback.impactOccurred('heavy'); // Сильная вибрация при разборе
      onDismantle();
    } else {
      // Возврат на место
      WebApp.HapticFeedback.impactOccurred('light');
    }
  };

  const handleDrag = () => {
    // Легкая вибрация при перетягивании
    if (y.get() > 30) {
      WebApp.HapticFeedback.selectionChanged();
    }
  };

  return (
    <div
      className="relative w-full h-24 flex flex-col justify-end items-center overflow-hidden border border-white/5 bg-black/40 backdrop-blur-md rounded-b-lg mt-4"
      ref={containerRef}
      style={{
        clipPath: 'polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%)'
      }}
    >
      {/* Фон "Matter Grinder" (Шредер) */}
      <div className="absolute inset-0 pointer-events-none flex flex-col justify-end items-center pb-2 opacity-30">
        <svg width="40" height="20" viewBox="0 0 40 20" className="text-red-500 fill-current">
          <path d="M 5 0 L 15 20 L 25 0 L 35 20 L 40 0 L 0 0 Z" />
        </svg>
        <span className="text-[10px] font-share-tech text-red-500 uppercase tracking-widest mt-1">Разобрать</span>
      </div>

      {/* Драгабельный элемент */}
      <motion.div
        drag="y"
        dragConstraints={{ top: 0, bottom: 80 }}
        dragElastic={0.1}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        style={{ y, opacity, scale, background, borderColor }}
        className="w-full h-12 flex justify-center items-center cursor-grab active:cursor-grabbing border-b border-t z-10"
      >
        <span className="text-sm font-rajdhani text-white/80 uppercase tracking-wider font-bold">
          <span className="text-xs text-white/40 mr-2">▼</span>
          Свайп вниз для разбора
          <span className="text-xs text-white/40 ml-2">▼</span>
        </span>
      </motion.div>
    </div>
  );
};

export default DragToDismantle;

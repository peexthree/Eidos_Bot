import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import WebApp from '@twa-dev/sdk';

import HoldToEquip from './actions/HoldToEquip';
import DragToDismantle from './actions/DragToDismantle';

const ItemModal = ({ isOpen, onClose, item, onEquip, onDismantle }) => {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!isOpen || !item) return;

    const isRare = item.rarity === 'Epic' || item.rarity === 'Legendary';
    if (!isRare) return;

    const handleDeviceOrientation = (e) => {
      // Нормализуем значения гироскопа для плавного наклона
      const x = e.gamma ? e.gamma / 45 : 0; // Наклон влево-вправо (-45 до 45)
      const y = e.beta ? (e.beta - 45) / 45 : 0; // Наклон вперед-назад (0 до 90)

      setTilt({
        x: Math.max(-1, Math.min(1, x)) * 15, // Ограничиваем угол поворота 15 градусами
        y: Math.max(-1, Math.min(1, y)) * 15
      });
    };

    window.addEventListener('deviceorientation', handleDeviceOrientation);
    return () => window.removeEventListener('deviceorientation', handleDeviceOrientation);
  }, [isOpen, item]);

  if (!item) return null;

  const rarityColor = {
    Common: 'text-white border-white/20',
    Rare: 'text-blue-400 border-blue-400/30',
    Epic: 'text-purple-400 border-purple-400/40',
    Legendary: 'text-orange-400 border-orange-400/50'
  }[item.rarity] || 'text-white';

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Затенение фона */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[80000] bg-black/60 backdrop-blur-sm"
          />

          {/* Bottom Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            drag="y"
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, info) => {
              if (info.offset.y > 100) {
                onClose();
              }
            }}
            className="fixed bottom-0 left-0 right-0 z-[90000] p-4 pb-8 bg-eidos-bg/80 backdrop-blur-2xl border-t border-eidos-cyan/20"
            style={{
              clipPath: 'polygon(20px 0, 100% 0, 100% 100%, 0 100%, 0 20px)' // Фирменный срез Eidos
            }}
          >
            {/* Хендлер для свайпа */}
            <div className="w-12 h-1 bg-white/20 rounded-full mx-auto mb-6" />

            <motion.div
              style={{
                rotateX: tilt.y,
                rotateY: tilt.x,
                transformPerspective: 1000
              }}
              className="flex flex-col items-center gap-6"
            >
              {/* Голограмма предмета */}
              <div className={`w-32 h-32 flex items-center justify-center border ${rarityColor} bg-black/40 backdrop-blur-md rotate-45`}>
                <div className="-rotate-45 text-4xl">
                  {item.icon}
                </div>
              </div>

              {/* Информация */}
              <div className="text-center w-full">
                <h2 className={`text-2xl font-orbitron tracking-widest uppercase mb-2 ${rarityColor.split(' ')[0]}`}>
                  {item.name}
                </h2>
                <p className="text-sm font-share-tech text-white/60 mb-4 px-4">
                  {item.description}
                </p>
                <div className="grid grid-cols-2 gap-2 text-sm font-rajdhani">
                  <div className="bg-white/5 p-2 rounded border border-white/10">
                    <span className="text-white/40 block">УРОВЕНЬ</span>
                    <span className="text-eidos-cyan">{item.level || 1}</span>
                  </div>
                  <div className="bg-white/5 p-2 rounded border border-white/10">
                    <span className="text-white/40 block">ПРОЧНОСТЬ</span>
                    <span className="text-white">{item.durability || '100%'}</span>
                  </div>
                </div>
              </div>

              {/* Действия */}
              <div className="w-full flex flex-col gap-4 mt-4">
                <HoldToEquip onEquip={() => onEquip(item.id)} />
                <DragToDismantle onDismantle={() => onDismantle(item.id)} />
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ItemModal;

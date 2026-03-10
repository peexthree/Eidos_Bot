import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import WebApp from '@twa-dev/sdk';
import useStore from '../store/useStore';
import axios from 'axios';

const ItemModal = ({ isOpen, onClose, item }) => {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(false);

  const profile = useStore((state) => state.profile);
  const equipped = useStore((state) => state.equipped) || {};
  const fetchProfile = useStore((state) => state.fetchProfile);

  const itemId = item?.id || item?.item_id;
  const isEquipped = itemId && Object.values(equipped).some(val =>
    val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))
  );

  useEffect(() => {
    if (!isOpen || !item) return;

    const isRare = item.rarity === 'epic' || item.rarity === 'legendary' || item.rarity === 'Epic' || item.rarity === 'Legendary';
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

  const handleEquipToggle = async () => {
    setIsLoading(true);
    try {
      // Telegram initData injection should be handled globally via axios interceptor
      // but let's pass uid here as well
      let uid;
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
          uid = window.Telegram.WebApp.initDataUnsafe.user.id;
      } else {
          const urlParams = new URLSearchParams(window.location.search);
          uid = urlParams.get('uid');
      }

      if (isEquipped) {
        // Find which slot it is equipped in
        let slotToUnequip = null;
        for (const [slot, val] of Object.entries(equipped)) {
           if (val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))) {
              slotToUnequip = slot;
              break;
           }
        }

        if (slotToUnequip) {
          await axios.post('/api/action/unequip', { uid: uid, item_id: itemId }); // Using /api/action/unequip as per directive, although bot.py says /api/inventory/unequip (let's use bot.py's one if it exists or action if specified) Wait, user said `POST /api/action/unequip`. I will use `/api/inventory/unequip` to be safe if that's what's mapped, or use both if one fails. Actually I will just check the bot.py and update it if necessary or just use `/api/inventory/unequip`. Wait, the prompt specifically says "triggers POST /api/action/unequip". Let me update bot.py to handle this route.
        }
      } else {
        await axios.post('/api/action/equip', { uid: uid, item_id: itemId });
      }

      // Immediately fetch updated profile
      if (uid) {
         await fetchProfile(uid);
      }
      onClose();
    } catch (error) {
      console.error("Action error:", error);
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.showAlert("Ошибка при выполнении действия");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const rarityColor = {
    common: 'text-white border-white/20',
    rare: 'text-blue-400 border-blue-400/30',
    epic: 'text-purple-400 border-purple-400/40',
    legendary: 'text-orange-400 border-orange-400/50',
    Common: 'text-white border-white/20',
    Rare: 'text-blue-400 border-blue-400/30',
    Epic: 'text-purple-400 border-purple-400/40',
    Legendary: 'text-orange-400 border-orange-400/50'
  }[item.rarity || 'common'] || 'text-white';

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
            className="fixed bottom-0 left-0 right-0 z-[90000] p-4 pb-8 bg-eidos-bg/90 backdrop-blur-2xl border-t border-eidos-cyan/30"
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
              {/* Голограмма предмета Large Image */}
              <div className={`w-40 h-40 flex items-center justify-center border ${rarityColor} bg-black/40 backdrop-blur-md relative overflow-hidden clip-hex`}>
                 {item.image_url ? (
                    <img src={item.image_url} alt={item.name} className="w-full h-full object-contain p-2 z-10" />
                 ) : (
                    <div className="text-4xl z-10">
                      {item.icon || '📦'}
                    </div>
                 )}
                 <div className={`absolute inset-0 opacity-20 bg-gradient-to-tr from-transparent to-${rarityColor.split('-')[1]} z-0`} />
              </div>

              {/* Информация */}
              <div className="text-center w-full">
                <h2 className={`text-2xl font-orbitron tracking-widest uppercase mb-2 ${rarityColor.split(' ')[0]}`}>
                  {item.name}
                </h2>
                <p className="text-sm font-share text-white/70 mb-4 px-4 h-20 overflow-y-auto">
                  {item.description || item.desc || "Описание отсутствует."}
                </p>
                <div className="grid grid-cols-3 gap-2 text-sm font-rajdhani mb-4">
                  <div className="bg-white/5 p-2 rounded border border-white/10 flex flex-col items-center">
                    <span className="text-eidos-red text-[10px] uppercase font-share tracking-wider">ATK</span>
                    <span className="text-white text-lg font-bold">{item?.stats?.atk || item?.atk || 0}</span>
                  </div>
                  <div className="bg-white/5 p-2 rounded border border-white/10 flex flex-col items-center">
                    <span className="text-blue-400 text-[10px] uppercase font-share tracking-wider">DEF</span>
                    <span className="text-white text-lg font-bold">{item?.stats?.def || item?.def || 0}</span>
                  </div>
                  <div className="bg-white/5 p-2 rounded border border-white/10 flex flex-col items-center">
                    <span className="text-yellow-400 text-[10px] uppercase font-share tracking-wider">LUCK</span>
                    <span className="text-white text-lg font-bold">{item?.stats?.luck || item?.luck || 0}</span>
                  </div>
                </div>
              </div>

              {/* Действия */}
              <div className="w-full flex flex-col gap-3 mt-2">
                {item.type !== 'Consumable' && item.type !== 'consumable' && item.type !== 'misc' && (
                  <button
                     onClick={handleEquipToggle}
                     disabled={isLoading}
                     className={`w-full font-orbitron font-bold text-lg py-4 clip-hex border transition-all ${
                        isEquipped
                          ? 'bg-eidos-red/20 text-eidos-red border-eidos-red hover:bg-eidos-red/40'
                          : 'bg-eidos-cyan/20 text-eidos-cyan border-eidos-cyan hover:bg-eidos-cyan/40'
                     } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                     {isLoading ? 'ОБРАБОТКА...' : isEquipped ? 'СНЯТЬ (UNEQUIP)' : 'НАДЕТЬ (EQUIP)'}
                  </button>
                )}

                <button
                   onClick={onClose}
                   className="w-full font-share text-sm py-2 text-white/50 hover:text-white transition-colors uppercase tracking-widest"
                >
                   Закрыть
                </button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default ItemModal;

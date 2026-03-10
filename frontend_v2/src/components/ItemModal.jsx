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

  const handleDismantle = async () => {
    setIsLoading(true);
    try {
      let uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
      // The backend uses string ids or internal ids, try the default item_id from DB
      await axios.post('/api/inventory/dismantle', { uid, inv_id: item.id });
      if (uid) await fetchProfile(uid);
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEquipToggle = async (action) => {
    setIsLoading(true);
    try {
      let uid;
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
          uid = window.Telegram.WebApp.initDataUnsafe.user.id;
      } else {
          const urlParams = new URLSearchParams(window.location.search);
          uid = urlParams.get('uid');
      }

      // API mapping for unequip slot.
      // API expects: head, weapon, body, software, artifact
      const apiSlotMap = {
          'armor': 'body',
          'chip': 'software',
          'eidos_shard': 'artifact'
      };

      if (action === 'unequip' || isEquipped) {
        let slotToUnequip = null;
        for (const [slot, val] of Object.entries(equipped)) {
           if (val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))) {
              slotToUnequip = slot;
              break;
           }
        }

        if (slotToUnequip) {
          const apiSlot = apiSlotMap[slotToUnequip] || slotToUnequip;
          await axios.post('/api/inventory/unequip', { uid: uid, slot: apiSlot });
        }
      } else {
        await axios.post('/api/inventory/equip', { uid: uid, item_id: itemId });
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
              <div className={`w-full aspect-square flex items-center justify-center border-t border-b ${rarityColor} bg-black/40 backdrop-blur-md relative overflow-hidden`}>
                 {/* ABSOLUTE STATS OVERLAY IN TOP LEFT CORNER */}
                 <div className="absolute top-2 left-2 flex flex-col gap-1 z-20">
                    <div className="flex items-center space-x-1 bg-black/60 px-2 py-1 rounded border border-white/10">
                       <img src="/IMG/eidos_weapon-attack.svg" alt="ATK" className="w-3 h-3 text-eidos-red" style={{ filter: 'var(--svg-color-red, invert(28%) sepia(85%) saturate(7186%) hue-rotate(352deg) brightness(102%) contrast(106%))' }} />
                       <span className="text-eidos-red text-[10px] uppercase font-share tracking-wider">ATK</span>
                       <span className="text-white text-sm font-bold">{item?.stats?.atk || item?.atk || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1 bg-black/60 px-2 py-1 rounded border border-white/10">
                       <img src="/IMG/eidos_shield-armor.svg" alt="DEF" className="w-3 h-3 text-blue-400" style={{ filter: 'var(--svg-color-blue, invert(60%) sepia(45%) saturate(4522%) hue-rotate(193deg) brightness(101%) contrast(105%))' }} />
                       <span className="text-blue-400 text-[10px] uppercase font-share tracking-wider">DEF</span>
                       <span className="text-white text-sm font-bold">{item?.stats?.def || item?.def || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1 bg-black/60 px-2 py-1 rounded border border-white/10">
                       <img src="/IMG/eidos_luck-dice.svg" alt="LCK" className="w-3 h-3 text-yellow-400" style={{ filter: 'var(--svg-color-yellow, invert(85%) sepia(50%) saturate(1008%) hue-rotate(359deg) brightness(105%) contrast(104%))' }} />
                       <span className="text-yellow-400 text-[10px] uppercase font-share tracking-wider">LCK</span>
                       <span className="text-white text-sm font-bold">{item?.stats?.luck || item?.luck || 0}</span>
                    </div>
                 </div>

                 {item.image_url ? (
                    <img src={item.image_url} alt={item.name} className="w-full h-full object-cover z-10" />
                 ) : (
                    <div className="text-6xl z-10">
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
                <p className="text-sm font-share text-white/70 mb-4 px-4 w-full">
                  {item.description || item.desc || "Описание отсутствует."}
                </p>

              </div>

              {/* Действия */}
              <div className="w-full flex justify-between gap-2 mt-2 px-2">
                {item.type !== 'Consumable' && item.type !== 'consumable' && item.type !== 'misc' && !isEquipped && (
                  <button
                     onClick={() => handleEquipToggle('equip')}
                     disabled={isLoading}
                     className={`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-eidos-cyan/20 text-eidos-cyan border-eidos-cyan hover:bg-eidos-cyan/40 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                     [ НАДЕТЬ ]
                  </button>
                )}
                {isEquipped && (
                  <button
                     onClick={() => handleEquipToggle('unequip')}
                     disabled={isLoading}
                     className={`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-eidos-red/20 text-eidos-red border-eidos-red hover:bg-eidos-red/40 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                     [ СНЯТЬ ]
                  </button>
                )}

                <button
                   onClick={handleDismantle}
                   disabled={isLoading || isEquipped}
                   className={`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-yellow-400/20 text-yellow-400 border-yellow-400 hover:bg-yellow-400/40 ${isLoading || isEquipped ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                   [ РАЗОБРАТЬ ]
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

import React from 'react';
import useStore from '../store/useStore';

const EquipSlot = ({ label, slot, item }) => {
  const unequipItem = useStore((state) => state.unequipItem);

  const handleUnequip = () => {
    if (item) {
      unequipItem(slot);
    }
  };

  const rarityColorMap = {
    common: 'border-white text-white',
    rare: 'border-eidos-cyan text-eidos-cyan',
    epic: 'border-purple-500 text-purple-500',
    legendary: 'border-eidos-red text-eidos-red'
  };

  const isEmpty = !item;
  const itemRarity = item?.rarity || 'common';
  const slotColorClass = isEmpty ? 'border-white/20 text-white/40 border-dashed' : (rarityColorMap[itemRarity] || rarityColorMap.common);
  const bgClass = isEmpty ? 'bg-black/20' : 'bg-eidos-glass';

  return (
    <div
      onClick={handleUnequip}
      className={`relative flex flex-col items-center justify-center p-2 w-20 h-24 clip-hex border-2 transition-all duration-300 ${slotColorClass} ${bgClass} cursor-pointer hover:bg-white/10`}
    >
      <div className="absolute top-1 left-2 text-[8px] font-share uppercase opacity-50 tracking-widest z-10">
        {label}
      </div>
      {isEmpty ? (
        <div className="font-share text-xs opacity-30 mt-2">EMPTY</div>
      ) : (
        <div className="flex flex-col items-center text-center w-full h-full relative z-0 mt-2">
           {item?.image_url ? (
             <div className="w-10 h-10 mb-1 flex-shrink-0">
               <img src={item.image_url} alt={item?.name} className="w-full h-full object-cover rounded-sm" />
             </div>
           ) : (
             <div className="w-10 h-10 mb-1 bg-white/10 flex items-center justify-center flex-shrink-0">
               <span className="font-share text-[8px] opacity-50">NO IMG</span>
             </div>
           )}

           <div className={`font-orbitron text-[8px] leading-tight font-bold truncate w-full ${itemRarity === 'legendary' ? 'text-glow-red' : ''}`}>
             {item?.name || 'Unknown'}
           </div>
        </div>
      )}
    </div>
  );
};

const EquipDoll = () => {
  const equipped = useStore((state) => state.equipped) || {};
  const inventory = useStore((state) => state.inventory) || [];

  const getItem = (id) => inventory.find(i => i?.id === id);

  return (
    <div className="w-full bg-eidos-glass p-6 clip-hex border border-white/10 relative overflow-hidden mb-6">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'linear-gradient(var(--color-eidos-cyan) 1px, transparent 1px), linear-gradient(90deg, var(--color-eidos-cyan) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />

      <div className="relative z-10 flex flex-col items-center">
        {/* Head */}
        <div className="mb-2">
          <EquipSlot label="HEAD" slot="head" item={getItem(equipped?.head)} />
        </div>

        {/* Middle row: Weapon, Body, Software */}
        <div className="flex items-center justify-center gap-4 mb-2">
          <EquipSlot label="WEAPON" slot="weapon" item={getItem(equipped?.weapon)} />
          <EquipSlot label="BODY" slot="body" item={getItem(equipped?.body)} />
          <EquipSlot label="SOFTWARE" slot="software" item={getItem(equipped?.software)} />
        </div>

        {/* Artifact */}
        <div>
           <EquipSlot label="ARTIFACT" slot="artifact" item={getItem(equipped?.artifact)} />
        </div>
      </div>
    </div>
  );
};

export default EquipDoll;

import React from 'react';
import useStore from '../store/useStore';

const ItemCard = ({ item }) => {
  const equipped = useStore((state) => state.equipped) || {};

  const isEquipped = Object.values(equipped).some(val =>
    val === item?.id || (val && typeof val === 'object' && val.item_id === item?.id)
  );

  const rarityStyles = {
    common: 'border-l-white bg-white/5',
    rare: 'border-l-eidos-cyan bg-eidos-cyan/10',
    epic: 'border-l-purple-500 bg-purple-500/10 text-glow-purple',
    legendary: 'border-l-eidos-red bg-eidos-red/10 text-glow-red',
    Common: 'border-l-white bg-white/5',
    Rare: 'border-l-eidos-cyan bg-eidos-cyan/10',
    Epic: 'border-l-purple-500 bg-purple-500/10 text-glow-purple',
    Legendary: 'border-l-eidos-red bg-eidos-red/10 text-glow-red'
  };

  const itemRarity = item?.rarity || 'common';
  const borderColor = rarityStyles[itemRarity] || rarityStyles.common;

  return (
    <div
      className={`relative flex items-center justify-between p-3 mb-2 clip-hex bg-eidos-glass border border-white/10 border-l-4 ${borderColor} transition-all duration-300 hover:bg-white/10 group cursor-pointer`}
    >
      <div className="flex items-center flex-1 gap-3">
        {/* Item Image */}
        <div className="w-12 h-12 flex-shrink-0 bg-black/40 border border-white/20 clip-hex flex items-center justify-center overflow-hidden">
           {item?.image_url ? (
             <img src={item.image_url} alt={item?.name} className="w-full h-full object-cover" />
           ) : (
             <span className="font-share text-[20px]">{item?.icon || '📦'}</span>
           )}
        </div>

        <div className="flex flex-col flex-1">
          <h3 className="font-orbitron text-sm font-bold tracking-widest text-white/90 group-hover:text-white transition-colors">
            {item?.name || 'Unknown Item'}
          </h3>
          <div className="flex items-center space-x-2 mt-1 flex-wrap gap-y-1">
            <span className="font-share text-[10px] uppercase text-white/50 border border-white/20 px-1 py-0.5 rounded-sm flex items-center gap-1">
              <img src="/IMG/nav_tab-equip.svg" alt="" className="w-2 h-2 opacity-50" />
              {item?.type || 'Unknown'}
            </span>
            {item?.amount && (
              <span className="font-share text-[10px] text-yellow-400">
                QTY: {item.amount}
              </span>
            )}
            {item?.stats && (
              <div className="font-share text-[10px] text-eidos-cyan flex space-x-2">
                {Object.entries(item.stats).map(([k, v]) => (
                  <span key={k}>+{v}{k.toUpperCase()}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {item?.type !== 'Consumable' && item?.type !== 'consumable' && item?.type !== 'misc' && (
        <div
          className={`ml-4 font-share text-xs px-3 py-1 border clip-hex transition-colors flex-shrink-0 ${
            isEquipped
              ? 'border-eidos-neon text-eidos-neon bg-eidos-neon/10'
              : 'border-white/30 text-white/70 bg-black/40'
          }`}
        >
          {isEquipped ? 'EQUIPPED' : 'IN BAG'}
        </div>
      )}
    </div>
  );
};

export default ItemCard;

import React from 'react';
import useStore from '../store/useStore';

const ItemCard = ({ item }) => {
  const equipItem = useStore((state) => state.equipItem);
  const equipped = useStore((state) => state.equipped);

  const isEquipped = Object.values(equipped).includes(item.id);

  const handleEquip = () => {
    if (item.type !== 'Consumable') {
      equipItem(item.type.toLowerCase(), item.id);
    }
  };

  const rarityStyles = {
    common: 'border-l-white bg-white/5',
    rare: 'border-l-eidos-cyan bg-eidos-cyan/10',
    epic: 'border-l-purple-500 bg-purple-500/10 text-glow-purple',
    legendary: 'border-l-eidos-red bg-eidos-red/10 text-glow-red',
  };

  const borderColor = rarityStyles[item.rarity] || rarityStyles.common;

  return (
    <div
      className={`relative flex items-center justify-between p-3 mb-2 clip-hex bg-eidos-glass border border-white/10 border-l-4 ${borderColor} transition-all duration-300 hover:bg-white/10 group`}
    >
      <div className="flex flex-col flex-1">
        <h3 className="font-orbitron text-sm font-bold tracking-widest text-white/90 group-hover:text-white transition-colors">
          {item.name}
        </h3>
        <div className="flex items-center space-x-2 mt-1">
          <span className="font-share text-[10px] uppercase text-white/50 border border-white/20 px-1 py-0.5 rounded-sm">
            {item.type}
          </span>
          {item.amount && (
            <span className="font-share text-[10px] text-yellow-400">
              QTY: {item.amount}
            </span>
          )}
          {item.stats && (
            <div className="font-share text-[10px] text-eidos-cyan flex space-x-2">
              {Object.entries(item.stats).map(([k, v]) => (
                <span key={k}>+{v}{k.toUpperCase()}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {item.type !== 'Consumable' && (
        <button
          onClick={handleEquip}
          disabled={isEquipped}
          className={`ml-4 font-share text-xs px-3 py-1 border clip-hex transition-colors ${
            isEquipped
              ? 'border-eidos-neon text-eidos-neon bg-eidos-neon/10 opacity-50 cursor-not-allowed'
              : 'border-white/30 text-white/70 hover:border-eidos-cyan hover:text-eidos-cyan bg-black/40'
          }`}
        >
          {isEquipped ? 'EQUIPPED' : 'EQUIP'}
        </button>
      )}
    </div>
  );
};

export default ItemCard;

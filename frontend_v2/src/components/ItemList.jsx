import React, { useState } from 'react';
import useStore from '../store/useStore';
import ItemCard from './ItemCard';

const ItemList = () => {
  const inventory = useStore((state) => state.inventory);
  const [filter, setFilter] = useState('ALL');

  const filters = ['ALL', 'EQUIP', 'CONSUMABLES'];

  const filteredInventory = inventory.filter((item) => {
    if (filter === 'ALL') return true;
    if (filter === 'EQUIP') return item.type !== 'Consumable';
    if (filter === 'CONSUMABLES') return item.type === 'Consumable';
    return true;
  });

  return (
    <div className="flex flex-col flex-1 bg-eidos-glass p-4 border border-white/10 clip-hex relative overflow-hidden h-full">
      {/* Filters */}
      <div className="flex justify-between items-center mb-4 border-b border-white/20 pb-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`font-orbitron text-xs px-3 py-1 transition-all clip-hex ${
              filter === f
                ? 'bg-eidos-cyan text-black font-bold text-glow-cyan'
                : 'text-white/50 hover:text-white bg-black/40 border border-white/20'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Item List Scroll Area */}
      <div className="scroll-area flex-1 overflow-y-auto pr-2 space-y-2 relative z-10">
        {filteredInventory.map((item) => (
          <ItemCard key={item.id} item={item} />
        ))}
        {filteredInventory.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-black/40 border border-white/10 clip-hex">
            <span className="font-orbitron text-eidos-red text-xl mb-2">EMPTY</span>
            <span className="font-share text-xs text-white/50">NO ITEMS FOUND IN STORAGE</span>
          </div>
        )}
      </div>

      {/* Decorative Scanline Overlay */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-eidos-cyan/5 to-transparent h-[10px] w-full sys-scanline animate-pulse"></div>
    </div>
  );
};

export default ItemList;

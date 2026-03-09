import React from 'react';
import { useLocation } from 'wouter';
import { motion } from 'framer-motion';

const NexusTile = ({ title, icon, path, status = "ONLINE", color = "eidos-cyan" }) => {
  const [, setLocation] = useLocation();

  const colorMap = {
    'eidos-cyan': 'text-eidos-cyan border-eidos-cyan/30 hover:border-eidos-cyan bg-eidos-cyan/10 hover:bg-eidos-cyan/20 text-glow-cyan',
    'eidos-red': 'text-eidos-red border-eidos-red/30 hover:border-eidos-red bg-eidos-red/10 hover:bg-eidos-red/20 text-glow-red',
    'eidos-neon': 'text-eidos-neon border-eidos-neon/30 hover:border-eidos-neon bg-eidos-neon/10 hover:bg-eidos-neon/20 text-glow-neon',
    'yellow-400': 'text-yellow-400 border-yellow-400/30 hover:border-yellow-400 bg-yellow-400/10 hover:bg-yellow-400/20 text-glow-yellow'
  };

  const styleClass = colorMap[color] || colorMap['eidos-cyan'];

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => setLocation(path)}
      className={`relative flex flex-col items-center justify-center p-4 h-32 clip-hex border-2 transition-all duration-300 ${styleClass} group`}
    >
      <div className="absolute top-2 left-2 text-[8px] font-share opacity-50 uppercase">
        {status}
      </div>
      <div className="w-10 h-10 mb-2 opacity-80 group-hover:opacity-100 transition-opacity">
        {/* Иконка (с fallback на текст, если не загрузится) */}
        <img src={icon} alt={title} className="w-full h-full" style={{ filter: 'var(--svg-color-current, invert(1))' }} onError={(e) => { e.target.style.display='none'; }} />
      </div>
      <span className="font-orbitron font-bold tracking-widest text-sm uppercase">
        {title}
      </span>
      {/* Уголки для эффекта прицела */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-current opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-current opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </motion.button>
  );
};

const Nexus = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full">
      <div className="text-center mb-8 w-full max-w-sm">
        <h1 className="font-orbitron text-3xl font-bold text-white tracking-[0.2em] mb-2 text-glow-cyan">
          NEXUS.<span className="text-eidos-cyan">GRID</span>
        </h1>
        <div className="h-px w-full bg-gradient-to-r from-transparent via-eidos-cyan to-transparent opacity-50"></div>
        <p className="font-share text-xs text-eidos-cyan/70 mt-2 uppercase tracking-widest">
          SYSTEM_VER: 2.0.4b // NEURAL LINK ACTIVE
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full max-w-sm" id="view-nexus">
        <NexusTile title="Profile" icon="/IMG/nav_head-eidos.svg" path="/profile" color="eidos-neon" />
        <NexusTile title="Inventory" icon="/IMG/nav_tab-equip.svg" path="/inventory" color="eidos-cyan" />
        <NexusTile title="Market" icon="/IMG/nav_head-shop.svg" path="/shop" color="yellow-400" />
        <NexusTile title="Arena" icon="/IMG/eidos_arena-pvp.svg" path="/arena" color="eidos-red" />
        <NexusTile title="Raids" icon="/IMG/nav_head-raid.svg" path="/raids" color="eidos-red" />
        <NexusTile title="Settings" icon="/IMG/eidos_settings-gear.svg" path="/settings" color="white" status="OFFLINE" />
      </div>
    </div>
  );
};

export default Nexus;

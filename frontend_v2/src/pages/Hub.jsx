import React from 'react';
import { motion } from 'framer-motion';
import useStore from '../store/useStore';
import ProfileHeader from '../components/ProfileHeader';

const HubTile = ({ title, icon, color = "eidos-cyan", onClick }) => {
  const colorMap = {
    'eidos-cyan': 'text-eidos-cyan border-eidos-cyan/30 hover:border-eidos-cyan bg-eidos-cyan/10 hover:bg-eidos-cyan/20 text-glow-cyan',
    'eidos-red': 'text-eidos-red border-eidos-red/30 hover:border-eidos-red bg-eidos-red/10 hover:bg-eidos-red/20 text-glow-red',
    'eidos-neon': 'text-eidos-neon border-eidos-neon/30 hover:border-eidos-neon bg-eidos-neon/10 hover:bg-eidos-neon/20 text-glow-neon',
    'yellow-400': 'text-yellow-400 border-yellow-400/30 hover:border-yellow-400 bg-yellow-400/10 hover:bg-yellow-400/20 text-glow-yellow',
    'white': 'text-white border-white/30 hover:border-white bg-white/10 hover:bg-white/20'
  };

  const styleClass = colorMap[color] || colorMap['eidos-cyan'];

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`relative flex flex-col items-center justify-center p-4 h-32 clip-hex border-2 transition-all duration-300 ${styleClass} group backdrop-blur-md`}
    >
      <div className="w-10 h-10 mb-2 opacity-80 group-hover:opacity-100 transition-opacity">
        <img src={icon} alt={title} className="w-full h-full" style={{ filter: 'var(--svg-color-current, invert(1))' }} onError={(e) => { e.target.style.display='none'; }} />
      </div>
      <span className="font-orbitron font-bold tracking-widest text-sm uppercase">
        {title}
      </span>
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-current opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-current opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </motion.button>
  );
};

const HeroBanner = ({ title, color = "eidos-cyan", onClick, status="" }) => {
    const colorMap = {
      'eidos-cyan': 'text-eidos-cyan border-eidos-cyan/30 hover:border-eidos-cyan bg-eidos-cyan/10 hover:bg-eidos-cyan/20 text-glow-cyan',
      'eidos-red': 'text-eidos-red border-eidos-red/30 hover:border-eidos-red bg-eidos-red/10 hover:bg-eidos-red/20 text-glow-red',
      'yellow-400': 'text-yellow-400 border-yellow-400/30 hover:border-yellow-400 bg-yellow-400/10 hover:bg-yellow-400/20 text-glow-yellow'
    };
    const styleClass = colorMap[color] || colorMap['eidos-cyan'];

    return (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onClick}
          className={`relative w-full py-3 px-4 clip-hex border transition-all duration-300 flex justify-between items-center group backdrop-blur-md mb-2 ${styleClass}`}
        >
            <span className="font-orbitron font-bold tracking-widest uppercase">{title}</span>
            <div className="flex space-x-1">
                <div className="w-1.5 h-1.5 bg-current opacity-50"></div>
                <div className="w-1.5 h-1.5 bg-current opacity-75"></div>
                <div className="w-1.5 h-1.5 bg-current"></div>
            </div>
        </motion.button>
    )
}

const QuickAction = ({ title, icon, onClick }) => {
    return (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onClick}
          className="flex-1 flex items-center justify-center py-2 px-2 clip-hex bg-eidos-cyan/10 border border-eidos-cyan/30 hover:bg-eidos-cyan/20 hover:border-eidos-cyan text-eidos-cyan transition-all backdrop-blur-md group"
        >
            <img src={icon} className="w-5 h-5 mr-2 opacity-80 group-hover:opacity-100" style={{ filter: 'invert(1)' }} alt={title} onError={(e) => { e.target.style.display='none'; }}/>
            <span className="font-orbitron text-xs uppercase font-bold tracking-wider">{title}</span>
        </motion.button>
    )
}

const Hub = ({ setView }) => {
  const twa = window.Telegram?.WebApp;

  const handleOfflineAction = () => {
      if (twa && twa.showPopup) {
          twa.showPopup({
              title: 'SYSTEM MODULE OFFLINE',
              message: 'Модуль находится в разработке.',
              buttons: [{type: 'close'}]
          });
      } else {
          alert("MODULE OFFLINE");
      }
  }

  return (
    <div className="flex flex-col h-full w-full max-w-sm mx-auto space-y-4 pb-16">

      {/* BLOCK 1: HEADER */}
      <ProfileHeader />

      {/* BLOCK 2: QUICK ACTIONS */}
      <div className="flex w-full space-x-3">
          <QuickAction title="[ СИНХРОН ]" icon="/IMG/eidos_net-sync.svg" onClick={handleOfflineAction} />
          <QuickAction title="[ СИГНАЛ ]" icon="/IMG/eidos_comm-link.svg" onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 3: MAIN CALIBER (Hero Banners) */}
      <div className="w-full flex flex-col space-y-2 mt-4">
          <HeroBanner title="[ НУЛЕВОЙ СЛОЙ ]" color="eidos-cyan" onClick={handleOfflineAction} />
          <HeroBanner title="[ СЕТЕВАЯ ВОЙНА ]" color="eidos-red" onClick={handleOfflineAction} />
          <HeroBanner title="[ ВРАТА ЭЙДОСА ]" color="yellow-400" onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 4: MANAGEMENT GRID (2x3 Grid) */}
      <div className="grid grid-cols-2 gap-3 w-full mt-4" id="view-nexus">
        <HubTile title="[ ПРОФИЛЬ ]" icon="/IMG/eidos_demiurge-user.svg" color="eidos-neon" onClick={handleOfflineAction} />
        <HubTile title="[ РЫНОК ]" icon="/IMG/eidos_black-market.svg" color="yellow-400" onClick={handleOfflineAction} />

        <HubTile title="[ ИНВЕНТАРЬ ]" icon="/IMG/eidos_inventory-cache.svg" color="eidos-cyan" onClick={() => setView('INVENTORY')} />
        <HubTile title="[ РЕЙТИНГ ]" icon="/IMG/eidos_xp-rank.svg" color="eidos-neon" onClick={handleOfflineAction} />

        <HubTile title="[ СИНДИКАТ ]" icon="/IMG/eidos_shield-armor.svg" color="eidos-red" onClick={handleOfflineAction} />
        <HubTile title="[ ДНЕВНИК ]" icon="/IMG/eidos_neuro-brain.svg" color="white" onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 5: FOOTER (Meta) */}
      <div className="w-full mt-6 mb-4 flex flex-col items-center space-y-3">
          <motion.button
             whileTap={{ scale: 0.95 }}
             onClick={handleOfflineAction}
             className="w-full py-3 clip-hex border border-white/20 bg-black/50 text-white/50 hover:text-white hover:border-white/50 transition-colors backdrop-blur-md uppercase font-orbitron text-xs tracking-widest text-center"
          >
              [ ТЕНЕВОЙ БРОКЕР ]
          </motion.button>

          <div className="flex w-full justify-between items-center px-4">
             <div className="flex space-x-4">
                <button onClick={handleOfflineAction} className="opacity-50 hover:opacity-100 transition-opacity">
                   <img src="/IMG/eidos_neuro-brain.svg" className="w-6 h-6" style={{ filter: 'invert(1)' }} alt="Гайд"/>
                </button>
                <button onClick={handleOfflineAction} className="opacity-50 hover:opacity-100 transition-opacity">
                   <img src="/IMG/eidos_comm-link.svg" className="w-6 h-6" style={{ filter: 'invert(1)' }} alt="Обратная связь"/>
                </button>
             </div>

             <button onClick={handleOfflineAction} className="font-orbitron text-xs text-yellow-500/50 hover:text-yellow-400 border border-yellow-500/20 hover:border-yellow-400/50 px-3 py-1 clip-hex bg-black/50 transition-colors">
                [ ⚡ GOD MODE ]
             </button>
          </div>
      </div>

    </div>
  );
};

export default Hub;

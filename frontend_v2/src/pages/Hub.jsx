import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import useStore from '../store/useStore';
import ProfileHeader from '../components/ProfileHeader';
import axios from 'axios';

const HubTile = ({ title, iconUrl, onClick }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="relative flex flex-col items-center justify-end p-2 h-32 clip-hex border border-white/10 group overflow-hidden bg-black/80"
      style={{
        backgroundImage: iconUrl ? `url(${iconUrl})` : 'none',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent transition-opacity group-hover:from-eidos-cyan/30" />
      <div className="relative z-10 w-full text-center pb-1">
        <span className="font-orbitron font-bold tracking-widest text-xs uppercase text-white group-hover:text-glow-cyan group-hover:text-eidos-cyan transition-colors">
          {title}
        </span>
      </div>
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-white/50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-white/50 opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </motion.button>
  );
};

const HeroBanner = ({ title, iconUrl, onClick }) => {
    return (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onClick}
          className="relative w-full h-24 clip-hex border border-white/10 flex items-center justify-center group overflow-hidden bg-black/80 mb-2"
          style={{
            backgroundImage: iconUrl ? `url(${iconUrl})` : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
            <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/40 to-black/80 transition-opacity group-hover:from-eidos-cyan/40" />
            <span className="relative z-10 font-orbitron font-bold tracking-widest uppercase text-white text-lg group-hover:text-glow-cyan group-hover:text-eidos-cyan transition-colors drop-shadow-md">
                {title}
            </span>
            <div className="absolute right-4 flex space-x-1 z-10 opacity-50 group-hover:opacity-100">
                <div className="w-1.5 h-1.5 bg-white group-hover:bg-eidos-cyan"></div>
                <div className="w-1.5 h-1.5 bg-white group-hover:bg-eidos-cyan"></div>
                <div className="w-1.5 h-1.5 bg-white group-hover:bg-eidos-cyan"></div>
            </div>
        </motion.button>
    )
}

const QuickAction = ({ title, iconUrl, onClick }) => {
    return (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onClick}
          className="relative flex-1 flex flex-col items-center justify-center py-4 h-20 clip-hex border border-white/10 bg-black/80 group overflow-hidden"
          style={{
            backgroundImage: iconUrl ? `url(${iconUrl})` : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-black/20 group-hover:from-eidos-cyan/30 transition-opacity" />
            <span className="relative z-10 font-orbitron text-[10px] md:text-xs uppercase font-bold tracking-wider text-white group-hover:text-eidos-cyan group-hover:text-glow-cyan drop-shadow-md">
                {title}
            </span>
        </motion.button>
    )
}

const Hub = ({ setView }) => {
  const twa = window.Telegram?.WebApp;
  const [hubData, setHubData] = useState({});

  useEffect(() => {
    const fetchHubData = async () => {
      try {
        const res = await axios.get('/api/hub_data');
        setHubData(res.data);
      } catch (e) {
        console.error("Failed to fetch hub images", e);
      }
    };
    fetchHubData();
  }, []);

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

  // Helper for safe lookup
  const getImg = (key) => hubData[key] || '';

  return (
    <div className="flex flex-col h-full w-full max-w-sm mx-auto space-y-4 pb-16">

      {/* BLOCK 1: HEADER */}
      <ProfileHeader />

      {/* BLOCK 2: QUICK ACTIONS */}
      <div className="flex w-full space-x-3 mt-2">
          <QuickAction title="[ СИНХРОН ]" iconUrl={getImg("get_protocol")} onClick={handleOfflineAction} />
          <QuickAction title="[ СИГНАЛ ]" iconUrl={getImg("get_signal")} onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 3: MAIN CALIBER (Hero Banners) */}
      <div className="w-full flex flex-col space-y-2 mt-4">
          <HeroBanner title="[ НУЛЕВОЙ СЛОЙ ]" iconUrl={getImg("zero_layer_menu")} onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 4: MANAGEMENT GRID (2x3 Grid) */}
      <div className="grid grid-cols-2 gap-3 w-full mt-2" id="view-nexus">
        <HubTile title="[ РЫНОК ]" iconUrl={getImg("shop_menu")} onClick={handleOfflineAction} />
        <HubTile title="[ ИНВЕНТАРЬ ]" iconUrl={getImg("inventory")} onClick={() => setView('INVENTORY')} />

        <HubTile title="[ СИНДИКАТ ]" iconUrl={getImg("referral")} onClick={handleOfflineAction} />
        <HubTile title="[ РЕЙТИНГ ]" iconUrl={getImg("leaderboard")} onClick={handleOfflineAction} />

        <HubTile title="[ ДНЕВНИК ]" iconUrl={getImg("diary_menu")} onClick={handleOfflineAction} />
        <HubTile title="[ ГАЙД ]" iconUrl={getImg("guide")} onClick={handleOfflineAction} />
      </div>

      {/* BLOCK 5: FOOTER (Meta) */}
      <div className="w-full mt-6 mb-4 flex flex-col items-center space-y-3">
          <motion.button
             whileTap={{ scale: 0.95 }}
             onClick={handleOfflineAction}
             className="relative w-full py-4 clip-hex border border-white/20 bg-black/80 group overflow-hidden"
             style={{
                backgroundImage: getImg("shadow_shop_menu") ? `url(${getImg("shadow_shop_menu")})` : 'none',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
             }}
          >
              <div className="absolute inset-0 bg-black/70 group-hover:bg-eidos-red/20 transition-colors" />
              <div className="relative z-10 text-white/70 group-hover:text-glow-red group-hover:text-eidos-red transition-colors uppercase font-orbitron tracking-widest text-center font-bold">
                  [ ТЕНЕВОЙ БРОКЕР ]
              </div>
          </motion.button>

          <div className="flex w-full justify-between items-center px-4 mt-2">
             <div className="flex space-x-4">
                <button onClick={handleOfflineAction} className="opacity-50 hover:opacity-100 transition-opacity">
                   <img src="/IMG/eidos_comm-link.svg" className="w-6 h-6" style={{ filter: 'invert(1)' }} alt="Обратная связь"/>
                </button>
             </div>

             <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={handleOfflineAction}
                className="relative font-orbitron text-xs text-white border border-white/20 hover:border-white/50 px-4 py-2 clip-hex bg-black/80 overflow-hidden group"
                style={{
                    backgroundImage: getImg("admin_panel") ? `url(${getImg("admin_panel")})` : 'none',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                }}
             >
                <div className="absolute inset-0 bg-black/80 group-hover:bg-yellow-500/30 transition-colors" />
                <span className="relative z-10 group-hover:text-glow-yellow group-hover:text-yellow-400">
                   [ ⚡ GOD MODE ]
                </span>
             </motion.button>
          </div>
      </div>

    </div>
  );
};

export default Hub;

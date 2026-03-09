import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import ProfileHeader from '../components/ProfileHeader';
import axios from 'axios';

const HexButton = ({ title, iconUrl, onClick }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="relative flex flex-col items-center justify-center cursor-pointer group focus:outline-none bg-transparent border-none aspect-[100/115] w-full max-w-[100px] mx-auto"
      style={{
        backgroundImage: 'url(/video/hex_frame.png)',
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
      }}
    >
      {iconUrl && (
        <img
          src={iconUrl}
          alt={title}
          className="w-8 h-8 md:w-10 md:h-10 mb-1 drop-shadow-[0_0_5px_rgba(255,255,255,0.5)] group-hover:drop-shadow-[0_0_8px_rgba(0,229,255,0.8)] transition-all object-contain"
        />
      )}
      <span
        className="font-orbitron font-bold text-[8px] md:text-[9px] uppercase tracking-wider text-center leading-tight px-1"
        style={{ color: '#00E5FF', textShadow: '0 0 5px #00E5FF, 0 0 10px #00E5FF' }}
      >
        {title}
      </span>
    </motion.button>
  );
};

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
    <>
      {/* Layer 0: Video Background */}
      <div className="fixed inset-0 w-[100vw] h-[100vh] -z-20">
        <video
          src="/video/loop_bg.mp4"
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover"
        />
      </div>

      {/* Layer 1: Main Frame Overlay */}
      <div className="fixed inset-0 w-[100vw] h-[100vh] -z-10 pointer-events-none">
        <img
          src="/video/main_frame.png"
          alt="Main Frame"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Layer 2: Interactive Grid */}
      <div className="relative z-10 flex flex-col h-full w-full max-w-sm mx-auto pb-16 px-4">

        {/* BLOCK 1: HEADER */}
        <ProfileHeader />

        {/* HEXAGONAL GRID CONTAINER */}
        <div className="flex flex-col items-center justify-center mt-6 w-full space-y-2">

          {/* Row 1 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="СИНХРОН" iconUrl={getImg("get_protocol")} onClick={handleOfflineAction} />
            <HexButton title="СИГНАЛ" iconUrl={getImg("get_signal")} onClick={handleOfflineAction} />
            <HexButton title="НУЛЕВОЙ СЛОЙ" iconUrl={getImg("zero_layer_menu")} onClick={handleOfflineAction} />
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="РЫНОК" iconUrl={getImg("shop_menu")} onClick={handleOfflineAction} />
            <HexButton title="ИНВЕНТАРЬ" iconUrl={getImg("inventory")} onClick={() => setView('INVENTORY')} />
            <HexButton title="ДНЕВНИК" iconUrl={getImg("diary_menu")} onClick={handleOfflineAction} />
          </div>

          {/* Row 3 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="СИНДИКАТ" iconUrl={getImg("referral")} onClick={handleOfflineAction} />
            <HexButton title="РЕЙТИНГ" iconUrl={getImg("leaderboard")} onClick={handleOfflineAction} />
            <HexButton title="ТЕНЕВОЙ БРОКЕР" iconUrl={getImg("shadow_shop_menu")} onClick={handleOfflineAction} />
          </div>

          {/* Row 4 */}
          <div className="flex justify-center space-x-2 w-full max-w-[320px]">
            <div className="w-1/3">
              <HexButton title="ГАЙД" iconUrl={getImg("guide")} onClick={handleOfflineAction} />
            </div>
            <div className="w-1/3">
              <HexButton title="GOD MODE" iconUrl={getImg("admin_panel")} onClick={handleOfflineAction} />
            </div>
          </div>

        </div>
      </div>
    </>
  );
};

export default Hub;

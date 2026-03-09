import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import ProfileHeader from '../components/ProfileHeader';
import axios from 'axios';

const HexButton = ({ title, iconUrl, tgImageUrl, onClick }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => onClick(tgImageUrl)}
      className="relative flex flex-col items-center justify-center cursor-pointer group focus:outline-none bg-transparent border-none aspect-[100/115] w-full max-w-[100px] mx-auto overflow-hidden"
      style={{
        backgroundImage: 'url(/video/hex_frame.png)',
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
      }}
    >
      {/* Затемнение внутри гексогона 30% */}
      <div
        className="absolute inset-0 bg-black/30 transition-all duration-300 group-hover:bg-black/10"
        style={{
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          transform: 'scale(0.85)'
        }}
      ></div>

      {iconUrl && (
        <img
          src={iconUrl}
          alt={title}
          className="relative z-10 w-8 h-8 md:w-10 md:h-10 mb-1 drop-shadow-[0_0_5px_rgba(255,255,255,0.5)] group-hover:drop-shadow-[0_0_8px_rgba(0,229,255,0.8)] transition-all object-contain"
        />
      )}
      <span
        className="relative z-10 font-orbitron font-bold text-[8px] md:text-[9px] uppercase tracking-wider text-center leading-tight px-1"
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
  const [modalImage, setModalImage] = useState(null);

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

  const handleAction = (tgImageUrl, action) => {
      if (tgImageUrl) {
          setModalImage(tgImageUrl);
      } else if (action) {
          action();
      } else {
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
      <div className="fixed inset-0 w-[100vw] h-[100vh] z-20 pointer-events-none">
        <img
          src="/video/main_frame.png"
          alt="Main Frame"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Layer 2: Interactive Grid */}
      <div className="relative z-10 flex flex-col h-full w-full max-w-sm mx-auto pt-32 pb-16 px-4">

        {/* BLOCK 1: HEADER */}
        <ProfileHeader />

        {/* HEXAGONAL GRID CONTAINER */}
        <div className="flex flex-col items-center justify-center mt-auto mb-8 w-full space-y-2">

          {/* Row 1 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="СИНХРОН" iconUrl="/IMG/eidos_sync.svg" tgImageUrl={getImg("get_protocol")} onClick={(img) => handleAction(img, null)} />
            <HexButton title="СИГНАЛ" iconUrl="/IMG/eidos_signal.svg" tgImageUrl={getImg("get_signal")} onClick={(img) => handleAction(img, null)} />
            <HexButton title="НУЛЕВОЙ СЛОЙ" iconUrl="/IMG/eidos_zero-layer.svg" tgImageUrl={getImg("zero_layer_menu")} onClick={(img) => handleAction(img, null)} />
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="РЫНОК" iconUrl="/IMG/eidos_market.svg" tgImageUrl={getImg("shop_menu")} onClick={(img) => handleAction(img, null)} />
            <HexButton title="ИНВЕНТАРЬ" iconUrl="/IMG/eidos_inventory.svg" tgImageUrl={getImg("inventory")} onClick={(img) => { setView('INVENTORY'); }} />
            <HexButton title="ДНЕВНИК" iconUrl="/IMG/eidos_diary.svg" tgImageUrl={getImg("diary_menu")} onClick={(img) => handleAction(img, null)} />
          </div>

          {/* Row 3 */}
          <div className="grid grid-cols-3 gap-2 w-full max-w-[320px]">
            <HexButton title="СИНДИКАТ" iconUrl="/IMG/eidos_syndicate.svg" tgImageUrl={getImg("referral")} onClick={(img) => handleAction(img, null)} />
            <HexButton title="РЕЙТИНГ" iconUrl="/IMG/eidos_rating.svg" tgImageUrl={getImg("leaderboard")} onClick={(img) => handleAction(img, null)} />
            <HexButton title="ТЕНЕВОЙ БРОКЕР" iconUrl="/IMG/eidos_broker.svg" tgImageUrl={getImg("shadow_shop_menu")} onClick={(img) => handleAction(img, null)} />
          </div>

          {/* Row 4 */}
          <div className="flex justify-center space-x-2 w-full max-w-[320px]">
            <div className="w-1/3">
              <HexButton title="ГАЙД" iconUrl="/IMG/eidos_guides.svg" tgImageUrl={getImg("guide")} onClick={(img) => handleAction(img, null)} />
            </div>
            <div className="w-1/3">
              <HexButton title="GOD MODE" iconUrl="/IMG/eidos_god-mode.svg" tgImageUrl={getImg("admin_panel")} onClick={(img) => handleAction(img, null)} />
            </div>
          </div>

        </div>
      </div>

      {/* Image Modal */}
      {modalImage && (
        <div
          className="fixed inset-0 z-[100000] flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
          onClick={() => setModalImage(null)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative max-w-sm w-full bg-eidos-bg/90 border border-eidos-cyan/50 p-2 clip-hex shadow-[0_0_30px_rgba(102,252,241,0.3)]"
            onClick={(e) => e.stopPropagation()}
          >
             <button
                onClick={() => setModalImage(null)}
                className="absolute top-4 right-4 text-eidos-cyan z-10 bg-black/50 w-8 h-8 rounded-full flex items-center justify-center border border-eidos-cyan/30"
             >
               ✕
             </button>
             <img src={modalImage} alt="Module Interface" className="w-full h-auto object-contain max-h-[70vh] rounded" />
             <div className="mt-4 p-2 text-center text-eidos-cyan font-orbitron border-t border-eidos-cyan/20">
                MODULE PREVIEW
             </div>
          </motion.div>
        </div>
      )}
    </>
  );
};

export default Hub;

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import ProfileHeader from '../components/ProfileHeader';
import axios from 'axios';

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

  const handleAction = async (tgImageUrl, actionUrl, customAction) => {
    if (customAction) {
      customAction();
      return;
    }

    if (actionUrl) {
      try {
        if (twa && twa.HapticFeedback) {
          twa.HapticFeedback.impactOccurred('light');
        }
        await axios.post(actionUrl);
        // Might need a toast or some feedback here, but for now we just post
      } catch (e) {
        console.error(`Failed action: ${actionUrl}`, e);
      }
      return;
    }

    if (tgImageUrl) {
        setModalImage(tgImageUrl);
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

  const getImg = (key) => hubData[key] || '';

  const btnStyle = {
    cursor: 'pointer',
    transition: 'transform 0.1s ease, filter 0.2s',
  };

  const btnHoverActiveStyle = `
    hover:scale-95 hover:brightness-125
    active:scale-95 active:brightness-125
  `;

  return (
    <div style={{
      aspectRatio: '9 / 16',
      width: '100%',
      maxHeight: '100vh',
      position: 'relative',
      margin: '0 auto',
      overflow: 'hidden'
    }}>
      {/* Layer 0: Background Video */}
      <video
        src="/video/back.mp4"
        autoPlay
        loop
        muted
        playsInline
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: 0
        }}
      />

      {/* Layer 1: Button Grid (The Precision Grid) */}
      <div style={{
        position: 'absolute',
        inset: 0,
        zIndex: 5,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        padding: '15% 5% 5% 5%'
      }}>
        {/* Profile Header injected at the top inside the grid layout so it doesn't break absolute positioning */}
        <div style={{ marginBottom: '5%' }}>
          <ProfileHeader />
        </div>

        {/* Header Row */}
        <div style={{ width: '100%', display: 'flex', justifyContent: 'center', marginBottom: '5%' }}>
          <img
            src="/video/nadpis.png"
            alt="Title"
            style={{ width: '80%', objectFit: 'contain' }}
          />
        </div>

        {/* Row 1 (Split 40/60) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', gap: '5%' }}>
          <img
            src="/video/signa.png"
            alt="Signal"
            className={btnHoverActiveStyle}
            style={{ width: '40%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(null, '/api/action/signal')}
          />
          <img
            src="/video/sinxr.png"
            alt="Synchron"
            className={btnHoverActiveStyle}
            style={{ width: '55%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(null, '/api/action/synchron')}
          />
        </div>

        {/* Row 2 (4 Items) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', gap: '2%', marginTop: '5%' }}>
          <img
            src="/video/_nul.png"
            alt="Zero Layer"
            className={btnHoverActiveStyle}
            style={{ width: '23%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("zero_layer_menu"))}
          />
          <img
            src="/video/shop.png"
            alt="Shop"
            className={btnHoverActiveStyle}
            style={{ width: '23%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("shop_menu"))}
          />
          <img
            src="/video/invent.png"
            alt="Inventory"
            className={btnHoverActiveStyle}
            style={{ width: '23%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(null, null, () => setView('INVENTORY'))}
          />
          <img
            src="/video/dnecvnik.png"
            alt="Diary"
            className={btnHoverActiveStyle}
            style={{ width: '23%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("diary_menu"))}
          />
        </div>

        {/* Row 3 (3 Items Centered) */}
        <div style={{ display: 'flex', justifyContent: 'center', width: '100%', gap: '4%', marginTop: '5%' }}>
          <img
            src="/video/sindi.png"
            alt="Syndicate"
            className={btnHoverActiveStyle}
            style={{ width: '28%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("referral"))}
          />
          <img
            src="/video/reiting.png"
            alt="Rating"
            className={btnHoverActiveStyle}
            style={{ width: '28%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("leaderboard"))}
          />
          <img
            src="/video/guid.png"
            alt="Guide"
            className={btnHoverActiveStyle}
            style={{ width: '28%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("guide"))}
          />
        </div>

        {/* Row 4 (Bottom Split) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', gap: '10%', marginTop: '5%' }}>
          <img
            src="/video/shadow_b.png"
            alt="Shadow Broker"
            className={btnHoverActiveStyle}
            style={{ width: '45%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("shadow_shop_menu"))}
          />
          <img
            src="/video/admin.png"
            alt="Admin"
            className={btnHoverActiveStyle}
            style={{ width: '45%', objectFit: 'contain', ...btnStyle }}
            onClick={() => handleAction(getImg("admin_panel"))}
          />
        </div>
      </div>

      {/* Layer 2: Top Frame Overlay */}
      <img
        src="/video/frame.png"
        alt="Frame Overlay"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          pointerEvents: 'none',
          zIndex: 10
        }}
      />

      {/* Image Modal (Z-index strictly highest) */}
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
                className="absolute top-4 right-4 text-eidos-cyan z-10 bg-black/50 w-8 h-8 rounded-full flex items-center justify-center border border-eidos-cyan/30 cursor-pointer hover:bg-white/10"
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
    </div>
  );
};

export default Hub;

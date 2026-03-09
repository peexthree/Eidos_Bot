import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
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

  const btnHoverActiveStyle = `
    hover:scale-95 hover:brightness-125
    active:scale-95 active:brightness-125
    transition-transform duration-100 ease-in-out
  `;

  return (
    <div style={{
      position: 'relative',
      width: '100vw',
      maxWidth: '500px',
      aspectRatio: '9/16',
      margin: '0 auto',
      overflow: 'hidden',
      backgroundColor: '#000'
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
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'fill',
          zIndex: 0
        }}
      />

      {/* Layer 1: Button Grid (Z-Index: 10) */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 10 }}>
        {/* Header Title */}
        <img src="/video/nadpis.png" style={{ position: 'absolute', top: '3%', left: '15%', width: '70%', objectFit: 'contain', zIndex: 10, pointerEvents: 'none' }} />


        {/* Row 1 */}
        <img
          src="/video/signa.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '23%', left: '4%', width: '25%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(null, '/api/action/signal')}
        />
        <img
          src="/video/sinxr.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '15%', left: '33%', width: '34%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(null, '/api/action/synchron')}
        />

        {/* Row 2 */}
        <img
          src="/video/_nul.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '45%', left: '4%', width: '21%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("zero_layer_menu"))}
        />
        <img
          src="/video/shop.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '45%', left: '28%', width: '21%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("shop_menu"))}
        />
        <img
          src="/video/invent.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '45%', left: '52%', width: '21%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(null, null, () => setView('INVENTORY'))}
        />
        <img
          src="/video/dnecvnik.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '45%', left: '76%', width: '21%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("diary_menu"))}
        />

        {/* Row 3 */}
        <img
          src="/video/sindi.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '60%', left: '14%', width: '22%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("referral"))}
        />
        <img
          src="/video/reiting.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '60%', left: '39%', width: '22%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("leaderboard"))}
        />
        <img
          src="/video/guid.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '60%', left: '64%', width: '22%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("guide"))}
        />

        {/* Row 4 */}
        <img
          src="/video/shadow_b.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '78%', left: '8%', width: '40%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("shadow_shop_menu"))}
        />
        <img
          src="/video/admin.png"
          className={btnHoverActiveStyle}
          style={{ position: 'absolute', top: '78%', left: '52%', width: '40%', cursor: 'pointer', zIndex: 10 }}
          onClick={() => handleAction(getImg("admin_panel"))}
        />
      </div>

      {/* Layer 2: Top Frame Overlay (Z-Index: 20) */}
      <img src="/video/frame.png" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'fill', zIndex: 20, pointerEvents: 'none' }} />

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

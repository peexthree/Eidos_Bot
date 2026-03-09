import React from 'react';

const IntroVideo = ({ onComplete }) => {
  return (
    <div className="fixed inset-0 z-[99999] bg-black flex flex-col items-center justify-center">
      <video
        src="/video/LOGO.mp4"
        autoPlay
        muted
        playsInline
        onEnded={onComplete}
        className="w-full h-full object-cover opacity-80"
      />

      <div className="absolute bottom-10 w-full px-8 flex justify-center z-50">
        <button
          onClick={onComplete}
          className="w-full max-w-xs py-2 clip-hex bg-transparent border border-white/10 text-white/30 font-orbitron tracking-widest text-xs hover:bg-white/10 hover:text-white/80 transition-all uppercase"
        >
          [ ПРОПУСТИТЬ ]
        </button>
      </div>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none sys-scanline opacity-10"></div>
    </div>
  );
};

export default IntroVideo;

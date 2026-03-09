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
          className="w-full max-w-xs py-3 clip-hex bg-black/50 border border-eidos-cyan/30 text-eidos-cyan font-orbitron tracking-widest text-sm hover:bg-eidos-cyan/20 hover:border-eidos-cyan transition-all backdrop-blur-md uppercase text-glow-cyan"
        >
          [ ПРОПУСТИТЬ ]
        </button>
      </div>

      <div className="absolute top-0 left-0 w-full h-full pointer-events-none sys-scanline opacity-10"></div>
    </div>
  );
};

export default IntroVideo;

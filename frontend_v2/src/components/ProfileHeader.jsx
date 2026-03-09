import React from 'react';
import useStore from '../store/useStore';

const ProfileHeader = () => {
  const profile = useStore((state) => state.profile);

  return (
    <div className="w-full bg-eidos-glass p-4 border-b border-eidos-cyan/30 clip-hex mb-4">
      <div className="flex items-center space-x-4 mb-4">
        {/* Аватар с clip-hex */}
        <div className="relative w-16 h-16 bg-eidos-cyan/20 clip-hex flex items-center justify-center border border-eidos-cyan">
          <span className="font-orbitron text-xl text-eidos-cyan font-bold">CN</span>
          <div className="absolute -bottom-2 -right-2 bg-eidos-red text-white text-xs px-1 font-share clip-hex font-bold">
            LVL {profile.level}
          </div>
        </div>

        {/* Имя, Фракция, Биокоины */}
        <div className="flex flex-col flex-1">
          <h2 className="font-orbitron text-lg text-eidos-cyan text-glow-cyan uppercase tracking-wider">
            {profile.name}
          </h2>
          <div className="font-share text-xs text-white/70 mb-1">
            FACTION: <span className="text-eidos-neon text-glow-neon">{profile.faction}</span>
          </div>
          <div className="font-share text-sm text-yellow-400 flex items-center">
            <span className="mr-1">◈</span> {profile.biocoins.toLocaleString()} BC
          </div>
        </div>
      </div>

      {/* Сетка статов */}
      <div className="grid grid-cols-4 gap-2 border-t border-white/10 pt-3">
        {/* ATK - Red */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-eidos-red/30">
          <span className="font-share text-[10px] text-eidos-red mb-1">ATK</span>
          <span className="font-rajdhani text-lg text-white font-bold">{profile.stats.atk}</span>
        </div>
        {/* DEF - Blue */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-blue-400/30">
          <span className="font-share text-[10px] text-blue-400 mb-1">DEF</span>
          <span className="font-rajdhani text-lg text-white font-bold">{profile.stats.def}</span>
        </div>
        {/* LCK - Yellow */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-yellow-400/30">
          <span className="font-share text-[10px] text-yellow-400 mb-1">LCK</span>
          <span className="font-rajdhani text-lg text-white font-bold">{profile.stats.luck}</span>
        </div>
        {/* SIGNAL - Neon Green */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-eidos-neon/30">
          <span className="font-share text-[10px] text-eidos-neon mb-1">SIGNAL</span>
          <span className="font-rajdhani text-lg text-white font-bold">{profile.stats.signal}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProfileHeader;

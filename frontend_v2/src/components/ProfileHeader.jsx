import React from 'react';
import useStore from '../store/useStore';

const ProfileHeader = () => {
  const profile = useStore((state) => state.profile);

  return (
    <div className="w-full bg-eidos-glass p-4 border-b border-eidos-cyan/30 clip-hex mb-4">
      <div className="flex items-center space-x-4 mb-4">
        {/* Аватар с clip-hex */}
        <div className="relative w-16 h-16 bg-eidos-cyan/20 clip-hex flex items-center justify-center border border-eidos-cyan">
          {profile?.avatar_url ? (
            <img src={profile.avatar_url} alt="Avatar" className="w-full h-full object-cover clip-hex" />
          ) : (
            <span className="font-orbitron text-xl text-eidos-cyan font-bold">CN</span>
          )}
          <div className="absolute -bottom-2 -right-2 bg-eidos-red text-white text-xs px-1 font-share clip-hex font-bold z-10">
            LVL {profile?.level || 0}
          </div>
        </div>

        {/* Имя, Фракция, Биокоины */}
        <div className="flex flex-col flex-1">
          <h2 className="font-orbitron text-lg text-eidos-cyan text-glow-cyan uppercase tracking-wider">
            {profile?.name || "UNKNOWN"}
          </h2>
          <div className="flex items-center gap-2 mb-1">
             <div className="font-share text-xs text-white/70 flex items-center gap-1">
                <img src="/IMG/eidos_faction-icon.svg" alt="" className="w-3 h-3 opacity-70" onError={(e) => e.target.style.display='none'} />
                FACTION: <span className="text-eidos-neon text-glow-neon">{profile?.faction || "UNKNOWN"}</span>
             </div>
          </div>
          <div className="font-share text-sm text-yellow-400 flex items-center">
            <img src="/IMG/eidos_credits-crypto.svg" alt="BC" className="w-4 h-4 mr-1" />
            {(profile?.biocoins || 0).toLocaleString()} BC
          </div>
        </div>
      </div>

      {/* Сетка статов */}
      <div className="grid grid-cols-4 gap-2 border-t border-white/10 pt-3">
        {/* ATK - Red */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-eidos-red/30">
          <div className="flex items-center space-x-1 mb-1">
            <img src="/IMG/eidos_weapon-attack.svg" alt="ATK" className="w-3 h-3 text-eidos-red" style={{ filter: 'var(--svg-color-red, invert(28%) sepia(85%) saturate(7186%) hue-rotate(352deg) brightness(102%) contrast(106%))' }} />
            <span className="font-share text-[10px] text-eidos-red">ATK</span>
          </div>
          <span className="font-rajdhani text-lg text-white font-bold">{profile?.stats?.atk || profile?.atk || 0}</span>
        </div>
        {/* DEF - Blue */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-blue-400/30">
          <div className="flex items-center space-x-1 mb-1">
            <img src="/IMG/eidos_shield-armor.svg" alt="DEF" className="w-3 h-3 text-blue-400" style={{ filter: 'var(--svg-color-blue, invert(60%) sepia(45%) saturate(4522%) hue-rotate(193deg) brightness(101%) contrast(105%))' }} />
            <span className="font-share text-[10px] text-blue-400">DEF</span>
          </div>
          <span className="font-rajdhani text-lg text-white font-bold">{profile?.stats?.def || profile?.def || 0}</span>
        </div>
        {/* LCK - Yellow */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-yellow-400/30">
          <div className="flex items-center space-x-1 mb-1">
             <img src="/IMG/eidos_luck-dice.svg" alt="LCK" className="w-3 h-3 text-yellow-400" style={{ filter: 'var(--svg-color-yellow, invert(85%) sepia(50%) saturate(1008%) hue-rotate(359deg) brightness(105%) contrast(104%))' }} />
             <span className="font-share text-[10px] text-yellow-400">LCK</span>
          </div>
          <span className="font-rajdhani text-lg text-white font-bold">{profile?.stats?.luck || profile?.luck || 0}</span>
        </div>
        {/* SIGNAL - Neon Green */}
        <div className="flex flex-col items-center justify-center bg-black/40 p-2 clip-hex border border-eidos-neon/30">
          <div className="flex items-center space-x-1 mb-1">
            <img src="/IMG/eidos_signal-wave.svg" alt="SIGNAL" className="w-3 h-3 text-eidos-neon" onError={(e) => { e.target.src='/IMG/eidos_audio-wave.svg' }} style={{ filter: 'var(--svg-color-neon, invert(67%) sepia(61%) saturate(3065%) hue-rotate(85deg) brightness(102%) contrast(110%))' }} />
            <span className="font-share text-[10px] text-eidos-neon">SIGNAL</span>
          </div>
          <span className="font-rajdhani text-lg text-white font-bold">{profile?.stats?.signal || profile?.signal || 0}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProfileHeader;

import React from 'react';
import useStore from '../store/useStore';

const ProfileHeader = () => {
  const profile = useStore((state) => state.profile);

  return (
    <div
      className="relative w-full overflow-hidden"
      style={{
        height: '30vh',
        minHeight: '220px',
        width: '100vw',
        marginLeft: 'calc(-50vw + 50%)', // Break out of container padding to fill width
        marginRight: 'calc(-50vw + 50%)',
        backgroundImage: `url(${profile?.avatar_url || ''})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center center'
      }}
    >
      {/* Dark overlay to make avatar visible but let text pop */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Top gradient for scanline/tech effect */}
      <div className="absolute top-0 left-0 w-full h-1/4 bg-gradient-to-b from-black/80 to-transparent" />

      {/* Bottom overlay with gradient mask for text & stats readability */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black via-black/80 to-transparent pt-12 pb-2 px-2">

        {/* Nickname, Faction, Level area */}
        <div className="flex items-end justify-between mb-3 w-full max-w-2xl mx-auto px-2">
          <div className="flex flex-col">
            <h2 className="font-orbitron text-2xl text-eidos-cyan text-glow-cyan uppercase tracking-wider leading-none">
              {profile?.name || "UNKNOWN"}
            </h2>
            <div className="flex items-center gap-2 mt-1">
               <div className="absolute top-3 right-3 bg-eidos-red text-white text-sm px-2 py-0.5 font-share clip-hex font-bold z-10 shadow-[0_0_10px_rgba(255,51,51,0.5)]">
                 LVL {profile?.level || 0}
               </div>
               <div className="font-share text-xs text-white/70 flex items-center gap-1 bg-black/50 px-2 py-0.5 clip-hex border border-white/10">
                  <img src="/IMG/eidos_faction-icon.svg" alt="" className="w-3 h-3 opacity-70" onError={(e) => e.target.style.display='none'} />
                  FACTION: <span className="text-eidos-neon text-glow-neon">{profile?.faction || "UNKNOWN"}</span>
               </div>
               <div className="font-share text-xs text-yellow-400 flex items-center bg-black/50 px-2 py-0.5 clip-hex border border-yellow-400/20">
                 <img src="/IMG/eidos_credits-crypto.svg" alt="BC" className="w-3 h-3 mr-1" />
                 {(profile?.biocoins || 0).toLocaleString()} BC
               </div>
            </div>
          </div>
        </div>

        {/* Сетка статов */}
        <div className="flex justify-between items-center pt-2 w-full max-w-2xl mx-auto px-2">
          {/* ATK - Red */}
          <div className="flex items-center space-x-1 bg-black/30 px-2 py-1 rounded">
            <img src="/IMG/eidos_weapon-attack.svg" alt="ATK" className="w-3 h-3 text-eidos-red" style={{ filter: 'var(--svg-color-red, invert(28%) sepia(85%) saturate(7186%) hue-rotate(352deg) brightness(102%) contrast(106%))' }} />
            <span className="font-share text-xs text-eidos-red">ATK</span>
            <span className="font-rajdhani text-sm text-white font-bold">{profile?.stats?.atk || profile?.atk || 0}</span>
          </div>
          {/* DEF - Blue */}
          <div className="flex items-center space-x-1 bg-black/30 px-2 py-1 rounded">
            <img src="/IMG/eidos_shield-armor.svg" alt="DEF" className="w-3 h-3 text-blue-400" style={{ filter: 'var(--svg-color-blue, invert(60%) sepia(45%) saturate(4522%) hue-rotate(193deg) brightness(101%) contrast(105%))' }} />
            <span className="font-share text-xs text-blue-400">DEF</span>
            <span className="font-rajdhani text-sm text-white font-bold">{profile?.stats?.def || profile?.def || 0}</span>
          </div>
          {/* LCK - Yellow */}
          <div className="flex items-center space-x-1 bg-black/30 px-2 py-1 rounded">
             <img src="/IMG/eidos_luck-dice.svg" alt="LCK" className="w-3 h-3 text-yellow-400" style={{ filter: 'var(--svg-color-yellow, invert(85%) sepia(50%) saturate(1008%) hue-rotate(359deg) brightness(105%) contrast(104%))' }} />
             <span className="font-share text-xs text-yellow-400">LCK</span>
             <span className="font-rajdhani text-sm text-white font-bold">{profile?.stats?.luck || profile?.luck || 0}</span>
          </div>
          {/* SIGNAL - Neon Green */}
          <div className="flex items-center space-x-1 bg-black/30 px-2 py-1 rounded">
            <img src="/IMG/eidos_signal-wave.svg" alt="SIGNAL" className="w-3 h-3 text-eidos-neon" onError={(e) => { e.target.src='/IMG/eidos_audio-wave.svg' }} style={{ filter: 'var(--svg-color-neon, invert(67%) sepia(61%) saturate(3065%) hue-rotate(85deg) brightness(102%) contrast(110%))' }} />
            <span className="font-share text-xs text-eidos-neon">SIG</span>
            <span className="font-rajdhani text-sm text-white font-bold">{profile?.stats?.signal || profile?.signal || 0}%</span>
          </div>
        </div>
      </div>

      {/* Cyberpunk accent lines overlay */}
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-eidos-cyan/50" />
      <div className="absolute top-0 left-0 w-full h-[2px] bg-eidos-cyan/20" />
    </div>
  );
};

export default ProfileHeader;

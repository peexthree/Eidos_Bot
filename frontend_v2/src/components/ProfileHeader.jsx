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
      {/* Top gradient for scanline/tech effect */}
      <div className="absolute top-0 left-0 w-full h-1/4 bg-gradient-to-b from-black/80 to-transparent" />

      {/* Bottom gradient mask for tech lines readability */}
      <div className="absolute bottom-0 left-0 w-full h-1/4 bg-gradient-to-t from-black via-black/80 to-transparent" />

      {/* Top-Left Cluster: Name, Faction, Level, BioCoins */}
      <div className="absolute top-3 left-3 flex flex-col items-start gap-1">
        <div className="bg-black/50 backdrop-blur-sm px-3 py-1 clip-hex border border-white/10">
          <h2 className="font-orbitron text-lg md:text-xl text-eidos-cyan text-glow-cyan uppercase tracking-wider leading-none">
            {profile?.name || "UNKNOWN"}
          </h2>
        </div>

        <div className="flex gap-2">
          <div className="bg-eidos-red text-white text-xs px-2 py-0.5 font-share clip-hex font-bold shadow-[0_0_10px_rgba(255,51,51,0.5)]">
            LVL {profile?.level || 0}
          </div>

          <div className="font-share text-[10px] md:text-xs text-white/70 flex items-center gap-1 bg-black/50 backdrop-blur-sm px-2 py-0.5 clip-hex border border-white/10">
            <img src="/IMG/eidos_faction-icon.svg" alt="" className="w-2.5 h-2.5 opacity-70" onError={(e) => e.target.style.display='none'} />
            <span className="text-eidos-neon text-glow-neon">{profile?.faction || "UNKNOWN"}</span>
          </div>
        </div>

        <div className="font-share text-[10px] md:text-xs text-yellow-400 flex items-center bg-black/50 backdrop-blur-sm px-2 py-0.5 mt-1 clip-hex border border-yellow-400/20">
          <img src="/IMG/eidos_credits-crypto.svg" alt="BC" className="w-2.5 h-2.5 mr-1" />
          {(profile?.biocoins || 0).toLocaleString()} BC
        </div>
      </div>

      {/* Bottom-Right Compact Stats HUD */}
      <div className="absolute bottom-3 right-3 grid grid-cols-2 gap-1 bg-black/50 backdrop-blur-sm p-1.5 rounded-sm border border-white/10">
        {/* ATK - Red */}
        <div className="flex items-center justify-between space-x-1.5 px-1.5 py-0.5">
          <div className="flex items-center space-x-1">
            <img src="/IMG/eidos_weapon-attack.svg" alt="ATK" className="w-2.5 h-2.5 text-eidos-red" style={{ filter: 'var(--svg-color-red, invert(28%) sepia(85%) saturate(7186%) hue-rotate(352deg) brightness(102%) contrast(106%))' }} />
            <span className="font-share text-[10px] text-eidos-red">ATK</span>
          </div>
          <span className="font-rajdhani text-xs text-white font-bold">{profile?.stats?.atk || profile?.atk || 0}</span>
        </div>

        {/* DEF - Blue */}
        <div className="flex items-center justify-between space-x-1.5 px-1.5 py-0.5">
          <div className="flex items-center space-x-1">
            <img src="/IMG/eidos_shield-armor.svg" alt="DEF" className="w-2.5 h-2.5 text-blue-400" style={{ filter: 'var(--svg-color-blue, invert(60%) sepia(45%) saturate(4522%) hue-rotate(193deg) brightness(101%) contrast(105%))' }} />
            <span className="font-share text-[10px] text-blue-400">DEF</span>
          </div>
          <span className="font-rajdhani text-xs text-white font-bold">{profile?.stats?.def || profile?.def || 0}</span>
        </div>

        {/* LCK - Yellow */}
        <div className="flex items-center justify-between space-x-1.5 px-1.5 py-0.5">
          <div className="flex items-center space-x-1">
             <img src="/IMG/eidos_luck-dice.svg" alt="LCK" className="w-2.5 h-2.5 text-yellow-400" style={{ filter: 'var(--svg-color-yellow, invert(85%) sepia(50%) saturate(1008%) hue-rotate(359deg) brightness(105%) contrast(104%))' }} />
             <span className="font-share text-[10px] text-yellow-400">LCK</span>
          </div>
          <span className="font-rajdhani text-xs text-white font-bold">{profile?.stats?.luck || profile?.luck || 0}</span>
        </div>

        {/* SIGNAL - Neon Green */}
        <div className="flex items-center justify-between space-x-1.5 px-1.5 py-0.5">
          <div className="flex items-center space-x-1">
            <img src="/IMG/eidos_signal-wave.svg" alt="SIGNAL" className="w-2.5 h-2.5 text-eidos-neon" onError={(e) => { e.target.src='/IMG/eidos_audio-wave.svg' }} style={{ filter: 'var(--svg-color-neon, invert(67%) sepia(61%) saturate(3065%) hue-rotate(85deg) brightness(102%) contrast(110%))' }} />
            <span className="font-share text-[10px] text-eidos-neon">SIG</span>
          </div>
          <span className="font-rajdhani text-xs text-white font-bold">{profile?.stats?.signal || profile?.signal || 0}%</span>
        </div>
      </div>

      {/* Cyberpunk accent lines overlay */}
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-eidos-cyan/50" />
      <div className="absolute top-0 left-0 w-full h-[2px] bg-eidos-cyan/20" />
    </div>
  );
};

export default ProfileHeader;

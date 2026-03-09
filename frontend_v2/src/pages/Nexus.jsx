import React from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'wouter';

// Компонент NexusTile (Плитка хаба)
// Использует glassmorphism (bg-glass), кастомную обрезку углов (clip-hex)
// и Framer Motion для микро-анимаций при наведении/нажатии.
const NexusTile = ({ title, desc, icon, route }) => {
  const [, setLocation] = useLocation();

  return (
    <motion.button
      onClick={() => setLocation(route)}
      className="flex flex-col items-start justify-center p-4 h-32 w-full text-left bg-glass clip-hex border border-[var(--color-eidos-cyan)]/30 hover:border-[var(--color-eidos-neon)]/60 transition-colors shadow-[0_0_15px_rgba(102,252,241,0.05)] hover:shadow-[0_0_20px_rgba(0,255,65,0.2)]"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.95 }}
    >
      <div className="flex items-center gap-2 mb-2 w-full">
        {/* Иконка плитки (шрифт/SVG). Если используются SVG из /src/assets - подгружать их. */}
        <span className="text-2xl text-[var(--color-eidos-cyan)]">{icon}</span>
        <h3 className="font-orbitron font-bold text-lg text-white tracking-widest leading-none truncate w-full">
          {title}
        </h3>
      </div>
      <p className="font-share text-xs text-white/60 leading-tight">
        {desc}
      </p>
    </motion.button>
  );
};

// Главный компонент Nexus
// Это стартовый хаб EIDOS OS.
export default function Nexus() {
  // Анимация появления контейнера грида
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1, // Каскадное появление плиток
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="flex flex-col items-center justify-start w-full">
      {/* Заголовок хаба */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full text-center mb-8 border-b border-[var(--color-eidos-cyan)]/30 pb-4 relative"
      >
        {/* Декоративный скан-лайн под заголовком */}
        <div className="absolute bottom-0 left-[10%] right-[10%] h-[1px] bg-gradient-to-r from-transparent via-[var(--color-eidos-neon)] to-transparent opacity-50 shadow-[0_0_5px_var(--color-eidos-neon)]" />

        <h1 className="text-3xl font-orbitron font-black text-[var(--color-eidos-neon)] text-glow-neon uppercase">
          NEXUS.GRID
        </h1>
        <p className="font-share text-[var(--color-eidos-cyan)]/70 text-sm tracking-widest mt-1 uppercase text-glow-cyan animate-pulse">
          /// SYNCHRONIZED ///
        </p>
      </motion.div>

      {/*
        Сетка хаба (CSS Grid, 2 колонки, адаптивный gap).
        Используется w-full, чтобы растянуть сетку на доступную ширину контейнера (max-w-2xl).
      */}
      <motion.div
        className="grid grid-cols-2 gap-4 w-full"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={itemVariants}>
          <NexusTile
            title="PROFILE"
            desc="STATUS // BIO"
            icon="■"
            route="/profile"
          />
        </motion.div>

        <motion.div variants={itemVariants}>
          <NexusTile
            title="GEAR"
            desc="EQUIP // MODS"
            icon="▲"
            route="/inventory"
          />
        </motion.div>

        <motion.div variants={itemVariants}>
          <NexusTile
            title="MARKET"
            desc="TRADE // CREDITS"
            icon="●"
            route="/shop"
          />
        </motion.div>

        <motion.div variants={itemVariants}>
          <NexusTile
            title="ARENA"
            desc="COMBAT // PVP"
            icon="X"
            route="/arena"
          />
        </motion.div>

        <motion.div variants={itemVariants} className="col-span-2">
          {/* Плитка Райдов занимает 2 колонки */}
          <NexusTile
            title="RAIDS"
            desc="MISSIONS // LOOT // CO-OP"
            icon="▼"
            route="/raids"
          />
        </motion.div>
      </motion.div>

      {/* Терминальная заглушка снизу для атмосферы */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-8 p-3 w-full bg-black/50 border border-[var(--color-eidos-cyan)]/20 font-share text-xs text-white/40"
      >
        {">"} INIT LOAD... OK.<br />
        {">"} CHECKING CONNECTION TO CORE... STABLE.<br />
        {">"} AWAITING OPERATOR INPUT_
        <span className="inline-block w-[6px] h-[12px] bg-[var(--color-eidos-cyan)]/50 ml-1 animate-ping" />
      </motion.div>
    </div>
  );
}

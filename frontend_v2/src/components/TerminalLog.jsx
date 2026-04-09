import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import useStore from '../store/useStore';

const TerminalLog = () => {
  const terminalLogs = useStore((state) => state.terminalLogs);

  return (
    <div className="fixed top-4 left-4 right-4 z-[999999] pointer-events-none flex flex-col gap-2 font-share">
      <AnimatePresence>
        {terminalLogs.map((log) => (
          <motion.div
            key={log.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-black/80 border-l-4 border-eidos-neon text-eidos-neon p-2 text-sm shadow-[0_0_10px_rgba(0,255,65,0.2)] uppercase tracking-wider clip-hex backdrop-blur-sm"
          >
            &gt; {log.msg}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default TerminalLog;

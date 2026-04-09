import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { eidosApi } from '../api/client';
import useStore from '../store/useStore';

const ShopModal = ({ onClose }) => {
  const [error, setError] = useState(null);
  const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
  const fetchProfile = useStore((state) => state.fetchProfile);
  const profile = useStore((state) => state.profile);

  const buyMutation = useMutation({
    mutationFn: (itemId) => eidosApi.post('/shop/buy', { uid, item_id: itemId }),
    onSuccess: () => {
      fetchProfile(uid);
      onClose();
    },
    onError: (err) => {
      setError(err?.response?.data?.error || 'Транзакция отклонена');
      fetchProfile(uid);
    }
  });

  const handleBuy = () => {
    buyMutation.mutate('basic_medkit'); // Пример
  };

  return (
    <div className="fixed inset-0 z-[90000] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="relative w-full max-w-sm bg-eidos-bg/90 border border-eidos-cyan/50 p-6 clip-hex"
      >
        <h2 className="text-xl text-eidos-cyan font-orbitron mb-4 uppercase text-center">Теневой Рынок</h2>

        <div className="mb-4 text-center">
            <span className="text-white/70">Баланс: {profile?.stats?.coins || 0} BC</span>
        </div>

        {error && <div className="text-red-500 text-center mb-4 text-sm">{error}</div>}

        <button
          className="w-full py-3 bg-eidos-cyan/20 border border-eidos-cyan text-eidos-cyan font-orbitron uppercase tracking-widest hover:bg-eidos-cyan/40 transition-colors"
          onClick={handleBuy}
          disabled={buyMutation.isLoading}
        >
          {buyMutation.isLoading ? 'ОБРАБОТКА...' : 'КУПИТЬ АПТЕЧКУ (500 BC)'}
        </button>

        <button
          className="mt-4 w-full py-2 bg-red-500/20 border border-red-500 text-red-500 font-orbitron uppercase tracking-widest hover:bg-red-500/40 transition-colors"
          onClick={onClose}
        >
          ЗАКРЫТЬ
        </button>
      </motion.div>
    </div>
  );
};

export default ShopModal;

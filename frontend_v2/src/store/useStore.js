import { create } from 'zustand';
import axios from 'axios';

const useStore = create((set) => ({
  profile: {
    name: "CYBER_NOMAD",
    level: 0,
    faction: "UNKNOWN",
    biocoins: 0,
    stats: {
      atk: 0,
      def: 0,
      luck: 0,
      signal: 0
    }
  },
  inventory: [],
  equipped: {
    head: null,
    body: null,
    weapon: null,
    software: null,
    artifact: null
  },
  // Actions
  fetchProfile: async (uid) => {
    try {
      const response = await axios.get('/api/inventory', { params: { uid } });
      const data = response.data;

      set({
        profile: data.profile || {
          name: data.name || data.player?.name || "UNKNOWN",
          level: data.level || data.player?.level || 0,
          faction: data.faction || data.player?.faction || "UNKNOWN",
          biocoins: data.biocoins || data.player?.biocoins || data.balance || 0,
          stats: data.stats || data.player?.stats || { atk: 0, def: 0, luck: 0, signal: 0 }
        },
        inventory: data.inventory || data.items || [],
        equipped: data.equipped || { head: null, body: null, weapon: null, software: null, artifact: null }
      });
    } catch (error) {
      console.error("Error fetching profile:", error);
    }
  },

  equipItem: (slot, itemId) => set((state) => ({
    equipped: { ...state.equipped, [slot]: itemId }
  })),
  unequipItem: (slot) => set((state) => ({
    equipped: { ...state.equipped, [slot]: null }
  }))
}));

export default useStore;

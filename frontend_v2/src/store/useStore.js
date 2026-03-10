import { create } from 'zustand';
import axios from 'axios';

const useStore = create((set) => ({
  isLoading: true,
  profile: null, // Initially null to enforce the loading screen
  inventory: [],
  equipped: {
    head: null,
    armor: null,
    weapon: null,
    chip: null,
    eidos_shard: null
  },
  // Actions
  fetchProfile: async (uid) => {
    try {
      set({ isLoading: true });
      const response = await axios.get('/api/inventory', { params: { uid } });
      const data = response.data;

      set({
        isLoading: false,
        profile: data.profile || {
          name: data.name || data.player?.name || "UNKNOWN",
          level: data.level || data.player?.level || 0,
          faction: data.faction || data.player?.faction || "UNKNOWN",
          biocoins: data.biocoins || data.player?.biocoins || data.balance || 0,
          stats: data.stats || data.player?.stats || { atk: 0, def: 0, luck: 0, signal: 0 }
        },
        inventory: data.inventory || data.items || [],
        equipped: data.equipped || { head: null, armor: null, weapon: null, chip: null, eidos_shard: null }
      });
    } catch (error) {
      console.error("Error fetching profile:", error);
      set({ isLoading: false }); // To ensure we don't get stuck, though profile will remain null and show loader
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

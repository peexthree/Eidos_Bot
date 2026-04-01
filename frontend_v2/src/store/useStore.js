import { create } from 'zustand';
import { eidosApi as axios } from '../api/client';

const useStore = create((set, get) => ({
  profile: null,
  inventory: [],
  equipped: { head: null, armor: null, weapon: null, chip: null, eidos_shard: null },
  isLoading: true,
  currentView: 'HUB', // HUB, INVENTORY, RAID, SHOP, SOCIAL, PROFILE
  raidData: null,
  shopData: null,

  setCurrentView: (view) => set({ currentView: view }),

  fetchProfile: async (uid) => {
    try {
      set({ isLoading: true });

      const response = await axios.get('/inventory', { params: { uid } });
      const data = response;

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
        equipped: data.equipped ? {
            head: data.equipped.head || null,
            armor: data.equipped.armor || data.equipped.body || null,
            weapon: data.equipped.weapon || null,
            chip: data.equipped.chip || data.equipped.software || null,
            eidos_shard: data.equipped.eidos_shard || data.equipped.artifact || null
        } : { head: null, armor: null, weapon: null, chip: null, eidos_shard: null }
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
      set({ isLoading: false });
    }
  },


  optimisticEquip: (item, slotName) => {
    set((state) => {
      const newEquipped = { ...state.equipped };
      const currentItemInSlot = newEquipped[slotName];

      let newInventory = [...state.inventory];

      // If equipping an item, we typically keep it in the inventory array as per backend logic,
      // but we need to mark it equipped in the equipped object.
      newEquipped[slotName] = item;

      return { equipped: newEquipped };
    });
  },

  optimisticUnequip: (slotName) => {
    set((state) => {
      const newEquipped = { ...state.equipped };
      newEquipped[slotName] = null;
      return { equipped: newEquipped };
    });
  },

  optimisticDismantle: (itemId) => {
    set((state) => {
      const newInventory = state.inventory.filter((i) => i.id !== itemId && i.item_id !== itemId);
      return { inventory: newInventory };
    });
  },

  revertOptimistic: (prevEquipped, prevInventory) => {
    set({ equipped: prevEquipped, inventory: prevInventory });
  },

  fetchRaidData: async (uid) => {
    try {
        const response = await axios.get('/hub_data', { params: { uid } });
        set({ raidData: response.raids || [] });
    } catch (e) {
        console.error(e);
    }
  }
}));

export default useStore;

const fs = require('fs');
const file = 'frontend_v2/src/store/useStore.js';
let content = fs.readFileSync(file, 'utf8');

// Find the fetchRaidData function to append after it
const splitContent = content.split('  fetchRaidData: async (uid) => {');
const preContent = splitContent[0];
const postContent = '  fetchRaidData: async (uid) => {' + splitContent[1];

const newMethods = `
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

`;

fs.writeFileSync(file, preContent + newMethods + postContent);
console.log("Patched useStore.js");

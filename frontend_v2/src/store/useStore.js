import { create } from 'zustand';

const useStore = create((set) => ({
  profile: {
    name: "CYBER_NOMAD",
    level: 42,
    faction: "NEON_SYNDICATE",
    biocoins: 1337,
    stats: {
      atk: 150,
      def: 80,
      luck: 15,
      signal: 100
    }
  },
  inventory: [
    { id: 1, name: "Neural Implant v2", type: "Software", rarity: "rare", stats: { def: 10 } },
    { id: 2, name: "Plasma Cutter", type: "Weapon", rarity: "epic", stats: { atk: 55 } },
    { id: 3, name: "Scrap Metal", type: "Consumable", rarity: "common", amount: 5 },
    { id: 4, name: "Quantum Processor", type: "Artifact", rarity: "legendary", stats: { luck: 25, signal: 10 } },
    { id: 5, name: "Kevlar Vest", type: "Body", rarity: "common", stats: { def: 20 } },
    { id: 6, name: "Optic Sensor", type: "Head", rarity: "rare", stats: { signal: 5 } },
    { id: 7, name: "Energy Drink", type: "Consumable", rarity: "common", amount: 12 }
  ],
  equipped: {
    head: 6,
    body: 5,
    weapon: 2,
    software: 1,
    artifact: null
  },
  // Actions
  equipItem: (slot, itemId) => set((state) => ({
    equipped: { ...state.equipped, [slot]: itemId }
  })),
  unequipItem: (slot) => set((state) => ({
    equipped: { ...state.equipped, [slot]: null }
  }))
}));

export default useStore;

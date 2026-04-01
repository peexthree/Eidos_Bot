const fs = require('fs');
const file = 'frontend_v2/src/components/ItemModal.jsx';
let content = fs.readFileSync(file, 'utf8');

content = content.replace("import React, { useEffect, useState } from 'react';", "import React, { useEffect, useState } from 'react';\nimport { useMutation } from '@tanstack/react-query';\nimport HoldToEquip from './actions/HoldToEquip';\nimport DragToDismantle from './actions/DragToDismantle';");

const fetchProfileStr = "const fetchProfile = useStore((state) => state.fetchProfile);";
const extractStoreStr = `  const fetchProfile = useStore((state) => state.fetchProfile);
  const optimisticEquip = useStore((state) => state.optimisticEquip);
  const optimisticUnequip = useStore((state) => state.optimisticUnequip);
  const optimisticDismantle = useStore((state) => state.optimisticDismantle);
  const revertOptimistic = useStore((state) => state.revertOptimistic);
  const inventory = useStore((state) => state.inventory);
`;
content = content.replace(fetchProfileStr, extractStoreStr);

const actionFunctionsOld = `  const handleDismantle = async () => {
    setIsLoading(true);
    try {
      let uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
      // The backend uses string ids or internal ids, try the default item_id from DB
      await axios.post('/api/inventory/dismantle', { uid, inv_id: item.id });
      if (uid) await fetchProfile(uid);
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEquipToggle = async (action) => {
    setIsLoading(true);
    try {
      let uid;
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
          uid = window.Telegram.WebApp.initDataUnsafe.user.id;
      } else {
          const urlParams = new URLSearchParams(window.location.search);
          uid = urlParams.get('uid');
      }

      // API mapping for unequip slot.
      // API expects: head, weapon, body, software, artifact
      const apiSlotMap = {
          'armor': 'body',
          'chip': 'software',
          'eidos_shard': 'artifact'
      };

      if (action === 'unequip' || isEquipped) {
        let slotToUnequip = null;
        for (const [slot, val] of Object.entries(equipped)) {
           if (val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))) {
              slotToUnequip = slot;
              break;
           }
        }

        if (slotToUnequip) {
          const apiSlot = apiSlotMap[slotToUnequip] || slotToUnequip;
          await axios.post('/api/inventory/unequip', { uid: uid, slot: apiSlot });
        }
      } else {
        await axios.post('/api/inventory/equip', { uid: uid, item_id: itemId });
      }

      // Immediately fetch updated profile
      if (uid) {
         await fetchProfile(uid);
      }
      onClose();
    } catch (error) {
      console.error("Action error:", error);
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.showAlert("Ошибка при выполнении действия");
      }
    } finally {
      setIsLoading(false);
    }
  };`;

const actionFunctionsNew = `  // API mapping for unequip slot.
  const apiSlotMap = {
      'armor': 'body',
      'chip': 'software',
      'eidos_shard': 'artifact'
  };

  const equipMutation = useMutation({
    mutationFn: async ({ uid, itemId }) => {
      return axios.post('/api/inventory/equip', { uid, item_id: itemId });
    },
    onMutate: async ({ itemId }) => {
      const prevEquipped = { ...equipped };
      const prevInventory = [...inventory];
      const targetSlot = Object.keys(apiSlotMap).find(k => apiSlotMap[k] === item.type) || item.type;
      optimisticEquip(item, targetSlot);
      return { prevEquipped, prevInventory };
    },
    onError: (err, variables, context) => {
      console.error("Equip error:", err);
      revertOptimistic(context.prevEquipped, context.prevInventory);
      if (window.Telegram?.WebApp) window.Telegram.WebApp.showAlert("Ошибка при экипировке");
    },
    onSettled: () => {
       const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
       if (uid) fetchProfile(uid);
       onClose();
    }
  });

  const unequipMutation = useMutation({
    mutationFn: async ({ uid, slot }) => {
      return axios.post('/api/inventory/unequip', { uid, slot });
    },
    onMutate: async ({ slotToUnequip }) => {
      const prevEquipped = { ...equipped };
      const prevInventory = [...inventory];
      optimisticUnequip(slotToUnequip);
      return { prevEquipped, prevInventory };
    },
    onError: (err, variables, context) => {
      console.error("Unequip error:", err);
      revertOptimistic(context.prevEquipped, context.prevInventory);
      if (window.Telegram?.WebApp) window.Telegram.WebApp.showAlert("Ошибка при снятии");
    },
    onSettled: () => {
       const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
       if (uid) fetchProfile(uid);
       onClose();
    }
  });

  const dismantleMutation = useMutation({
    mutationFn: async ({ uid, invId }) => {
      return axios.post('/api/inventory/dismantle', { uid, inv_id: invId });
    },
    onMutate: async () => {
      const prevEquipped = { ...equipped };
      const prevInventory = [...inventory];
      optimisticDismantle(item.id);
      return { prevEquipped, prevInventory };
    },
    onError: (err, variables, context) => {
      console.error("Dismantle error:", err);
      revertOptimistic(context.prevEquipped, context.prevInventory);
      if (window.Telegram?.WebApp) window.Telegram.WebApp.showAlert("Ошибка при разборе");
    },
    onSettled: () => {
       const uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
       if (uid) fetchProfile(uid);
       onClose();
    }
  });

  const handleDismantle = () => {
    let uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');
    dismantleMutation.mutate({ uid, invId: item.id });
  };

  const handleEquipToggle = (action) => {
    let uid = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get('uid');

    if (action === 'unequip' || isEquipped) {
      let slotToUnequip = null;
      for (const [slot, val] of Object.entries(equipped)) {
         if (val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))) {
            slotToUnequip = slot;
            break;
         }
      }

      if (slotToUnequip) {
        const apiSlot = apiSlotMap[slotToUnequip] || slotToUnequip;
        unequipMutation.mutate({ uid, slot: apiSlot, slotToUnequip });
      }
    } else {
      equipMutation.mutate({ uid, itemId });
    }
  };
`;

content = content.replace(actionFunctionsOld, actionFunctionsNew);


const actionsUIOld = `              {/* Действия */}
              <div className="w-full flex justify-between gap-2 mt-2 px-2">
                {item.type !== 'Consumable' && item.type !== 'consumable' && item.type !== 'misc' && !isEquipped && (
                  <button
                     onClick={() => handleEquipToggle('equip')}
                     disabled={isLoading}
                     className={\`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-eidos-cyan/20 text-eidos-cyan border-eidos-cyan hover:bg-eidos-cyan/40 \${isLoading ? 'opacity-50 cursor-not-allowed' : ''}\`}
                  >
                     [ НАДЕТЬ ]
                  </button>
                )}
                {isEquipped && (
                  <button
                     onClick={() => handleEquipToggle('unequip')}
                     disabled={isLoading}
                     className={\`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-eidos-red/20 text-eidos-red border-eidos-red hover:bg-eidos-red/40 \${isLoading ? 'opacity-50 cursor-not-allowed' : ''}\`}
                  >
                     [ СНЯТЬ ]
                  </button>
                )}

                <button
                   onClick={handleDismantle}
                   disabled={isLoading || isEquipped}
                   className={\`flex-1 font-orbitron font-bold text-sm py-3 clip-hex border transition-all bg-yellow-400/20 text-yellow-400 border-yellow-400 hover:bg-yellow-400/40 \${isLoading || isEquipped ? 'opacity-50 cursor-not-allowed' : ''}\`}
                >
                   [ РАЗОБРАТЬ ]
                </button>
              </div>`;

const actionsUINew = `              {/* Действия */}
              <div className="w-full flex flex-col items-center gap-4 mt-2 px-2">
                {item.type !== 'Consumable' && item.type !== 'consumable' && item.type !== 'misc' && !isEquipped && (
                  <HoldToEquip onEquip={() => handleEquipToggle('equip')} text="НАДЕТЬ" baseColor="eidos-cyan" activeColor="eidos-cyan" />
                )}
                {isEquipped && (
                  <HoldToEquip onEquip={() => handleEquipToggle('unequip')} text="СНЯТЬ" baseColor="eidos-red" activeColor="eidos-red" />
                )}
                {!isEquipped && (
                  <DragToDismantle onDismantle={handleDismantle} />
                )}
              </div>`;

content = content.replace(actionsUIOld, actionsUINew);

fs.writeFileSync(file, content);
console.log("Patched ItemModal.jsx");

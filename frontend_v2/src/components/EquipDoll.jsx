import React, { useEffect } from 'react';
import useStore from '../store/useStore';

const EquipDoll = ({ onSlotClick }) => {
  const equipped = useStore((state) => state.equipped) || {};
  const inventory = useStore((state) => state.inventory) || [];

  useEffect(() => {
     console.log("/// EIDOS: Doll Equipped Data:", equipped);
  }, [equipped]);

  const getItem = (slotData) => {
    if (!slotData) return undefined;

    if (typeof slotData === 'object' && (slotData.image_url || slotData.name)) {
        return slotData;
    }

    let targetId = slotData;
    if (typeof slotData === 'object' && slotData.item_id) {
       targetId = slotData.item_id;
    } else if (typeof slotData === 'object' && slotData.id) {
       targetId = slotData.id;
    }

    return inventory.find(i => String(i?.id) === String(targetId));
  };

  const headItem = getItem(equipped?.head);
  const weaponItem = getItem(equipped?.weapon);
  const chipItem = getItem(equipped?.chip);
  const armorItem = getItem(equipped?.armor);
  const eidosShardItem = getItem(equipped?.eidos_shard);

  return (
    <div className="w-full mb-6 mt-4" style={{ position: 'sticky', top: 0, zIndex: 50, backgroundColor: '#000', width: '100%', aspectRatio: '16/9', overflow: 'hidden' }}>
      <video src="/video/DOLL.mp4" autoPlay loop muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', top: 0, left: 0, zIndex: 0 }} />

      {/* Head */}
      {headItem && <img src={`/api/image/${headItem.file_id}`} alt="Head" style={{ position: 'absolute', top: '10%', left: '40%', width: '20%', height: '30%', objectFit: 'contain', zIndex: 10, cursor: 'pointer' }} onClick={() => onSlotClick(headItem)} />}

      {/* Weapon */}
      {weaponItem && <img src={`/api/image/${weaponItem.file_id}`} alt="Weapon" style={{ position: 'absolute', top: '35%', left: '5%', width: '22%', height: '35%', objectFit: 'contain', zIndex: 10, cursor: 'pointer' }} onClick={() => onSlotClick(weaponItem)} />}

      {/* Chip */}
      {chipItem && <img src={`/api/image/${chipItem.file_id}`} alt="Chip" style={{ position: 'absolute', top: '35%', left: '73%', width: '22%', height: '35%', objectFit: 'contain', zIndex: 10, cursor: 'pointer' }} onClick={() => onSlotClick(chipItem)} />}

      {/* Armor */}
      {armorItem && <img src={`/api/image/${armorItem.file_id}`} alt="Armor" style={{ position: 'absolute', top: '65%', left: '30%', width: '18%', height: '30%', objectFit: 'contain', zIndex: 10, cursor: 'pointer' }} onClick={() => onSlotClick(armorItem)} />}

      {/* Eidos Shard */}
      {eidosShardItem && <img src={`/api/image/${eidosShardItem.file_id}`} alt="Eidos Shard" style={{ position: 'absolute', top: '65%', left: '52%', width: '18%', height: '30%', objectFit: 'contain', zIndex: 10, cursor: 'pointer' }} onClick={() => onSlotClick(eidosShardItem)} />}
    </div>
  );
};

export default EquipDoll;

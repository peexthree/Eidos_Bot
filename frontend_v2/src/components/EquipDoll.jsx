import React, { useEffect } from 'react';
import useStore from '../store/useStore';

const EquipSlot = ({ label, slot, item, onClick, style }) => {
  const unequipItem = useStore((state) => state.unequipItem);

  const handleClick = () => {
    if (onClick && item) {
       onClick(item);
    } else if (item) {
       unequipItem(slot);
    }
  };

  const isEmpty = !item;

  if (isEmpty) {
    return null;
  }

  return (
    <div
      onClick={handleClick}
      style={style}
    >
      <img
        src={item?.image_url || ('/api/image/' + item?.file_id)}
        alt={item?.name || 'Item'}
        style={{ width: '100%', height: '100%', objectFit: 'contain', cursor: 'pointer' }}
      />
    </div>
  );
};

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

  return (
    <div className="w-full relative overflow-hidden mb-6 mt-4" style={{ position: 'relative', width: '100%', aspectRatio: '16/9', overflow: 'hidden' }}>
      <video src="/video/DOLL.mp4" autoPlay loop muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', top: 0, left: 0, zIndex: 0 }} />

      <EquipSlot label="HEAD" slot="head" item={getItem(equipped?.head)} onClick={onSlotClick} style={{ position: 'absolute', top: '10%', left: '40%', width: '20%', height: '30%', zIndex: 10 }} />
      <EquipSlot label="WEAPON" slot="weapon" item={getItem(equipped?.weapon)} onClick={onSlotClick} style={{ position: 'absolute', top: '35%', left: '5%', width: '22%', height: '35%', zIndex: 10 }} />
      <EquipSlot label="ARMOR" slot="armor" item={getItem(equipped?.armor)} onClick={onSlotClick} style={{ position: 'absolute', top: '65%', left: '30%', width: '18%', height: '30%', zIndex: 10 }} />
      <EquipSlot label="SHARD" slot="eidos_shard" item={getItem(equipped?.eidos_shard)} onClick={onSlotClick} style={{ position: 'absolute', top: '65%', left: '52%', width: '18%', height: '30%', zIndex: 10 }} />
      <EquipSlot label="CHIP" slot="chip" item={getItem(equipped?.chip)} onClick={onSlotClick} style={{ position: 'absolute', top: '35%', left: '73%', width: '22%', height: '35%', zIndex: 10 }} />
    </div>
  );
};

export default EquipDoll;

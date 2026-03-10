import React, { useState } from 'react';
import useStore from '../store/useStore';
import ProfileHeader from '../components/ProfileHeader';
import EquipDoll from '../components/EquipDoll';
import ItemList from '../components/ItemList';
import ItemModal from '../components/ItemModal';

const Inventory = () => {
  const [selectedItem, setSelectedItem] = useState(null);

  const handleOpenModal = (item) => {
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  return (
    <div className="flex flex-col h-full w-full">
      <ProfileHeader />
      <EquipDoll onSlotClick={handleOpenModal} />
      <ItemList onItemClick={handleOpenModal} />
      <ItemModal
         isOpen={!!selectedItem}
         onClose={handleCloseModal}
         item={selectedItem}
      />
    </div>
  );
};

export default Inventory;

import React, { useState } from 'react';
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
    <div className="flex flex-col w-full px-4 py-6" style={{ width: "100%", maxWidth: "100vw", overflowY: "auto", height: "100vh", overflowX: "hidden", boxSizing: "border-box" }}>
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

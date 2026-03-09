import React from 'react';
import useStore from '../store/useStore';
import ProfileHeader from '../components/ProfileHeader';
import EquipDoll from '../components/EquipDoll';
import ItemList from '../components/ItemList';
import ItemModal from '../components/ItemModal';

const Inventory = () => {
  return (
    <div className="flex flex-col h-full w-full">
      <ProfileHeader />
      <EquipDoll />
      <ItemList />
      <ItemModal />
    </div>
  );
};

export default Inventory;

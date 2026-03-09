import React from 'react';
import ProfileHeader from '../components/ProfileHeader';
import EquipDoll from '../components/EquipDoll';
import ItemList from '../components/ItemList';

const Inventory = () => {
  return (
    <div className="flex flex-col h-full w-full max-w-lg mx-auto p-4 space-y-4 pt-[90px] pb-[20px] scroll-area overflow-y-auto">
      {/*
        Container constraints from AGENTS.md:
        "WebApp Layout Constraints: .views-container must maintain padding-top: 90px and padding-bottom: 20px"
        We assume this container might be within .views-container or acts as one.
        So padding is applied here to match constraints.
      */}
      <ProfileHeader />
      <EquipDoll />
      <div className="flex-1 min-h-[300px]">
        <ItemList />
      </div>
    </div>
  );
};

export default Inventory;

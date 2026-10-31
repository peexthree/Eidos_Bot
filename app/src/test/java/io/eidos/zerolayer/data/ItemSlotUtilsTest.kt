package io.eidos.zerolayer.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ItemSlotUtilsTest {

    @Test
    fun testResolvesSlotByMetadataType() {
        val weapon = ItemMetadata(id = "custom_gun", name = "Пушка", type = "weapon", rarity = "common")
        val armor = ItemMetadata(id = "custom_vest", name = "Жилет", type = "armor", rarity = "common")
        val head = ItemMetadata(id = "custom_helmet", name = "Шлем", type = "head", rarity = "common")
        val chip = ItemMetadata(id = "custom_chip", name = "Модуль", type = "chip", rarity = "common")
        val medkit = ItemMetadata(id = "medkit", name = "Аптечка", type = "consumable", rarity = "common")

        assertEquals("weapon", ItemSlotUtils.getSlotForItem(weapon.id, weapon))
        assertEquals("armor", ItemSlotUtils.getSlotForItem(armor.id, armor))
        assertEquals("head", ItemSlotUtils.getSlotForItem(head.id, head))
        assertEquals("chip", ItemSlotUtils.getSlotForItem(chip.id, chip))
        assertNull(ItemSlotUtils.getSlotForItem(medkit.id, medkit))
    }

    @Test
    fun testResolvesSlotByItemIdKeywordsFallback() {
        assertEquals("weapon", ItemSlotUtils.getSlotForItem("plasma_rifle"))
        assertEquals("weapon", ItemSlotUtils.getSlotForItem("cyber_katana"))
        assertEquals("armor", ItemSlotUtils.getSlotForItem("nano_suit"))
        assertEquals("head", ItemSlotUtils.getSlotForItem("nomad_goggles"))
        assertEquals("head", ItemSlotUtils.getSlotForItem("tactical_helmet"))
        assertEquals("chip", ItemSlotUtils.getSlotForItem("tachyon_core"))
    }

    @Test
    fun testEquippableAndConsumableChecks() {
        val sword = ItemMetadata(id = "sword_1", name = "Меч", type = "weapon", rarity = "rare")
        val stim = ItemMetadata(id = "stim_1", name = "Стимулятор", type = "consumable", rarity = "common")

        assertTrue(ItemSlotUtils.isEquippable(sword.id, sword))
        assertFalse(ItemSlotUtils.isConsumable(sword.id, sword))

        assertFalse(ItemSlotUtils.isEquippable(stim.id, stim))
        assertTrue(ItemSlotUtils.isConsumable(stim.id, stim))
    }
}

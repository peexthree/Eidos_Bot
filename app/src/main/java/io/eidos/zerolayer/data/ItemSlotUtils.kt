package io.eidos.zerolayer.data

object ItemSlotUtils {
    /**
     * Resolves the equipment slot ("weapon", "armor", "head", "chip") for any item,
     * or returns null if the item is not equippable (e.g. consumable, material).
     */
    fun getSlotForItem(itemId: String, meta: GameRepository.ItemMetadata? = null): String? {
        if (meta != null) {
            val t = meta.type.lowercase().trim()
            when {
                t == "weapon" || t == "atk" || t.contains("weapon") || t.contains("sword") || t.contains("blade") || t.contains("gun") || t.contains("knife") || t.contains("cannon") || t.contains("rifle") -> return "weapon"
                t == "armor" || t == "def" || t == "legs" || t == "boots" || t == "feet" || t == "body" || t.contains("armor") || t.contains("suit") || t.contains("vest") || t.contains("jacket") || t.contains("cloak") || t.contains("coat") || t.contains("plating") || t.contains("shroud") -> return "armor"
                t == "head" || t == "helmet" || t == "visor" || t == "mask" || t == "goggles" || t.contains("head") || t.contains("helmet") || t.contains("crown") || t.contains("halo") || t.contains("hood") || t.contains("cowl") || t.contains("eye") -> return "head"
                t == "chip" || t == "module" || t == "stl" || t.contains("chip") || t.contains("drive") || t.contains("booster") || t.contains("core") || t.contains("link") || t.contains("coil") || t.contains("transistor") -> return "chip"
            }
        }

        val id = itemId.lowercase().trim()

        // Explicit check by ID or keywords
        return when {
            // Weapon
            id in listOf(
                "rusty_knife", "crowbar", "data_bat", "shock_baton", "cyber_katana",
                "laser_pistol", "plasma_rifle", "nano_blade", "void_cannon", "singularity_sword",
                "credit_slicer", "banhammer_shard", "grandfather_paradox", "empath_whip", "cache_wiper",
                "trojan_bat", "ddos_cannon", "backdoor_js", "bruteforce_exe"
            ) || id.contains("sword") || id.contains("knife") || id.contains("cannon") ||
               id.contains("blade") || id.contains("rifle") || id.contains("pistol") ||
               id.contains("baton") || id.contains("whip") || id.contains("bat") ||
               id.contains("katana") || id.contains("cleaver") || id.contains("slicer") ||
               id.contains("dagger") || id.contains("axe") || id.contains("hammer") -> "weapon"

            // Armor / Body / Legs / Boots / Feet / Shield
            id in listOf(
                "hoodie", "leather_jacket", "kevlar_vest", "tactical_suit", "exo_skeleton",
                "nano_suit", "phantom_cloak", "force_field", "reality_armor", "quantum_shield",
                "error_404_mirror", "judas_shell", "holo_poverty", "schrodinger_armor", "schrodingers_armor",
                "thermonuclear_shroud", "cyber_vest", "void_armor", "nano_armor", "bio_plating", "thermal_plating",
                "chest_plate_forged", "exoskeleton_frame", "scavenger_coat"
            ) || id.contains("armor") || id.contains("suit") || id.contains("jacket") ||
               id.contains("vest") || id.contains("cloak") || id.contains("shield") ||
               id.contains("hoodie") || id.contains("shell") || id.contains("legs") ||
               id.contains("boots") || id.contains("pants") || id.contains("greaves") ||
               id.contains("poverty") || id.contains("shroud") || id.contains("coat") ||
               id.contains("plating") || id.contains("chassis") || id.contains("plate") -> "armor"

            // Head / Helmet / Mask / Visor / Crown / Hood / Halo / Eye
            id in listOf(
                "nomad_goggles", "scavenger_mask", "tactical_helmet", "vampire_visor", "cyber_halo",
                "overclock_crown", "void_walker_hood", "architect_mask", "relic_vampire", "relic_speed",
                "architect_eye", "crown_paranoia", "death_mask", "reality_silencer", "martyr_halo", "martyrs_halo",
                "tac_visor", "shadow_reliq_speed", "cyber_mask", "sentinel_visor", "combat_goggles",
                "reflex_visor", "shadow_cowl", "holo_hood", "neuro_crown", "eidos_crown"
            ) || id.contains("helmet") || id.contains("mask") || id.contains("visor") ||
               id.contains("crown") || id.contains("hood") || id.contains("halo") ||
               id.contains("goggles") || id.contains("eye") || id.contains("paranoia") ||
               id.contains("silencer") || id.contains("cowl") -> "head"

            // Chip / Module / Booster
            id in listOf(
                "ram_chip", "cpu_booster", "ai_core", "neural_link", "chronometer",
                "god_mode_chip", "glitch_filter", "overclocker", "overclock_module", "backup_drive", "logic_gate",
                "blood_miner", "karma_inversion", "oblivion_chip", "imposter_syndrome", "kamikaze_protocol",
                "maxwells_demon", "quantum_chip", "quantum_coil", "quantum_transistor", "kinetic_core",
                "tachyon_core", "chrono_drive", "chrono_drive_core", "reflex_boost", "neural_injector"
            ) || id.contains("chip") || id.contains("booster") || id.contains("core") ||
               id.contains("drive") || id.contains("link") || id.contains("gate") ||
               id.contains("overclock") || id.contains("protocol") || id.contains("miner") ||
               id.contains("inversion") || id.contains("syndrome") || id.contains("demon") ||
               id.contains("transistor") || id.contains("coil") || id.contains("module") -> "chip"

            else -> null
        }
    }

    fun getSlotForInventoryItem(item: InventoryItem, meta: GameRepository.ItemMetadata? = null): String? {
        val dbSlot = item.slot?.lowercase()?.trim()
        if (!dbSlot.isNullOrEmpty() && dbSlot in listOf("weapon", "armor", "head", "chip")) {
            return dbSlot
        }
        return getSlotForItem(item.item_id, meta)
    }

    fun isEquippable(itemId: String, meta: GameRepository.ItemMetadata? = null): Boolean {
        return getSlotForItem(itemId, meta) != null
    }

    /** Предметы, НЕ подлежащие синтезу 3-в-1: ключи, валюта, боссовые материалы. */
    val NON_MERGEABLE = setOf(
        "master_key", "abyssal_key", "admin_key", "hub_lock",
        "eidos_shard", "boss_core", "encrypted_cache"
    )

    /** Слитый предмет должен остаться в той же категории (шлемы в шлемы, расходники в расходники). */
    fun mergeCategoryFor(itemId: String, meta: GameRepository.ItemMetadata?): String? {
        val slot = getSlotForItem(itemId, meta)
        if (slot != null) return slot
        return when {
            isConsumable(itemId, meta) -> "consumable"
            meta?.type == "material" || itemId == "boss_core" -> "material"
            else -> null
        }
    }

    fun isConsumable(itemId: String, meta: GameRepository.ItemMetadata? = null): Boolean {
        if (meta?.type == "consumable") return true
        val id = itemId.lowercase()
        return id in listOf(
            "medkit", "energy_cell", "master_key", "abyssal_key", "battery",
            "neural_stimulator", "aegis", "admin_key", "emp_grenade", "stealth_spray",
            "data_spike", "memory_wiper", "cryo_capsule", "regen_kit", "stim_pack"
        ) || id.contains("medkit") || id.contains("battery") || id.contains("key") ||
           id.contains("stimulator") || id.contains("grenade") || id.contains("spray") ||
           id.contains("capsule") || id.contains("stim")
    }
}


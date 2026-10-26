package io.eidos.zerolayer.data

object AssetIconsMapping {

    fun getAssetIconUrl(key: String?): String {
        val cleanKey = key?.lowercase()?.trim() ?: ""

        val assetName = when {
            // Specific key matches
            cleanKey.contains("knife") || cleanKey.contains("crowbar") || cleanKey.contains("bat") ||
                    cleanKey.contains("baton") || cleanKey.contains("katana") || cleanKey.contains("pistol") ||
                    cleanKey.contains("rifle") || cleanKey.contains("blade") || cleanKey.contains("cannon") ||
                    cleanKey.contains("sword") -> "eidos_weapon_attack.svg"

            cleanKey.contains("goggles") || cleanKey.contains("mask") || cleanKey.contains("helmet") -> "eidos_shield_armor.svg"

            cleanKey.contains("armor") || cleanKey.contains("vest") || cleanKey.contains("skeleton") ||
                    cleanKey.contains("suit") || cleanKey.contains("def") -> "eidos_armor_defense.svg"

            cleanKey.contains("medkit") || cleanKey.contains("stim") || cleanKey.contains("repair") -> "eidos_medkit_repair.svg"

            cleanKey.contains("battery") || cleanKey.contains("energy") -> "eidos_energy_cell.svg"

            cleanKey.contains("key") -> "eidos_security_key.svg"

            cleanKey.contains("firewall") || cleanKey.contains("trap") || cleanKey.contains("proxy") -> "eidos_firewall.svg"

            cleanKey.contains("grenade") || cleanKey.contains("spike") || cleanKey.contains("mine") -> "eidos_data_mine.svg"

            cleanKey.contains("stealth") || cleanKey.contains("wiper") || cleanKey.contains("ghost") -> "eidos_stealth_ghost.svg"

            cleanKey.contains("chip") || cleanKey.contains("mod") || cleanKey.contains("core") || cleanKey.contains("forge") -> "eidos_forge_craft.svg"

            cleanKey.contains("shard") || cleanKey.contains("fragment") -> "eidos_shard_premium.svg"

            cleanKey.contains("soft") || cleanKey.contains("brute") || cleanKey.contains("trojan") ||
                    cleanKey.contains("ddos") || cleanKey.contains("sniffer") || cleanKey.contains("backdoor") ||
                    cleanKey.contains("vpn") || cleanKey.contains("aegis") || cleanKey.contains("ice") -> "eidos_api_node.svg"

            cleanKey.contains("cursed") || cleanKey.contains("corrupted") || cleanKey.contains("anomaly") ||
                    cleanKey.contains("glitch") -> "eidos_glitch_anomaly.svg"

            cleanKey.contains("chest") || cleanKey.contains("cache") || cleanKey.contains("inventory") -> "eidos_inventory_cache.svg"

            cleanKey.contains("evac") || cleanKey.contains("travel") -> "eidos_fast_travel.svg"

            cleanKey.contains("death") || cleanKey.contains("warning") -> "eidos_sys_warning.svg"

            cleanKey.contains("avatar") || cleanKey.contains("hacker") || cleanKey.contains("user") -> "eidos_demiurge_user.svg"

            cleanKey.contains("boss") || cleanKey.contains("villain") || cleanKey.contains("паразит") ||
                    cleanKey.contains("призрак") || cleanKey.contains("дрон") || cleanKey.contains("дракон") -> "eidos_drone_bot.svg"

            cleanKey.contains("compass") || cleanKey.contains("scanner") -> "eidos_vision_eye.svg"

            cleanKey.contains("dice") || cleanKey.contains("luck") -> "eidos_luck_dice.svg"

            else -> "eidos_eidos_core.svg"
        }

        return "file:///android_asset/icons/$assetName"
    }
}

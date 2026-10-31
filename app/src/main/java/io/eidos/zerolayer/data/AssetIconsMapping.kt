package io.eidos.zerolayer.data

object AssetIconsMapping {

    private val KNOWN_SVGS = setOf(
        "eidos_api_node", "eidos_arena_pvp", "eidos_armor_defense", "eidos_audio_wave",
        "eidos_biometric_id", "eidos_black_market", "eidos_boss_tier2", "eidos_comm_link",
        "eidos_core_collapse", "eidos_credits_crypto", "eidos_data_mine", "eidos_demiurge_user",
        "eidos_drone_bot", "eidos_eidos_core", "eidos_energy_cell", "eidos_fast_travel",
        "eidos_firewall", "eidos_forge_craft", "eidos_glitch_anomaly", "eidos_inventory_cache",
        "eidos_luck_dice", "eidos_map_sector", "eidos_medkit_repair", "eidos_net_sync",
        "eidos_neuro_brain", "eidos_raid_boss", "eidos_security_key", "eidos_server_cloud",
        "eidos_settings_gear", "eidos_shard_premium", "eidos_shield_armor", "eidos_skill_tree",
        "eidos_sniper_aim", "eidos_stealth_ghost", "eidos_streak_power", "eidos_sys_warning",
        "eidos_target_quest", "eidos_terminal_log", "eidos_time_cycle", "eidos_vision_eye",
        "eidos_weapon_attack", "eidos_xp_rank", "nav_head_eidos", "nav_head_forge",
        "nav_head_psycho", "nav_head_raid", "nav_head_shop", "nav_tab_all",
        "nav_tab_consum", "nav_tab_craft", "nav_tab_equip", "nav_tab_mat"
    )

    fun getAssetIconUrl(key: String?): String {
        val raw = key?.lowercase()?.trim() ?: ""
        if (raw.isBlank()) return "file:///android_asset/icons/eidos_eidos_core.svg"

        val cleanKey = raw.removeSuffix(".svg").removeSuffix(".png").removeSuffix(".jpg").replace(" ", "_")

        // 1. Direct match with existing SVG in assets/icons
        if (cleanKey in KNOWN_SVGS) {
            return "file:///android_asset/icons/$cleanKey.svg"
        }
        val eidosPrefixed = "eidos_$cleanKey"
        if (eidosPrefixed in KNOWN_SVGS) {
            return "file:///android_asset/icons/$eidosPrefixed.svg"
        }
        val navPrefixed = "nav_$cleanKey"
        if (navPrefixed in KNOWN_SVGS) {
            return "file:///android_asset/icons/$navPrefixed.svg"
        }

        // 2. Keyword fallback matching
        val assetName = when {
            cleanKey.contains("knife") || cleanKey.contains("crowbar") || cleanKey.contains("bat") ||
                    cleanKey.contains("baton") || cleanKey.contains("katana") || cleanKey.contains("pistol") ||
                    cleanKey.contains("rifle") || cleanKey.contains("blade") || cleanKey.contains("cannon") ||
                    cleanKey.contains("sword") || cleanKey.contains("weapon") || cleanKey.contains("клинок") ||
                    cleanKey.contains("меч") || cleanKey.contains("оружие") -> "eidos_weapon_attack.svg"

            cleanKey.contains("goggles") || cleanKey.contains("mask") || cleanKey.contains("helmet") ||
                    cleanKey.contains("шлем") || cleanKey.contains("маска") -> "eidos_shield_armor.svg"

            cleanKey.contains("armor") || cleanKey.contains("vest") || cleanKey.contains("skeleton") ||
                    cleanKey.contains("suit") || cleanKey.contains("def") || cleanKey.contains("броня") ||
                    cleanKey.contains("щит") -> "eidos_armor_defense.svg"

            cleanKey.contains("medkit") || cleanKey.contains("stim") || cleanKey.contains("repair") ||
                    cleanKey.contains("аптечка") || cleanKey.contains("стимулятор") -> "eidos_medkit_repair.svg"

            cleanKey.contains("battery") || cleanKey.contains("energy") || cleanKey.contains("батарея") ||
                    cleanKey.contains("энергия") -> "eidos_energy_cell.svg"

            cleanKey.contains("key") || cleanKey.contains("ключ") || cleanKey.contains("lock") -> "eidos_security_key.svg"

            cleanKey.contains("firewall") || cleanKey.contains("trap") || cleanKey.contains("proxy") -> "eidos_firewall.svg"

            cleanKey.contains("grenade") || cleanKey.contains("spike") || cleanKey.contains("mine") -> "eidos_data_mine.svg"

            cleanKey.contains("stealth") || cleanKey.contains("wiper") || cleanKey.contains("ghost") -> "eidos_stealth_ghost.svg"

            cleanKey.contains("chip") || cleanKey.contains("mod") || cleanKey.contains("core") ||
                    cleanKey.contains("forge") || cleanKey.contains("чип") || cleanKey.contains("кузница") -> "eidos_forge_craft.svg"

            cleanKey.contains("shard") || cleanKey.contains("fragment") || cleanKey.contains("осколок") -> "eidos_shard_premium.svg"

            cleanKey.contains("soft") || cleanKey.contains("brute") || cleanKey.contains("trojan") ||
                    cleanKey.contains("ddos") || cleanKey.contains("sniffer") || cleanKey.contains("backdoor") ||
                    cleanKey.contains("vpn") || cleanKey.contains("aegis") || cleanKey.contains("ice") -> "eidos_api_node.svg"

            cleanKey.contains("cursed") || cleanKey.contains("corrupted") || cleanKey.contains("anomaly") ||
                    cleanKey.contains("glitch") -> "eidos_glitch_anomaly.svg"

            cleanKey.contains("chest") || cleanKey.contains("cache") || cleanKey.contains("inventory") ||
                    cleanKey.contains("сундук") || cleanKey.contains("инвентарь") -> "eidos_inventory_cache.svg"

            cleanKey.contains("evac") || cleanKey.contains("travel") || cleanKey.contains("эвакуация") -> "eidos_fast_travel.svg"

            cleanKey.contains("death") || cleanKey.contains("warning") -> "eidos_sys_warning.svg"

            cleanKey.contains("avatar") || cleanKey.contains("hacker") || cleanKey.contains("user") -> "eidos_demiurge_user.svg"

            cleanKey.contains("boss") || cleanKey.contains("villain") || cleanKey.contains("паразит") ||
                    cleanKey.contains("призрак") || cleanKey.contains("дрон") || cleanKey.contains("дракон") -> "eidos_drone_bot.svg"

            cleanKey.contains("compass") || cleanKey.contains("scanner") || cleanKey.contains("компас") -> "eidos_vision_eye.svg"

            cleanKey.contains("dice") || cleanKey.contains("luck") || cleanKey.contains("удача") -> "eidos_luck_dice.svg"

            else -> "eidos_eidos_core.svg"
        }

        return "file:///android_asset/icons/$assetName"
    }
}

package io.eidos.zerolayer.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ForeignKey
import androidx.room.Index
import kotlinx.serialization.Serializable

fun calculateLevelForXp(xp: Long): Int {
    return PlayerProgressManager.calculateLevel(xp)
}

fun Player.getLevelUpShards(toLevel: Int): Int {
    if (toLevel <= this.level) return 0
    return (this.level + 1..toLevel).sumOf { lvl -> PlayerProgressManager.getLevelInfo(lvl).rewardShards }
}

fun Player.checkAndApplyLevelUp(): Pair<Player, Boolean> {
    val newLevel = calculateLevelForXp(this.xp).coerceIn(1, 31)
    if (newLevel > this.level) {
        val levelDiff = newLevel - this.level
        val bonusHp = levelDiff * 20
        val bonusAtk = levelDiff * 3
        val bonusDef = levelDiff * 2
        val bonusCoins = (this.level + 1..newLevel).sumOf { lvl -> PlayerProgressManager.getLevelInfo(lvl).rewardBioCoins }
        val updated = this.copy(
            level = newLevel,
            highest_level = maxOf(this.highest_level, newLevel),
            biocoin = this.biocoin + bonusCoins,
            max_hp = this.max_hp + bonusHp,
            hp = minOf(this.max_hp + bonusHp, this.hp + bonusHp),
            attack = this.attack + bonusAtk,
            defense = this.defense + bonusDef,
            state_version = this.state_version + 1,
            updated_at = System.currentTimeMillis()
        )
        return Pair(updated, true)
    }
    return Pair(this, false)
}

@Serializable
@Entity(tableName = "players")
data class Player(
    @PrimaryKey val uid: Long,
    val username: String?,
    val first_name: String?,
    val path: String = "general",
    val xp: Long = 0,
    val biocoin: Long = 100,
    val level: Int = 1,
    val highest_level: Int = 1,
    val streak: Int = 1,
    val energy: Int = 100,
    val max_energy: Int = 100,
    val hp: Int = 100,
    val max_hp: Int = 100,
    val attack: Int = 10,
    val defense: Int = 5,
    val luck: Int = 5,
    val last_active: Long = System.currentTimeMillis(),
    val total_spent: Long = 0,
    val is_admin: Boolean = false,
    val is_active: Boolean = true,
    val max_depth: Int = 0,
    val faction: String = "NONE",
    val kills: Int = 0,
    val raids_done: Int = 0,
    val perfect_raids: Int = 0,
    val skill_hacker_1: Int = 0,
    val skill_hacker_2: Int = 0,
    val skill_hacker_3: Int = 0,
    val skill_berserk_1: Int = 0,
    val skill_berserk_2: Int = 0,
    val skill_berserk_3: Int = 0,
    val skill_medic_1: Int = 0,
    val skill_medic_2: Int = 0,
    val skill_medic_3: Int = 0,
    val is_premium: Boolean = false,
    val last_supply_drop: Long = 0,
    val last_recharge: Long = 0,
    val last_signal_restore: Long = 0,
    val last_sync: Long = 0,
    val sync_accel_expiry: Long = 0,
    val cyber_deck_slots: Int = 4,
    val wins_pvp: Int = 0,
    val losses_pvp: Int = 0,
    val pvp_shield_until: Long = 0,
    val pvp_proxy_until: Long = 0,
    val defense_program_1: String = "SHIELD",
    val defense_program_2: String = "BRUTEFORCE",
    val defense_program_3: String = "STEALTH",
    val installed_hardware: String = "",
    val vendetta_logs: String = "",
    val reputation: Int = 0,
    val referral_code: String? = null,
    val referred_by: String? = null,
    val telegram_id: Long? = null,
    val telegram_username: String? = null,
    val meta_signal_level: Int = 0,
    val meta_key_level: Int = 0,
    val meta_luck_level: Int = 0,
    val meta_power_level: Int = 0,
    val weapon_level: Int = 1,
    val isGlitched: Boolean = false,
    val anomalyBuffType: String? = null,
    val anomalyBuffExpiry: Long = 0L,
    val lastHardGlitchTimestamp: Long = 0L,
    val glitchEncounterCounter: Int = 0,
    val state_version: Long = 1,
    val updated_at: Long = System.currentTimeMillis()
)

@Serializable
@Entity(
    tableName = "inventory",
    foreignKeys = [
        ForeignKey(
            entity = Player::class,
            parentColumns = ["uid"],
            childColumns = ["uid"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("uid")]
)
data class InventoryItem(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val uid: Long,
    val item_id: String,
    val quantity: Int = 1,
    val durability: Float = 100f,
    val is_equipped: Boolean = false,
    val slot: String? = null, // head, armor, weapon, module
    val custom_data: String? = null
)

@Entity(
    tableName = "game_logs",
    foreignKeys = [
        ForeignKey(
            entity = Player::class,
            parentColumns = ["uid"],
            childColumns = ["uid"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("uid")]
)
data class GameLog(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val uid: Long,
    val message: String,
    val type: String = "info", // info, combat, loot, error
    val timestamp: Long = System.currentTimeMillis()
)

@Entity(tableName = "villains_static")
data class VillainStatic(
    @PrimaryKey val name: String,
    val level: Int,
    val hp: Int,
    val atk: Int,
    val def: Int,
    val xp: Int,
    val coin: Int,
    val desc: String,
    val image: String? = null
)

@Entity(tableName = "game_content")
data class GameContent(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val level: String, // "1", "2", etc from JSON keys
    val type: String, // advice, protocol, signal
    val path: String, // raid_general, business, etc
    val text: String
)

@Entity(tableName = "raid_sessions")
data class RaidSession(
    @PrimaryKey val uid: Long,
    val depth: Int = 0,
    val signal: Int = 100,
    val buffer_xp: Long = 0,
    val buffer_coins: Long = 0,
    val buffer_items: String = "", // Comma separated item IDs
    val kills: Int = 0,
    val riddles_solved: Int = 0,
    val next_event_type: String? = null,
    val current_anomaly_id: String? = null,
    val event_streak: Int = 0,
    val current_enemy_id: String? = null,
    val current_enemy_hp: Int = 0,
    val start_time: Long = System.currentTimeMillis(),
    val combat_turn: Int = 0,
    val damage_buffer: Int = 0,
    val is_scanned: Boolean = false,
    val combo_count: Int = 0,
    val overdrive_turns: Int = 0,
    val active_mutator: String? = null,
    val drone_turns_left: Int = 0,
    val extract_multiplier: Float = 1.0f,
    val raid_damage_buff: Boolean = false,
    val boss_defeated_at: Int = 0,
    val active_aggro: Int = 0,
    val has_scanned_next_room: Boolean = false
)

@Serializable
@Entity(tableName = "graves")
data class Grave(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val uid: Long,
    val owner_name: String,
    val depth: Int,
    val coins: Long,
    val items: String, // Comma separated item IDs
    val timestamp: Long = System.currentTimeMillis()
)

@Serializable
@Entity(tableName = "bestiary_entries")
data class BestiaryEntry(
    @PrimaryKey val enemy_id: String,
    val encountered: Boolean = true,
    val killed_count: Int = 0
)

@Serializable
@Entity(tableName = "radio_messages")
data class RadioMessageEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val uid: Long,
    val sender: String,
    val title: String,
    val body: String,
    val rewardCoins: Long = 0L,
    val rewardXp: Long = 0L,
    val isClaimed: Boolean = false,
    val timestamp: Long = System.currentTimeMillis()
)

data class CombatVisualEvent(
    val eventId: Long = System.currentTimeMillis(),
    val damage: Int = 0,
    val isCrit: Boolean = false,
    val isOverdrive: Boolean = false,
    val isDodge: Boolean = false,
    val isPlayerHit: Boolean = false,
    val incomingDamage: Int = 0
)


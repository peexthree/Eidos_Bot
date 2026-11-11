package io.eidos.zerolayer.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.sql.Connection
import java.sql.DriverManager

/**
 * Миграционные тесты Room на реальном SQLite (xerial), без эмулятора.
 *
 * Room-схемы до v14 не экспортировались (exportSchema = false), поэтому
 * MigrationTestHelper с JSON-ассетами недоступен. Вместо этого тест
 * воспроизводит схему v10 вручную (сущности минус колонки, добавленные
 * миграциями 10-14), прогоняет боевые Migration-объекты через JDBC-обёртку
 * SupportSQLiteDatabase и проверяет:
 *  - новые колонки/таблицы/индексы появились;
 *  - данные игроков/инвентаря/логов/радио переживают цепочку миграций.
 *
 * Начиная с v14 схемы экспортируются (app/schemas) - при следующем
 * повышении версии стоит скопировать сюда свежую схему как v14-фикстуру.
 */
class DatabaseMigrationTest {

    private val conn: Connection = DriverManager.getConnection("jdbc:sqlite::memory:")

    // --- Схема v10: все таблицы на момент версии 10 ---

    private fun createV10Schema() {
        val ddl = listOf(
            // players: БЕЗ overdriveCharge/overchargeTier (10->11) и prestige_count (13->14)
            """CREATE TABLE IF NOT EXISTS players (
                uid INTEGER NOT NULL PRIMARY KEY,
                username TEXT, first_name TEXT,
                path TEXT NOT NULL DEFAULT 'general',
                xp INTEGER NOT NULL DEFAULT 0,
                biocoin INTEGER NOT NULL DEFAULT 100,
                level INTEGER NOT NULL DEFAULT 1,
                highest_level INTEGER NOT NULL DEFAULT 1,
                streak INTEGER NOT NULL DEFAULT 1,
                energy INTEGER NOT NULL DEFAULT 100,
                max_energy INTEGER NOT NULL DEFAULT 100,
                hp INTEGER NOT NULL DEFAULT 100,
                max_hp INTEGER NOT NULL DEFAULT 100,
                attack INTEGER NOT NULL DEFAULT 10,
                defense INTEGER NOT NULL DEFAULT 5,
                luck INTEGER NOT NULL DEFAULT 5,
                last_active INTEGER NOT NULL,
                total_spent INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                max_depth INTEGER NOT NULL DEFAULT 0,
                faction TEXT NOT NULL DEFAULT 'NONE',
                kills INTEGER NOT NULL DEFAULT 0,
                raids_done INTEGER NOT NULL DEFAULT 0,
                perfect_raids INTEGER NOT NULL DEFAULT 0,
                skill_hacker_1 INTEGER NOT NULL DEFAULT 0, skill_hacker_2 INTEGER NOT NULL DEFAULT 0, skill_hacker_3 INTEGER NOT NULL DEFAULT 0,
                skill_berserk_1 INTEGER NOT NULL DEFAULT 0, skill_berserk_2 INTEGER NOT NULL DEFAULT 0, skill_berserk_3 INTEGER NOT NULL DEFAULT 0,
                skill_medic_1 INTEGER NOT NULL DEFAULT 0, skill_medic_2 INTEGER NOT NULL DEFAULT 0, skill_medic_3 INTEGER NOT NULL DEFAULT 0,
                is_premium INTEGER NOT NULL DEFAULT 0,
                last_supply_drop INTEGER NOT NULL DEFAULT 0,
                last_recharge INTEGER NOT NULL DEFAULT 0,
                last_signal_restore INTEGER NOT NULL DEFAULT 0,
                last_sync INTEGER NOT NULL DEFAULT 0,
                sync_accel_expiry INTEGER NOT NULL DEFAULT 0,
                cyber_deck_slots INTEGER NOT NULL DEFAULT 4,
                wins_pvp INTEGER NOT NULL DEFAULT 0,
                losses_pvp INTEGER NOT NULL DEFAULT 0,
                pvp_shield_until INTEGER NOT NULL DEFAULT 0,
                pvp_proxy_until INTEGER NOT NULL DEFAULT 0,
                defense_program_1 TEXT NOT NULL DEFAULT 'SHIELD',
                defense_program_2 TEXT NOT NULL DEFAULT 'BRUTEFORCE',
                defense_program_3 TEXT NOT NULL DEFAULT 'STEALTH',
                installed_hardware TEXT NOT NULL DEFAULT '',
                vendetta_logs TEXT NOT NULL DEFAULT '',
                reputation INTEGER NOT NULL DEFAULT 0,
                referral_code TEXT, referred_by TEXT,
                telegram_id INTEGER, telegram_username TEXT,
                meta_signal_level INTEGER NOT NULL DEFAULT 0,
                meta_key_level INTEGER NOT NULL DEFAULT 0,
                meta_luck_level INTEGER NOT NULL DEFAULT 0,
                meta_power_level INTEGER NOT NULL DEFAULT 0,
                weapon_level INTEGER NOT NULL DEFAULT 1,
                isGlitched INTEGER NOT NULL DEFAULT 0,
                anomalyBuffType TEXT,
                anomalyBuffExpiry INTEGER NOT NULL DEFAULT 0,
                lastHardGlitchTimestamp INTEGER NOT NULL DEFAULT 0,
                glitchEncounterCounter INTEGER NOT NULL DEFAULT 0,
                state_version INTEGER NOT NULL DEFAULT 1,
                updated_at INTEGER NOT NULL
            )""",
            // inventory
            """CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                uid INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                durability REAL NOT NULL DEFAULT 100.0,
                is_equipped INTEGER NOT NULL DEFAULT 0,
                slot TEXT, custom_data TEXT,
                FOREIGN KEY(uid) REFERENCES players(uid) ON UPDATE NO ACTION ON DELETE CASCADE
            )""",
            "CREATE INDEX IF NOT EXISTS index_inventory_uid ON inventory(uid)",
            // game_logs: БЕЗ композитного индекса (12->13)
            """CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                uid INTEGER NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'info',
                timestamp INTEGER NOT NULL,
                FOREIGN KEY(uid) REFERENCES players(uid) ON UPDATE NO ACTION ON DELETE CASCADE
            )""",
            "CREATE INDEX IF NOT EXISTS index_game_logs_uid ON game_logs(uid)",
            """CREATE TABLE IF NOT EXISTS villains_static (
                name TEXT NOT NULL PRIMARY KEY,
                level INTEGER NOT NULL, hp INTEGER NOT NULL, atk INTEGER NOT NULL,
                def INTEGER NOT NULL, xp INTEGER NOT NULL, coin INTEGER NOT NULL,
                desc TEXT NOT NULL, image TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS game_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                level TEXT NOT NULL, type TEXT NOT NULL, path TEXT NOT NULL, text TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS raid_sessions (
                uid INTEGER NOT NULL PRIMARY KEY,
                depth INTEGER NOT NULL DEFAULT 0,
                signal INTEGER NOT NULL DEFAULT 100,
                buffer_xp INTEGER NOT NULL DEFAULT 0,
                buffer_coins INTEGER NOT NULL DEFAULT 0,
                buffer_items TEXT NOT NULL DEFAULT '',
                kills INTEGER NOT NULL DEFAULT 0,
                riddles_solved INTEGER NOT NULL DEFAULT 0,
                next_event_type TEXT, current_anomaly_id TEXT,
                event_streak INTEGER NOT NULL DEFAULT 0,
                current_enemy_id TEXT, current_enemy_hp INTEGER NOT NULL DEFAULT 0,
                start_time INTEGER NOT NULL,
                combat_turn INTEGER NOT NULL DEFAULT 0,
                damage_buffer INTEGER NOT NULL DEFAULT 0,
                is_scanned INTEGER NOT NULL DEFAULT 0,
                combo_count INTEGER NOT NULL DEFAULT 0,
                overdrive_turns INTEGER NOT NULL DEFAULT 0,
                active_mutator TEXT,
                drone_turns_left INTEGER NOT NULL DEFAULT 0,
                extract_multiplier REAL NOT NULL DEFAULT 1.0,
                raid_damage_buff INTEGER NOT NULL DEFAULT 0,
                boss_defeated_at INTEGER NOT NULL DEFAULT 0,
                active_aggro INTEGER NOT NULL DEFAULT 0,
                has_scanned_next_room INTEGER NOT NULL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS graves (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                uid INTEGER NOT NULL, owner_name TEXT NOT NULL, depth INTEGER NOT NULL,
                coins INTEGER NOT NULL, items TEXT NOT NULL, timestamp INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS bestiary_entries (
                enemy_id TEXT NOT NULL PRIMARY KEY,
                encountered INTEGER NOT NULL DEFAULT 1,
                killed_count INTEGER NOT NULL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS radio_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                uid INTEGER NOT NULL,
                sender TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
                rewardCoins INTEGER NOT NULL DEFAULT 0,
                rewardXp INTEGER NOT NULL DEFAULT 0,
                isClaimed INTEGER NOT NULL DEFAULT 0,
                timestamp INTEGER NOT NULL
            )"""
        )
        execAll(ddl)
    }

    /** SupportSQLiteDatabase-обёртка над JDBC: миграции используют только execSQL. */
    private fun jdbcSupportDb(): androidx.sqlite.db.SupportSQLiteDatabase {
        val iface = androidx.sqlite.db.SupportSQLiteDatabase::class.java
        val proxy = java.lang.reflect.Proxy.newProxyInstance(
            iface.classLoader, arrayOf(iface)
        ) { _, method, args ->
            when {
                method.name == "execSQL" -> {
                    val sql = args!![0] as String
                    if (args.size > 1 && args[1] != null) {
                        @Suppress("UNCHECKED_CAST")
                        val bindArgs = args[1] as Array<Any?>
                        conn.prepareStatement(sql).use { st ->
                            bindArgs.forEachIndexed { i, v -> st.setObject(i + 1, v) }
                            st.execute()
                        }
                    } else {
                        conn.createStatement().use { it.execute(sql) }
                    }
                    null
                }
                method.declaringClass == Any::class.java -> when (method.name) {
                    "toString" -> "JdbcSupportDb"
                    "hashCode" -> System.identityHashCode(this)
                    "equals" -> this === args?.get(0)
                    else -> null
                }
                else -> throw UnsupportedOperationException("Тест использует только execSQL, вызван: ${method.name}")
            }
        }
        return proxy as androidx.sqlite.db.SupportSQLiteDatabase
    }

    private fun execAll(statements: List<String>) {
        statements.forEach { sql ->
            conn.createStatement().use { it.execute(sql.trimIndent()) }
        }
    }

    private fun scalar(sql: String): Any? =
        conn.createStatement().use { st ->
            st.executeQuery(sql).use { rs -> if (rs.next()) rs.getObject(1) else null }
        }

    /** xerial возвращает Integer для COUNT и небольших INTEGER - нормализуем к Long. */
    private fun scalarLong(sql: String): Long = (scalar(sql) as? Number)?.toLong() ?: -1L

    private fun playerColumns(): Set<String> {
        val names = mutableSetOf<String>()
        conn.createStatement().use { st ->
            st.executeQuery("PRAGMA table_info(players)").use { rs ->
                while (rs.next()) names.add(rs.getString("name"))
            }
        }
        return names
    }

    private fun insertV10Player(uid: Long = 7L) {
        conn.createStatement().use { st ->
            st.execute(
                "INSERT INTO players (uid, username, first_name, xp, biocoin, level, max_depth, kills, last_active, updated_at) " +
                    "VALUES ($uid, 'СТАЛКЕР-7', 'Игорь', 4200, 1337, 5, 2400, 42, 1700000000000, 1700000000000)"
            )
        }
    }

    private fun insertV10Rows(uid: Long = 7L) {
        execAll(listOf(
            "INSERT INTO inventory (uid, item_id, quantity, is_equipped) VALUES ($uid, 'quantum_blade', 1, 1)",
            "INSERT INTO inventory (uid, item_id, quantity, is_equipped) VALUES ($uid, 'medkit_small', 3, 0)",
            "INSERT INTO game_logs (uid, message, type, timestamp) VALUES ($uid, 'боевой лог', 'combat', 1700000001000)",
            "INSERT INTO game_logs (uid, message, type, timestamp) VALUES ($uid, 'лут', 'loot', 1700000002000)",
            "INSERT INTO radio_messages (uid, sender, title, body, rewardCoins, rewardXp, isClaimed, timestamp) " +
                "VALUES ($uid, 'Кассандра', 'СИГНАЛ', 'тело сообщения', 250, 120, 0, 1700000003000)"
        ))
    }

    /** Полная цепочка 10 -> 14 боевыми Migration-объектами. */
    private fun runMigrations() {
        val db = jdbcSupportDb()
        MIGRATION_10_11.migrate(db)
        MIGRATION_11_12.migrate(db)
        MIGRATION_12_13.migrate(db)
        MIGRATION_13_14.migrate(db)
    }

    @Test
    fun `chain 10 to 14 adds all columns tables and index`() {
        createV10Schema()
        runMigrations()

        // 10->11: колонки OVERDRIVE
        val cols = playerColumns()
        assertTrue(cols.containsAll(listOf("overdriveCharge", "overchargeTier")))
        // 13->14: престиж NG+
        assertTrue("prestige_count" in cols)

        // 11->12: user_equipment
        assertEquals(0L, scalarLong("SELECT COUNT(*) FROM user_equipment"))
        // запись вставляется в ожидаемой Room форме
        execAll(listOf("INSERT INTO user_equipment (player_uid, head, armor, weapon, chip, eidos_shard) VALUES (7, 'helmet', 'armor', 'blade', NULL, NULL)"))
        assertEquals(1L, scalarLong("SELECT COUNT(*) FROM user_equipment"))

        // 12->13: композитный индекс для trimOldLogs
        assertEquals(
            "index_game_logs_uid_timestamp",
            scalar("SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'index_game_logs_uid_timestamp'")
        )

        // 13->14: пул World Boss + вклад
        assertEquals(0L, scalarLong("SELECT COUNT(*) FROM world_boss_state"))
        assertEquals(0L, scalarLong("SELECT COUNT(*) FROM world_boss_contrib"))
        execAll(listOf(
            "INSERT INTO world_boss_state (id, boss_hp, boss_max_hp, cycle, last_reset_month) VALUES (1, 1000, 1000, 1, '2026-11')",
            "INSERT INTO world_boss_contrib (player_uid, total_damage) VALUES (7, 500)"
        ))
        // upsert-путь DAO (ON CONFLICT DO UPDATE)
        execAll(listOf("INSERT INTO world_boss_contrib (player_uid, total_damage) VALUES (7, 250) ON CONFLICT(player_uid) DO UPDATE SET total_damage = total_damage + 250"))
        assertEquals(750L, scalarLong("SELECT total_damage FROM world_boss_contrib WHERE player_uid = 7"))
    }

    @Test
    fun `chain 10 to 14 preserves existing player data`() {
        createV10Schema()
        insertV10Player()
        insertV10Rows()
        runMigrations()

        conn.createStatement().use { st ->
            st.executeQuery("SELECT username, xp, biocoin, level, max_depth, kills FROM players WHERE uid = 7").use { rs ->
                assertTrue(rs.next())
                assertEquals("СТАЛКЕР-7", rs.getString(1))
                assertEquals(4200L, rs.getLong(2))
                assertEquals(1337L, rs.getLong(3))
                assertEquals(5, rs.getInt(4))
                assertEquals(2400, rs.getInt(5))
                assertEquals(42, rs.getInt(6))
            }
        }

        // добавленные колонки получили DEFAULT 0, а не мусор/NULL
        conn.createStatement().use { st ->
            st.executeQuery("SELECT overdriveCharge, overchargeTier, prestige_count FROM players WHERE uid = 7").use { rs ->
                assertTrue(rs.next())
                assertEquals(0, rs.getInt(1)); assertEquals(0, rs.getInt(2)); assertEquals(0, rs.getInt(3))
            }
        }

        assertEquals(2L, scalarLong("SELECT COUNT(*) FROM inventory WHERE uid = 7"))
        assertEquals("quantum_blade", scalar("SELECT item_id FROM inventory WHERE uid = 7 AND is_equipped = 1"))
        assertEquals(2L, scalarLong("SELECT COUNT(*) FROM game_logs WHERE uid = 7"))
        assertEquals("боевой лог", scalar("SELECT message FROM game_logs WHERE uid = 7 ORDER BY timestamp ASC LIMIT 1"))
        assertEquals(0L, scalarLong("SELECT isClaimed FROM radio_messages WHERE uid = 7"))
        assertEquals(250L, scalarLong("SELECT rewardCoins FROM radio_messages WHERE uid = 7"))
    }

    @Test
    fun `chain 10 to 14 succeeds on empty database`() {
        createV10Schema()
        runMigrations()
        // Все 12 таблиц живы
        val tables = mutableSetOf<String>()
        conn.createStatement().use { st ->
            st.executeQuery("SELECT name FROM sqlite_master WHERE type = 'table'").use { rs ->
                while (rs.next()) tables.add(rs.getString(1))
            }
        }
        assertTrue(
            tables.containsAll(listOf(
                "players", "inventory", "game_logs", "villains_static", "game_content",
                "raid_sessions", "graves", "bestiary_entries", "radio_messages",
                "user_equipment", "world_boss_state", "world_boss_contrib"
            ))
        )
        assertNotNull(playerColumns())
    }
}

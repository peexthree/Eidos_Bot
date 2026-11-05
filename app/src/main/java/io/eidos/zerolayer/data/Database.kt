package io.eidos.zerolayer.data

import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow
import java.io.File

@Dao
interface EidosDao {
    @Query("SELECT * FROM players WHERE uid = :uid")
    suspend fun getPlayer(uid: Long): Player?

    @Query("SELECT * FROM players WHERE uid = :uid")
    fun getPlayerFlow(uid: Long): Flow<Player?>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertPlayer(player: Player): Long

    @Update
    suspend fun updatePlayer(player: Player)

    @Upsert
    suspend fun upsertPlayer(player: Player)

    @Query("SELECT * FROM inventory WHERE uid = :uid")
    fun getInventoryFlow(uid: Long): Flow<List<InventoryItem>>

    @Query("SELECT * FROM inventory WHERE uid = :uid AND is_equipped = 1")
    fun getEquippedItemsFlow(uid: Long): Flow<List<InventoryItem>>

    @Query("SELECT * FROM villains_static WHERE level <= :maxLevel")
    suspend fun getVillainsForLevel(maxLevel: Int): List<VillainStatic>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVillains(villains: List<VillainStatic>)

    @Query("SELECT * FROM game_content WHERE level = :level")
    suspend fun getContentForLevel(level: String): List<GameContent>

    @Query("SELECT * FROM game_content WHERE type = :type")
    suspend fun getContentByType(type: String): List<GameContent>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertContent(content: List<GameContent>)

    @Insert
    suspend fun insertInventoryItem(item: InventoryItem)

    @Update
    suspend fun updateInventoryItem(item: InventoryItem)

    @Delete
    suspend fun deleteInventoryItem(item: InventoryItem)

    @Query("DELETE FROM inventory WHERE uid = :uid")
    suspend fun clearInventory(uid: Long)

    @Query("SELECT * FROM inventory WHERE uid = :uid")
    suspend fun getInventorySync(uid: Long): List<InventoryItem>

    @Query("SELECT * FROM game_logs WHERE uid = :uid ORDER BY timestamp DESC LIMIT 50")
    fun getLogsFlow(uid: Long): Flow<List<GameLog>>

    @Insert
    suspend fun insertLog(log: GameLog)

    @Query("DELETE FROM game_logs WHERE uid = :uid AND id NOT IN (SELECT id FROM game_logs WHERE uid = :uid ORDER BY timestamp DESC LIMIT 100)")
    suspend fun trimOldLogs(uid: Long)

    @Query("SELECT * FROM raid_sessions WHERE uid = :uid")
    suspend fun getRaidSession(uid: Long): RaidSession?

    @Query("SELECT * FROM raid_sessions WHERE uid = :uid")
    fun getRaidSessionFlow(uid: Long): Flow<RaidSession?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRaidSession(session: RaidSession)

    @Query("DELETE FROM raid_sessions WHERE uid = :uid")
    suspend fun deleteRaidSession(uid: Long)

    @Query("SELECT * FROM graves")
    suspend fun getAllGraves(): List<Grave>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGrave(grave: Grave)

    @Delete
    suspend fun deleteGrave(grave: Grave)

    @Query("SELECT * FROM bestiary_entries")
    fun getBestiaryFlow(): Flow<List<BestiaryEntry>>

    @Query("SELECT * FROM bestiary_entries WHERE enemy_id = :enemyId")
    suspend fun getBestiaryEntry(enemyId: String): BestiaryEntry?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBestiaryEntry(entry: BestiaryEntry)

    @Query("SELECT * FROM radio_messages WHERE uid = :uid ORDER BY timestamp DESC")
    fun getRadioMessagesFlow(uid: Long): Flow<List<RadioMessageEntity>>

    @Query("SELECT * FROM radio_messages WHERE uid = :uid")
    suspend fun getAllRadioMessages(uid: Long): List<RadioMessageEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRadioMessage(message: RadioMessageEntity)

    @Update
    suspend fun updateRadioMessage(message: RadioMessageEntity)

    @Query("SELECT COUNT(*) FROM radio_messages WHERE uid = :uid AND isClaimed = 0")
    fun getUnclaimedMessagesCountFlow(uid: Long): Flow<Int>

    @Query("SELECT * FROM user_equipment WHERE player_uid = :uid")
    suspend fun getUserEquipment(uid: Long): UserEquipment?

    @Query("SELECT * FROM user_equipment WHERE player_uid = :uid")
    fun getUserEquipmentFlow(uid: Long): Flow<UserEquipment?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveUserEquipment(equipment: UserEquipment)

    // --- World Boss (persistent shared pool) ---
    @Query("SELECT * FROM world_boss_state WHERE id = 1")
    suspend fun getWorldBossState(): WorldBossState?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWorldBossState(state: WorldBossState)

    @Query(
        "INSERT INTO world_boss_contrib (player_uid, total_damage) VALUES (:uid, :damage) " +
            "ON CONFLICT(player_uid) DO UPDATE SET total_damage = total_damage + :damage"
    )
    suspend fun addWorldBossDamage(uid: Long, damage: Long)

    @Query(
        "SELECT p.username AS username, c.total_damage AS total_damage " +
            "FROM world_boss_contrib c JOIN players p ON p.uid = c.player_uid " +
            "ORDER BY c.total_damage DESC LIMIT :limit"
    )
    suspend fun getTopWorldBossContributors(limit: Int): List<BossContributor>
}

val MIGRATION_10_11 = object : Migration(10, 11) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE players ADD COLUMN overdriveCharge INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE players ADD COLUMN overchargeTier INTEGER NOT NULL DEFAULT 0")
    }
}

val MIGRATION_11_12 = object : Migration(11, 12) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("CREATE TABLE IF NOT EXISTS user_equipment (player_uid INTEGER NOT NULL PRIMARY KEY, head TEXT, armor TEXT, weapon TEXT, chip TEXT, eidos_shard TEXT)")
    }
}

// Room's default generated name for Index(value = ["uid", "timestamp"]) on game_logs
val MIGRATION_12_13 = object : Migration(12, 13) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("CREATE INDEX IF NOT EXISTS `index_game_logs_uid_timestamp` ON `game_logs` (`uid`, `timestamp`)")
    }
}

// World Boss persistent pool + NG+ prestige counter
val MIGRATION_13_14 = object : Migration(13, 14) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS `world_boss_state` (`id` INTEGER NOT NULL PRIMARY KEY, " +
                "`boss_hp` INTEGER NOT NULL, `boss_max_hp` INTEGER NOT NULL, `cycle` INTEGER NOT NULL, " +
                "`last_reset_month` TEXT NOT NULL)"
        )
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS `world_boss_contrib` (`player_uid` INTEGER NOT NULL PRIMARY KEY, " +
                "`total_damage` INTEGER NOT NULL DEFAULT 0)"
        )
        db.execSQL("ALTER TABLE players ADD COLUMN prestige_count INTEGER NOT NULL DEFAULT 0")
    }
}

@Database(
    entities = [Player::class, InventoryItem::class, RaidSession::class, GameLog::class, VillainStatic::class, GameContent::class, Grave::class, BestiaryEntry::class, RadioMessageEntity::class, UserEquipment::class, WorldBossState::class, WorldBossContrib::class],
    version = 14,
    exportSchema = false
)
abstract class EidosDatabase : RoomDatabase() {
    abstract fun dao(): EidosDao

    companion object {
        @Volatile
        private var INSTANCE: EidosDatabase? = null

        private const val DB_NAME = "eidos_database"
        private const val RESCUE_BACKUP_NAME = "eidos_database_rescue_backup"

        /**
         * One-time raw file copy of the database before Room opens it.
         *
         * Migrations only exist for versions 10-12; older databases hit
         * fallbackToDestructiveMigration and lose all progress. This rescue
         * copy keeps the pre-wipe files on disk so data stays recoverable
         * (manually or via a future re-import). The copy is taken only while
         * no backup exists yet, so a post-wipe database can never overwrite
         * the rescue copy.
         */
        private fun createRescueBackup(context: android.content.Context) {
            try {
                val dbFile = context.getDatabasePath(DB_NAME)
                if (!dbFile.exists()) return
                val parent = dbFile.parentFile ?: return
                val backup = File(parent, RESCUE_BACKUP_NAME)
                if (backup.exists()) return
                for (suffix in listOf("", "-wal", "-shm")) {
                    val src = File(parent, DB_NAME + suffix)
                    if (src.exists()) {
                        src.copyTo(File(parent, RESCUE_BACKUP_NAME + suffix), overwrite = false)
                    }
                }
                android.util.Log.i("EidosDatabase", "Rescue backup created for legacy database")
            } catch (e: Exception) {
                android.util.Log.e("EidosDatabase", "Rescue backup failed: ${e.message}")
            }
        }

        fun getDatabase(context: android.content.Context): EidosDatabase {
            return INSTANCE ?: synchronized(this) {
                createRescueBackup(context)
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    EidosDatabase::class.java,
                    DB_NAME
                )
                .addMigrations(MIGRATION_10_11, MIGRATION_11_12, MIGRATION_12_13, MIGRATION_13_14)
                // Last resort only: wipe instead of crash for unknown old
                // versions. Data remains recoverable via RESCUE_BACKUP_NAME.
                .fallbackToDestructiveMigration()
                .fallbackToDestructiveMigrationOnDowngrade()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

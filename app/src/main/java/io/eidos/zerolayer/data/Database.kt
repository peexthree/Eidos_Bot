package io.eidos.zerolayer.data

import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow

@Dao
interface EidosDao {
    @Query("SELECT * FROM players WHERE uid = :uid")
    suspend fun getPlayer(uid: Long): Player?

    @Query("SELECT * FROM players WHERE uid = :uid")
    fun getPlayerFlow(uid: Long): Flow<Player?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPlayer(player: Player)

    @Update
    suspend fun updatePlayer(player: Player)

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
}

val MIGRATION_10_11 = object : Migration(10, 11) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE players ADD COLUMN overdriveCharge INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE players ADD COLUMN overchargeTier INTEGER NOT NULL DEFAULT 0")
    }
}

@Database(
    entities = [Player::class, InventoryItem::class, RaidSession::class, GameLog::class, VillainStatic::class, GameContent::class, Grave::class, BestiaryEntry::class, RadioMessageEntity::class],
    version = 11,
    exportSchema = false
)
abstract class EidosDatabase : RoomDatabase() {
    abstract fun dao(): EidosDao

    companion object {
        @Volatile
        private var INSTANCE: EidosDatabase? = null

        fun getDatabase(context: android.content.Context): EidosDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    EidosDatabase::class.java,
                    "eidos_database"
                )
                .addMigrations(MIGRATION_10_11)
                .fallbackToDestructiveMigrationOnDowngrade()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

package io.eidos.zerolayer.data

import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SupabaseDtoTest {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }

    @Test
    fun testAuthResponseSuccessDeserialization() {
        val rawJson = """
            {
                "access_token": "mock_jwt_token_12345",
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": "mock_refresh_token_abcde",
                "user": {
                    "id": "user-uuid-9876",
                    "email": "op_test@eidos.app",
                    "user_metadata": { "username": "Operator_Zero" }
                }
            }
        """.trimIndent()

        val response = json.decodeFromString<AuthResponse>(rawJson)
        assertEquals("mock_jwt_token_12345", response.accessToken)
        assertEquals("mock_refresh_token_abcde", response.refreshToken)
        assertNotNull(response.user)
        assertEquals("user-uuid-9876", response.user?.id)
        assertEquals("Operator_Zero", response.user?.userMetadata?.get("username"))
    }

    @Test
    fun testAuthResponseErrorDeserialization() {
        val rawJson = """
            {
                "error": "invalid_grant",
                "error_description": "Invalid login credentials",
                "msg": "Invalid login credentials"
            }
        """.trimIndent()

        val response = json.decodeFromString<AuthResponse>(rawJson)
        assertEquals("invalid_grant", response.error)
        assertEquals("Invalid login credentials", response.errorDescription)
        assertEquals("Invalid login credentials", response.msg)
    }

    @Test
    fun testRpcRaidRewardRequestSerialization() {
        val request = RpcRaidRewardRequest(
            exp = 250L,
            biocoins = 1200L,
            depth = 42
        )

        val raw = json.encodeToString(RpcRaidRewardRequest.serializer(), request)
        assertTrue(raw.contains("\"p_exp\":250"))
        assertTrue(raw.contains("\"p_biocoins\":1200"))
        assertTrue(raw.contains("\"p_depth\":42"))
    }

    @Test
    fun testRpcRaidRewardResponseDeserialization() {
        val rawJson = """
            {
                "success": true,
                "exp": 1500,
                "biocoins": 3000,
                "max_depth": 75,
                "message": "REWARD_SYNCED"
            }
        """.trimIndent()

        val response = json.decodeFromString<RpcRaidRewardResponse>(rawJson)
        assertTrue(response.success)
        assertEquals(1500L, response.exp)
        assertEquals(3000L, response.biocoins)
        assertEquals(75, response.maxDepth)
        assertEquals("REWARD_SYNCED", response.message)
    }

    @Test
    fun testSupabaseInventoryItemSerializationRoundtrip() {
        val item = SupabaseInventoryItem(
            id = "item-uuid-101",
            playerId = "player_abc",
            itemId = "cyber_katana",
            quantity = 1,
            isEquipped = true
        )

        val raw = json.encodeToString(SupabaseInventoryItem.serializer(), item)
        val decoded = json.decodeFromString<SupabaseInventoryItem>(raw)

        assertEquals(item.id, decoded.id)
        assertEquals(item.playerId, decoded.playerId)
        assertEquals(item.itemId, decoded.itemId)
        assertEquals(item.quantity, decoded.quantity)
        assertEquals(item.isEquipped, decoded.isEquipped)
    }

    @Test
    fun testSupabasePlayerSerializationRoundtrip() {
        val player = SupabasePlayer(
            id = "player-uuid-555",
            deviceId = "dev_123",
            username = "NetRunner",
            level = 5,
            exp = 1200L,
            biocoins = 4500L,
            hp = 95,
            energy = 80,
            rank = "Элита",
            stateVersion = 3,
            updatedAt = null
        )

        val raw = json.encodeToString(SupabasePlayer.serializer(), player)
        val decoded = json.decodeFromString<SupabasePlayer>(raw)

        assertEquals(player.id, decoded.id)
        assertEquals(player.deviceId, decoded.deviceId)
        assertEquals(player.username, decoded.username)
        assertEquals(player.level, decoded.level)
        assertEquals(player.exp, decoded.exp)
        assertEquals(player.biocoins, decoded.biocoins)
        assertEquals(player.hp, decoded.hp)
        assertEquals(player.energy, decoded.energy)
        assertEquals(player.rank, decoded.rank)
        assertEquals(player.stateVersion, decoded.stateVersion)
        assertEquals(player.updatedAt, decoded.updatedAt)
    }

    @Test
    fun testSupabasePlayerOmitsNullId() {
        val player = SupabasePlayer(
            deviceId = "dev_999",
            username = "Ghost_99"
        )
        val raw = json.encodeToString(SupabasePlayer.serializer(), player)
        assertTrue(!raw.contains("\"id\":null"))
        assertTrue(!raw.contains("\"id\":"))
    }

    @Test
    fun testSupabaseInventoryItemOmitsNullId() {
        val item = SupabaseInventoryItem(
            playerId = "player-uuid-1",
            itemId = "cyber_katana"
        )
        val raw = json.encodeToString(SupabaseInventoryItem.serializer(), item)
        assertTrue(!raw.contains("\"id\":null"))
        assertTrue(!raw.contains("\"id\":"))
    }
}
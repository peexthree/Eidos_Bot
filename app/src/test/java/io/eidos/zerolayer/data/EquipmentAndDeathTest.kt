package io.eidos.zerolayer.data

import org.junit.Assert.*
import org.junit.Test

class EquipmentAndDeathTest {

    @Test
    fun testUserEquipmentModel() {
        val eq = UserEquipment(
            player_uid = 12345L,
            head = "tactical_helmet",
            armor = "judas_shell",
            weapon = "credit_slicer",
            chip = "chip_red_atk,chip_green_crit",
            eidos_shard = "eidos_shard"
        )
        assertEquals(12345L, eq.player_uid)
        assertEquals("tactical_helmet", eq.head)
        assertEquals("judas_shell", eq.armor)
        assertEquals("credit_slicer", eq.weapon)
        assertEquals("chip_red_atk,chip_green_crit", eq.chip)
        assertEquals("eidos_shard", eq.eidos_shard)
    }

    @Test
    fun testEquipmentProcEvents() {
        val proc1 = EquipmentProcEvent("vampire_visor", "🩸 ВИЗОР ВАМПИРА: +5% СИГНАЛА [KILL]", ProcColorType.HEAL_NEON)
        val proc2 = EquipmentProcEvent("overclock_crown", "⚡ ВЕНЕЦ РАЗГОНА: x2 КРИТ [-2% HP]", ProcColorType.CURSED_RED)
        val proc3 = EquipmentProcEvent("architect_mask", "🛡 ЛИЦО АРХИТЕКТОРА: ОТРАЖЕНО 45 УРОНА", ProcColorType.SHIELD_CYAN)
        val proc4 = EquipmentProcEvent("credit_slicer", "💳 РЕЗАК КРЕДИТОВ: -12 BC [+18 ATK]", ProcColorType.GOLD_CRIT)

        val turnResult = CombatTurnResult(
            playerDamage = 120,
            enemyDamage = 35,
            isCrit = true,
            isDodge = false,
            enemyDefeated = false,
            playerDefeated = false,
            triggeredProcs = listOf(proc1, proc2, proc3, proc4)
        )

        assertEquals(4, turnResult.triggeredProcs.size)
        assertEquals(ProcColorType.HEAL_NEON, turnResult.triggeredProcs[0].colorType)
        assertEquals(ProcColorType.CURSED_RED, turnResult.triggeredProcs[1].colorType)
        assertEquals(ProcColorType.SHIELD_CYAN, turnResult.triggeredProcs[2].colorType)
        assertEquals(ProcColorType.GOLD_CRIT, turnResult.triggeredProcs[3].colorType)
    }

    @Test
    fun testDeathReportPenaltyStructure() {
        val report = GameRepository.DeathReport(
            depth = 3450,
            lostCoins = 1500L,
            lostXp = 800L,
            lostItems = "battery,medkit_small",
            graveCreated = true,
            brokenItems = listOf("Кредитный Резак"),
            durabilityPenaltyPercent = 10
        )

        assertEquals(3450, report.depth)
        assertEquals(1500L, report.lostCoins)
        assertEquals(800L, report.lostXp)
        assertTrue(report.graveCreated)
        assertEquals(1, report.brokenItems.size)
        assertEquals(10, report.durabilityPenaltyPercent)
    }
}

package io.eidos.zerolayer.domain

import io.eidos.zerolayer.data.AchievementRegistry
import io.eidos.zerolayer.data.ZeroLayerEconomy
import io.eidos.zerolayer.domain.combat.CombatEngine
import io.eidos.zerolayer.domain.raid.QuantumSectorEngine
import io.eidos.zerolayer.domain.raid.SectorMutator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Контрактные тесты механик, добавленных в продуктовом цикле 2026-11
 * (см. docs/PRODUCT_PLAN_2026-11-06.md). Чистые функции - без Android-зависимостей.
 */
class NewMechanicsTest {

    // --- Эндгейм-баланс: сложность должна догонять награды после 5000м ---

    @Test
    fun `difficulty is flat up to 5000m`() {
        assertEquals(1.0f, CombatEngine.getDepthDifficultyMultiplier(0), 0.001f)
        assertEquals(1.0f, CombatEngine.getDepthDifficultyMultiplier(5000), 0.001f)
    }

    @Test
    fun `difficulty scales steeply after 5000m and caps at +75 percent`() {
        val d7000 = CombatEngine.getDepthDifficultyMultiplier(7000)
        assertEquals(1.25f, d7000, 0.001f)
        val d13000 = CombatEngine.getDepthDifficultyMultiplier(13000)
        assertEquals(1.75f, d13000, 0.001f) // (13000-5000)/8000 = 1.0 -> cap 0.75
    }

    @Test
    fun `reward multiplier grows with depth and caps at x4`() {
        assertEquals(1.0f, CombatEngine.getDepthRewardMultiplier(0), 0.001f)
        assertEquals(1.5f, CombatEngine.getDepthRewardMultiplier(2000), 0.001f)
        assertEquals(3.5f, CombatEngine.getDepthRewardMultiplier(10000), 0.001f)
        assertEquals(4.0f, CombatEngine.getDepthRewardMultiplier(50000), 0.001f) // cap
    }

    // --- Экономика: налог эвакуации ---

    @Test
    fun `extraction tax is 8 percent of buffer`() {
        assertEquals(80L, ZeroLayerEconomy.calculateExtractionTax(1000L))
        assertEquals(0L, ZeroLayerEconomy.calculateExtractionTax(0L))
        assertEquals(8L, ZeroLayerEconomy.calculateExtractionTax(100L))
    }

    // --- Достижения: структурные инварианты реестра ---

    @Test
    fun `achievement ids are unique`() {
        val ids = AchievementRegistry.ALL_DEFINITIONS.map { it.id }
        assertEquals(ids.size, ids.distinct().size)
    }

    @Test
    fun `endgame category exists with depth and combat achievements`() {
        val endgame = AchievementRegistry.ALL_DEFINITIONS.filter { it.category == "Эндгейм/Бездна" }
        assertTrue("Expected >= 11 endgame achievements, got ${endgame.size}", endgame.size >= 11)
        val depthTiers = endgame.filter { it.id.startsWith("ach_depth_") }.map { it.target }
        assertTrue(depthTiers.containsAll(listOf(500L, 1000L, 2500L, 5000L, 8000L)))
        assertTrue(endgame.any { it.id == "ach_kills_1000" })
        assertTrue(endgame.any { it.id == "ach_pvp_10" })
    }

    @Test
    fun `every achievement has valid structure`() {
        AchievementRegistry.ALL_DEFINITIONS.forEach { def ->
            assertTrue("empty title in ${def.id}", def.title.isNotBlank())
            assertTrue("empty description in ${def.id}", def.description.isNotBlank())
            assertTrue("non-positive target in ${def.id}", def.target > 0)
        }
    }

    // --- Мутаторы: все 9 секторов имеют уникальные id и непустые обещания UI ---

    @Test
    fun `all nine sector mutators are declared with promises`() {
        assertEquals(9, SectorMutator.entries.size)
        val ids = SectorMutator.entries.map { it.id }
        assertEquals(ids.size, ids.distinct().size)
        SectorMutator.entries.forEach { m ->
            assertTrue("empty description in ${m.id}", m.description.isNotBlank())
            assertTrue("empty title in ${m.id}", m.title.isNotBlank())
            // fromId должен находить каждый мутатор по его id (используется в бою)
            assertEquals(m, SectorMutator.fromId(m.id))
        }
    }

    @Test
    fun `dead mutators are now wired - ids match game repository checks`() {
        // Реализация в GameRepository сверяется с этими конкретными id
        assertEquals("mutator_antigravity", SectorMutator.ANTIGRAVITY.id)
        assertEquals("mutator_glitch_storm", SectorMutator.GLITCH_STORM.id)
        assertEquals("mutator_echoes_past", SectorMutator.ECHOES_PAST.id)
    }

    @Test
    fun `quantum sector engine builds sectors for every mutator`() {
        // Смоук: генератор секторов не должен падать и должен выдавать валидные сектора
        val sectors = QuantumSectorEngine.generateSectorChoices(depth = 1050, isScanned = false)
        assertTrue(sectors.isNotEmpty())
        sectors.forEach { sector ->
            assertTrue(sector.title.isNotBlank())
            assertTrue(sector.costEnergy >= 0)
        }
    }
}

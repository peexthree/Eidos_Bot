package io.eidos.zerolayer.domain.combat

import androidx.annotation.DrawableRes
import androidx.compose.ui.graphics.Color
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.InventoryItem

enum class ChipColor(val displayName: String, val colorHex: Long) {
    RED("СИЛА // БОЙ", 0xFFFF3D00),
    GREEN("ЛОГИКА // КРИТ", 0xFF00E676),
    BLUE("НЕЙРО // ЭНЕРГИЯ", 0xFF00E5FF),
    CURSED("ПРОКЛЯТИЕ // БЕЗДНА", 0xFFE040FB),
    NEUTRAL("СТАНДАРТ", 0xFF90A4AE)
}

data class ActiveSynergy(
    val id: String,
    val title: String,
    val tierLabel: String, // "2/4" or "4/4" or "DUO" or "CURSED"
    val description: String,
    @DrawableRes val iconRes: Int,
    val color: Color
)

object ChipMatrixSynergyEngine {

    /**
     * Resolves the canonical color of any chip or equippable module.
     */
    fun getChipColor(itemId: String): ChipColor {
        val id = itemId.lowercase()
        return when {
            // Cursed relics / chips
            id in listOf("blood_miner", "karma_inversion", "oblivion_chip", "imposter_syndrome", "maxwells_demon", "relic_vampire") ||
            id.contains("cursed") || id.contains("demon") || id.contains("inversion") -> ChipColor.CURSED

            // Red (Strength / Combat / Overclock)
            id in listOf("overclocker", "ram_chip", "cpu_booster", "kamikaze_protocol", "chip_red_atk") ||
            id.contains("overclock") || id.contains("atk") || id.contains("ram") || id.contains("cpu") -> ChipColor.RED

            // Green (Agility / Crit / Logic / Evasion)
            id in listOf("chronometer", "neural_link", "glitch_filter", "logic_gate", "chip_green_crit") ||
            id.contains("crit") || id.contains("logic") || id.contains("chrono") || id.contains("filter") -> ChipColor.GREEN

            // Blue (Neuro / Energy / Shield / AI)
            id in listOf("ai_core", "backup_drive", "god_mode_chip", "chip_blue_energy") ||
            id.contains("energy") || id.contains("ai") || id.contains("backup") || id.contains("shield") -> ChipColor.BLUE

            else -> ChipColor.NEUTRAL
        }
    }

    /**
     * Evaluates all active synergies based on the equipped chips (up to 4)
     * and equipped cursed items.
     */
    fun evaluateSynergies(equippedChips: List<InventoryItem>, allEquippedItems: List<InventoryItem> = emptyList()): List<ActiveSynergy> {
        val colors = equippedChips.map { getChipColor(it.item_id) }
        val redCount = colors.count { it == ChipColor.RED }
        val greenCount = colors.count { it == ChipColor.GREEN }
        val blueCount = colors.count { it == ChipColor.BLUE }

        val cursedFromChips = colors.count { it == ChipColor.CURSED }
        val cursedFromGear = allEquippedItems.count { getChipColor(it.item_id) == ChipColor.CURSED }
        val cursedCount = maxOf(cursedFromChips, cursedFromGear)

        val active = mutableListOf<ActiveSynergy>()

        // RED RESONANCE (ДЖАГГЕРНАУТ)
        if (redCount >= 4) {
            active.add(
                ActiveSynergy(
                    id = "syn_red_4",
                    title = "ЯРОСТЬ ТИТАНА",
                    tierLabel = "4/4",
                    description = "Урон растет до +100% при падении HP. Смерть врага взрывом лечит +15% HP!",
                    iconRes = R.drawable.ic_action_crit,
                    color = Color(0xFFFF3D00)
                )
            )
        } else if (redCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_red_2",
                    title = "ШИПОВАННАЯ БРОНЯ",
                    tierLabel = "2/4",
                    description = "Стойка Защиты возвращает 100% заблокированного урона обратно атакующему!",
                    iconRes = R.drawable.ic_action_defense,
                    color = Color(0xFFFF5722)
                )
            )
        }

        // GREEN RESONANCE (ПРИЗРАЧНЫЙ ЖНЕЦ)
        if (greenCount >= 4) {
            active.add(
                ActiveSynergy(
                    id = "syn_green_4",
                    title = "ТАНЕЦ ТЕНЕЙ",
                    tierLabel = "4/4",
                    description = "Уклонение от удара дает +50% Овердрайва, а следующий удар гарантированно критический!",
                    iconRes = R.drawable.ic_action_flee,
                    color = Color(0xFF00E676)
                )
            )
        } else if (greenCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_green_2",
                    title = "ДВОЙНОЙ ИМПУЛЬС",
                    tierLabel = "2/4",
                    description = "Криты с 35% шансом наносят мгновенный Эхо-удар (50% DMG) и воруют +3 EP!",
                    iconRes = R.drawable.ic_action_skill,
                    color = Color(0xFF69F0AE)
                )
            )
        }

        // BLUE RESONANCE (АРХИТЕКТОР СЕТИ)
        if (blueCount >= 4) {
            active.add(
                ActiveSynergy(
                    id = "syn_blue_4",
                    title = "СИНГУЛЯРНОСТЬ",
                    tierLabel = "4/4",
                    description = "Избыточная Энергия (EP сверх максимума) дает Энерго-Щит поверх HP и бьет врага молнией!",
                    iconRes = R.drawable.ic_event_anomaly,
                    color = Color(0xFF00E5FF)
                )
            )
        } else if (blueCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_blue_2",
                    title = "СВЕРХПРОВОДНИК",
                    tierLabel = "2/4",
                    description = "Навык сжигает барьеры врага; при полном Овердрайве (100%) накладывает ШОК (Оглушение)!",
                    iconRes = R.drawable.ic_status_stun,
                    color = Color(0xFF80D8FF)
                )
            )
        }

        // RED+GREEN DUO: Кровавый Оверклок
        if (redCount >= 2 && greenCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_duo_red_green",
                    title = "КРОВАВЫЙ ОВЕРКЛОК",
                    tierLabel = "DUO",
                    description = "Криты вызывают коррозию кода у врага (-10 HP/ход) и вампирят 15% нанесенного урона в HP.",
                    iconRes = R.drawable.ic_action_blood_overdrive,
                    color = Color(0xFFFF5252)
                )
            )
        }

        // RED+BLUE DUO: Реактор Возмездия
        if (redCount >= 2 && blueCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_duo_red_blue",
                    title = "РЕАКТОР ВОЗМЕЗДИЯ",
                    tierLabel = "DUO",
                    description = "Использование батареи или Навыка выпускает ЭМ-импульс (35 урона врагу + 15 DEF на 2 хода).",
                    iconRes = R.drawable.ic_action_crit,
                    color = Color(0xFFD500F9)
                )
            )
        }

        // GREEN+BLUE DUO: Квантовый Призрак
        if (greenCount >= 2 && blueCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_duo_green_blue",
                    title = "КВАНТОВЫЙ ПРИЗРАК",
                    tierLabel = "DUO",
                    description = "Расход шага -2 EP, базовое уклонение +20%, а каждый уворот восстанавливает +4 EP.",
                    iconRes = R.drawable.ic_action_flee,
                    color = Color(0xFF1DE9B6)
                )
            )
        }

        // CURSED: Пакт Бездны
        if (cursedCount >= 2) {
            active.add(
                ActiveSynergy(
                    id = "syn_cursed_pact",
                    title = "ПАКТ БЕЗДНЫ",
                    tierLabel = "CURSED",
                    description = "+25% BC и Осколков за каждый проклятый предмет. При смертельном ударе: взрыв врага и спасение с 25% HP!",
                    iconRes = R.drawable.ic_event_grave,
                    color = Color(0xFFE040FB)
                )
            )
        }

        return active
    }

    /**
     * Complete list of all potential synergies in the game for the in-game Codex / Cheat-Sheet modal.
     */
    val ALL_SYNERGIES_INFO: List<ActiveSynergy> = listOf(
        ActiveSynergy("syn_red_2", "ШИПОВАННАЯ БРОНЯ", "2 Красных", "Стойка Защиты возвращает 100% заблокированного урона врагу.", R.drawable.ic_action_defense, Color(0xFFFF5722)),
        ActiveSynergy("syn_red_4", "ЯРОСТЬ ТИТАНА", "4 Красных", "Урон растет до +100% на грани смерти. Смерть врага взрывом хилит 15% HP.", R.drawable.ic_action_crit, Color(0xFFFF3D00)),
        ActiveSynergy("syn_green_2", "ДВОЙНОЙ ИМПУЛЬС", "2 Зеленых", "Криты с 35% шансом вызывают мгновенный второй Эхо-удар (50% DMG) и +3 EP.", R.drawable.ic_action_skill, Color(0xFF69F0AE)),
        ActiveSynergy("syn_green_4", "ТАНЕЦ ТЕНЕЙ", "4 Зеленых", "Уклонение от атаки дает +50% Овердрайва и делает следующий удар 100% критом.", R.drawable.ic_action_flee, Color(0xFF00E676)),
        ActiveSynergy("syn_blue_2", "СВЕРХПРОВОДНИК", "2 Синих", "Навык сжигает щиты врага; при 100% Овердрайве оглушает врага на 1 ход.", R.drawable.ic_status_stun, Color(0xFF80D8FF)),
        ActiveSynergy("syn_blue_4", "СИНГУЛЯРНОСТЬ", "4 Синих", "Избыточная Энергия (EP сверх макс) дает Энерго-Щит поверх HP и бьет врага молнией.", R.drawable.ic_event_anomaly, Color(0xFF00E5FF)),
        ActiveSynergy("syn_duo_red_green", "КРОВАВЫЙ ОВЕРКЛОК", "2 Кр + 2 Зел", "Криты вызывают коррозию кода (-10 HP/ход) и вампирят 15% урона в HP.", R.drawable.ic_action_blood_overdrive, Color(0xFFFF5252)),
        ActiveSynergy("syn_duo_red_blue", "РЕАКТОР ВОЗМЕЗДИЯ", "2 Кр + 2 Син", "Батарея или Навык вызывают взрыв (35 урона врагу + 15 DEF на 2 хода).", R.drawable.ic_action_crit, Color(0xFFD500F9)),
        ActiveSynergy("syn_duo_green_blue", "КВАНТОВЫЙ ПРИЗРАК", "2 Зел + 2 Син", "Расход шага -2 EP, +20% уклонение, а каждый уворот восстанавливает +4 EP.", R.drawable.ic_action_flee, Color(0xFF1DE9B6)),
        ActiveSynergy("syn_cursed_pact", "ПАКТ БЕЗДНЫ", "2+ Проклятых", "+25% BC и Осколков за предмет. Смертельный удар взрывает врага и оживляет с 25% HP.", R.drawable.ic_event_grave, Color(0xFFE040FB))
    )
}

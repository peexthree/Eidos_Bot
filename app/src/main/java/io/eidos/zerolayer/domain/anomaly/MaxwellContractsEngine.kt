package io.eidos.zerolayer.domain.anomaly

import io.eidos.zerolayer.data.Player

data class MaxwellContractInfo(
    val id: String,
    val title: String,
    val conditionText: String,
    val rewardText: String,
    val icon: String,
    val isApplicable: (Player?) -> Boolean = { true }
)

object MaxwellContractsEngine {

    val CONTRACT_BLOOD_OVERCLOCK = MaxwellContractInfo(
        id = "blood_overclock",
        title = "КРОВАВЫЙ ОВЕРКЛОК",
        conditionText = "Снижает Max HP на -20% до конца рейда",
        rewardText = "+35% к урону (ATK) и +15% к шансу крита",
        icon = "🩸",
        isApplicable = { player -> (player?.hp ?: 0) > 20 }
    )

    val CONTRACT_FORTUNE_INVERSION = MaxwellContractInfo(
        id = "fortune_inversion",
        title = "ИНВЕРСИЯ ФОРТУНЫ",
        conditionText = "Входящий урон от врагов и ловушек возрастает на +25%",
        rewardText = "x2 Drop Rate на Реликвии и Зашифрованные кэши",
        icon = "🎲"
    )

    val CONTRACT_SOCKET_MUTATION = MaxwellContractInfo(
        id = "socket_mutation",
        title = "КВАНТОВАЯ МУТАЦИЯ СОКЕТА",
        conditionText = "Списывает 1500 BC из буфера/баланса",
        rewardText = "50%: Радужный сокет (+25% к любому чипу) // 50%: Сокет заблокирован",
        icon = "🔮",
        isApplicable = { player -> (player?.biocoin ?: 0L) >= 1500L }
    )

    val CONTRACT_MEMORY_SACRIFICE = MaxwellContractInfo(
        id = "memory_sacrifice",
        title = "ЖЕРТВА ПАМЯТИ",
        conditionText = "Списывает 250 XP оператора",
        rewardText = "100% Энергии + 1x Ключ Бездны (abyssal_key)",
        icon = "🧠",
        isApplicable = { player -> (player?.xp ?: 0L) >= 250L }
    )

    val CONTRACT_ENTROPY_SHIELD = MaxwellContractInfo(
        id = "entropy_shield",
        title = "ЭНТРОПИЙНЫЙ ЩИТ",
        conditionText = "Zalgo/Glitch-эффект интерфейса на 30 минут",
        rewardText = "100% иммунитет к урону от любых ловушек в рейде",
        icon = "🛡️"
    )

    val ALL_CONTRACTS = listOf(
        CONTRACT_BLOOD_OVERCLOCK,
        CONTRACT_FORTUNE_INVERSION,
        CONTRACT_SOCKET_MUTATION,
        CONTRACT_MEMORY_SACRIFICE,
        CONTRACT_ENTROPY_SHIELD
    )
}

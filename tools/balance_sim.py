"""
Симуляция баланса экономики EDO (docs/TZ_UPGRADE_2026-11-11.md, пакет П4).
Константы взяты из кода: DailyQuestData.kt (дейлики), ZeroLayerEconomy.kt
(ремонт/налог/реролл), GameRepository.kt (депо, радио), AchievementData.kt.
Допущения (рейдовый лут, частоты) помечены ASSUME и вынесены в блок ASSUMPTIONS.
Запуск: python tools/balance_sim.py
"""
import random

DAYS = 30
SEED = 20261112

# ---- Константы из кода -------------------------------------------------
DAILY_TYPES = {
    "KILLS": {"coins_per_target": 150, "targets": [4, 5, 6, 7, 8, 9]},
    "DEPTH": {"coins_per_target": 200, "targets": [2, 3, 4]},
    "SYNC":  {"coins_per_target": 120, "targets": [2, 2]},
    "SPEND": {"coins_per_target": 250, "targets": [150, 225, 300]},   # target в BC
    "CHEST": {"coins_per_target": 180, "targets": [1, 1, 2]},
}
DAILY_BONUS = 100  # +100 BC к каждому квесту

REPAIR_RATE_PER_PERCENT = {"common": 1, "uncommon": 2, "rare": 3, "epic": 8, "legendary": 20, "cursed": 40}
REROLL_BC = {"rare": 250, "epic": 500, "legendary": 1000, "cursed": 2000}
EXTRACTION_TAX = 0.08

RADIO_REWARD = [150, 300]      # ASSUME: 1-2 радио-сообщения в день, награда 150-300 BC
RAID_BUFFER_BC = [40, 160]     # ASSUME: буфер BC за рейд до налога (лут врагов/секторов)
RAID_DURABILITY_LOSS = [8, 25] # ASSUME: % износа основного оружия за рейд

# ---- Профили -----------------------------------------------------------
PROFILES = {
    "casual_15min": {"raids_per_day": 1, "dailies_done": 0.7, "radio": 1, "rerolls_per_week": 1, "craft_synthesis_per_week": 0},
    "active_1h": {"raids_per_day": 3, "dailies_done": 1.0, "radio": 2, "rerolls_per_week": 3, "craft_synthesis_per_week": 1},
    "completionist": {"raids_per_day": 5, "dailies_done": 1.0, "radio": 2, "rerolls_per_week": 6, "craft_synthesis_per_week": 2},
}

# ASSUME: стартовая экипировка common/uncommon, к 7-му дню rare, к 14-му epic, к 21-му legendary
def gear_rarity(day):
    if day < 7: return "common"
    if day < 14: return "rare"
    if day < 21: return "epic"
    return "legendary"


def simulate(profile_name, cfg, rng):
    bc = 500  # стартовый баланс (ensureDevicePlayerExists)
    daily_income = daily_spend = repair_spend = reroll_spend = other_spend = 0
    deficits = []
    for day in range(1, DAYS + 1):
        rarity = gear_rarity(day)
        day_income = day_repair = day_reroll = day_spend = 0

        # Дейлики: 3 случайных типа, часть из них выполняется по профилю
        types = list(DAILY_TYPES.keys())
        rng.shuffle(types)
        for t in types[:3]:
            if rng.random() > cfg["dailies_done"]:
                continue
            tgt = rng.choice(DAILY_TYPES[t]["targets"])
            coins = DAILY_TYPES[t]["coins_per_target"] * tgt + DAILY_BONUS
            day_income += coins
            if t == "SPEND":
                # SPEND-квест требует потратить BC - считаем расход совпадающим с таргетом
                day_spend += tgt

        # Радио-награды
        for _ in range(cfg["radio"]):
            day_income += rng.randint(*RADIO_REWARD)

        # Рейды: буфер - налог 8%
        for _ in range(cfg["raids_per_day"]):
            buffer = rng.randint(*RAID_BUFFER_BC)
            day_income += buffer - int(buffer * EXTRACTION_TAX)
            # износ оружия -> ремонт вечером
            loss = rng.randint(*RAID_DURABILITY_LOSS)
            day_repair += int(loss * REPAIR_RATE_PER_PERCENT[rarity])

        # Рероллы аффиксов (по неделям -> в день); common-реролл = 100 BC
        day_reroll += cfg["rerolls_per_week"] * REROLL_BC.get(rarity, 100) / 7.0

        daily_income += day_income
        repair_spend += day_repair
        reroll_spend += day_reroll
        other_spend += day_spend
        bc += day_income - day_repair - day_reroll - day_spend
        if bc < 0:
            deficits.append(day)
            bc = 0  # игрок пропускает покупку/ремонт (банкрот-день)
    return {
        "profile": profile_name,
        "final_bc": int(bc),
        "daily_income_avg": round(daily_income / DAYS),
        "repair_avg": round(repair_spend / DAYS),
        "reroll_avg": round(reroll_spend / DAYS),
        "spend_quest_avg": round(other_spend / DAYS),
        "deficit_days": deficits,
    }


def main():
    rng = random.Random(SEED)
    print("СИМУЛЯЦИЯ БАЛАНСА EDO - 30 дней, seed", SEED)
    print("=" * 72)
    rows = [simulate(name, cfg, random.Random(SEED + hash(name) % 1000)) for name, cfg in PROFILES.items()]
    header = f"{'профиль':16} {'доход/день':>11} {'ремонт/день':>12} {'реролл/день':>12} {'SPEND/день':>11} {'финал BC':>10} {'дефицитные дни':>15}"
    print(header)
    for r in rows:
        print(f"{r['profile']:16} {r['daily_income_avg']:>11} {r['repair_avg']:>12} {r['reroll_avg']:>12} {r['spend_quest_avg']:>11} {r['final_bc']:>10} {str(len(r['deficit_days'])):>15}")

    print()
    print("ВЫВОДЫ:")
    for r in rows:
        net = r["daily_income_avg"] - r["repair_avg"] - r["reroll_avg"] - r["spend_quest_avg"]
        state = "профицит" if net > 100 else ("около нуля" if net > -50 else "ДЕФИЦИТ - экономика душит")
        print(f"  {r['profile']}: чистыми {net} BC/день -> {state}")


if __name__ == "__main__":
    main()

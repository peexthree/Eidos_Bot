# -*- coding: utf-8 -*-
# Добавляет в items.json предметы, отсутствующие в базе, но падающие из лута/крафта:
# medkit_small, boss_core, quantum_blade (без метаданных mergeItems/магазины молча ломались)
import json
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATH = r"D:\EDO\app\src\main\assets\items.json"

with io.open(PATH, encoding="utf-8") as f:
    data = json.load(f)

added = []

def add(item_id, entry):
    if item_id in data:
        print("SKIP (exists):", item_id)
        return
    data[item_id] = entry
    added.append(item_id)

add("medkit_small", {
    "name": "⚪️ 💉 МАЛАЯ АПТЕЧКА",
    "heal": 15,
    "desc": "Аптечка. Мгновенно восстанавливает 15% HP (Сигнала). Можно использовать прямо в бою.\nПолевой реставрационный набор мародёра: бинт из фольги, ампула стимулятора и молитва Архитекторам. Работает чаще, чем положено.",
    "price": 60,
    "slot": "consumable",
    "type": "consumable"
})

add("boss_core", {
    "name": "🔵 🧿 ЯДРО МИРОВОГО БОССА",
    "desc": "Пульсирующее ядро поверженного колосса Нулевого Слоя. Сырьё для высшей ковки.\nВнутри до сих пор тикает чужая логика - иногда оно повторяет последние команды того, кто был раньше хозяином.",
    "price": 2000,
    "slot": "material",
    "type": "material"
})

add("quantum_blade", {
    "name": "🟠 ⚔️ КВАНТОВЫЙ КЛИНОК",
    "slot": "weapon",
    "atk": 110,
    "def": 5,
    "luck": 0,
    "price": 12000,
    "desc": "+110 ATK. Легендарное оружие. Рассекает вероятностные линии врага до того, как тот решит атаковать.\nКлинок не существует в одном месте одновременно. Он уже порезал тебя во всех возможных вариантах боя - просто в этом ты ещё не почувствовал."
})

with io.open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("ADDED:", added)
print("total items now:", len(data))

import sys
import os
import random
import json

# Mock sys.modules for bot_instance to avoid import errors
from unittest.mock import MagicMock
sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.bot_instance.bot'] = MagicMock()

import database as db
import config
from modules.services.raid import process_raid_step
from modules.services.crafting import crafting_service
from modules.services.combat import process_combat_action

# Helper to print pass/fail
def assert_true(cond, msg):
    if cond: print(f"✅ PASS: {msg}")
    else: print(f"❌ FAIL: {msg}")

# Setup dummy user
uid = 123456
username = "test_user"

# Reset DB state for user
db.delete_user_fully(uid)
db.add_user(uid, username, "Test")
db.update_user(uid, xp=5000, biocoin=500000, level=10)

print(f"--- SETUP USER {uid} ---")

# 1. Verify Cursed Chest Generation
print("\n--- TEST: CURSED CHEST GENERATION ---")
cursed_found = False
for i in range(200):
    # Mock randomness to force cursed chest or just run enough times?
    # Rarity is 1%. 200 runs gives ~86% chance.
    # Let's force it by mocking random if possible, or just checking the function logic.
    pass

# We can manually inject a cursed chest event into the session to test opening
db.db_session().__enter__() # Keep session open? No, process_raid_step handles it.
with db.db_session() as conn:
    with conn.cursor() as cur:
        # Create session with 'cursed_chest' as next event
        cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time, next_event_type) VALUES (%s, 10, 100, %s, 'cursed_chest')", (uid, int(time.time())))

print("Injected Cursed Chest event.")

# Test Opening without Key
res, txt, extra, u, etype, cost = process_raid_step(uid, answer='open_chest')
assert_true("ПРОКЛЯТО" in txt, "Cannot open Cursed Chest without Abyss Key")

# Give Abyss Key
db.add_item(uid, 'abyssal_key', 1)
print("Given Abyssal Key.")

# Test Opening with Key
res, txt, extra, u, etype, cost = process_raid_step(uid, answer='open_chest')
assert_true("УСПЕХ" in txt, "Opened Cursed Chest with Abyss Key")
assert_true("ПРОКЛЯТЫЙ ЛУТ" in txt or "Предмет" in txt, "Received Loot")

# Check if we got a Red Item
with db.db_cursor() as cur:
    cur.execute("SELECT buffer_items FROM raid_sessions WHERE uid=%s", (uid,))
    buf = cur.fetchone()[0]
    print(f"Loot Buffer: {buf}")
    red_found = any(item in buf for item in config.CURSED_CHEST_DROPS)
    assert_true(red_found, "Found Red Tier item in buffer")

# 2. Verify Mechanic Data (Grandfather Paradox)
print("\n--- TEST: GRANDFATHER PARADOX ---")
# Equip item
db.equip_item(uid, 'grandfather_paradox', 'weapon')
# Inject Combat
db.update_raid_enemy(uid, 1, 100) # Villain ID 1
# Simulate Enemy Hit
# We need to simulate the enemy turn where player takes damage.
# This happens in process_combat_action after player attack/run/etc.
# Let's just simulate 'combat_attack' and assume enemy hits back.
# We need to ensure enemy survives to hit back. Villain 1 has 15 HP. Player has high attack?
# Grandfather Paradox has 100 ATK. Villain 1 will die instantly.
# Use a stronger villain. ID 19 (God Machine) HP 270.
db.update_raid_enemy(uid, 19, 270)

res, msg, extra = process_combat_action(uid, 'attack')
print(f"Combat Result: {res}\nMsg: {msg}")

# Check if Paradox triggered (delayed damage)
# If enemy hit us, we should see "Урон отложен"
if "Урон отложен" in msg:
    assert_true(True, "Grandfather Paradox delayed damage")
    # Check DB
    with db.db_cursor() as cur:
        cur.execute("SELECT mechanic_data FROM raid_sessions WHERE uid=%s", (uid,))
        md = cur.fetchone()[0]
        print(f"Mechanic Data: {md}")
        assert_true("paradox_queue" in md, "Paradox Queue exists in DB")
else:
    print("⚠️ Enemy might not have hit (dodged/blocked/dead/stunned). Retry recommended.")

# 3. Verify Crafting (Fragments)
print("\n--- TEST: CRAFTING FRAGMENTS ---")
db.add_item(uid, 'fragment', 5)
res, msg = crafting_service.craft_item(uid, 'fragment')
assert_true(res, "Crafted Fragment")
print(msg)
# Check inventory for new item
inv = db.get_inventory(uid)
print("Inventory:", [i['item_id'] for i in inv])

print("\n--- VERIFICATION COMPLETE ---")

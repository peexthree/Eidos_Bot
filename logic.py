import random, time
from config import *
import database as db

def process_xp(uid, amount):
    u = db.get_user(uid)
    if not u: return 0
    new_xp = u['xp'] + amount
    new_lvl = u['level']
    for l, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr: new_lvl = l; break
    db.update_user(uid, xp=new_xp, level=new_lvl)
    return amount

def raid_step_logic(uid):
    conn = db.get_db_connection()
    cur = conn.cursor(psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    
    # Берем случайное событие
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    event = cur.fetchone()
    
    riddle_data = None
    display_text = event['text']
    
    # --- SMART RIDDLE EXTRACTION ---
    if "(Ответ:" in display_text:
        parts = display_text.split("(Ответ:")
        question = parts[0].strip()
        correct = parts[1].split(")")[0].strip()
        
        # Решаем, какие обманки подсунуть
        pool = SYNC_TERMS if any(t.lower() in correct.lower() for t in SYNC_TERMS) else GENERAL_TERMS
        wrong = random.sample([t for t in pool if t.lower() != correct.lower()], 2)
        options = wrong + [correct]
        random.shuffle(options)
        
        riddle_data = {"correct": correct, "options": options}
        display_text = question + "\n\n🧩 **ДЕШИФРОВКА ТЕРМИНА:**"

    new_depth = s['depth'] + 1
    dmg = 10 if event['type'] == 'trap' else random.randint(2, 5)
    new_signal = max(0, s['signal'] - dmg)
    new_buffer = s['buffer_xp'] + (event['val'] if event['type'] == 'loot' else 0)
    
    if new_signal <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        conn.commit(); conn.close(); return False, "💀 **СИГНАЛ ПОТЕРЯН.**", None
        
    cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, buffer_xp=%s WHERE uid=%s", (new_depth, new_signal, new_buffer, uid))
    conn.commit(); conn.close()
    
    icon = "🟢" if new_signal > 60 else "🟡" if new_signal > 30 else "🔴"
    msg = f"⚓️ **ГЛУБИНА: {new_depth} м**\n\n{display_text}\n\n🎒 **В МЕШКЕ:** {new_buffer} XP | 📡 **СИГНАЛ:** {icon} {new_signal}%"
    return True, msg, riddle_data

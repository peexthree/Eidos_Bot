import random, time
from datetime import datetime
from config import *
import database as db

def process_xp_logic(uid, amount):
    u = db.get_user(uid)
    if not u: return False, 0
    today = datetime.now().date()
    last_active = u['last_active']
    if isinstance(last_active, str): last_active = datetime.strptime(last_active, "%Y-%m-%d").date()
    
    new_streak = u['streak']
    if last_active < today:
        if (today - last_active).days == 1: new_streak += 1
        else:
            if u['cryo'] > 0: db.update_user(uid, cryo=u['cryo']-1)
            else: new_streak = 1
        db.update_user(uid, streak=new_streak, last_active=today)

    total_gain = amount + (new_streak * 5)
    new_xp = u['xp'] + total_gain
    new_lvl = u['level']
    for l, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr: new_lvl = l; break
    db.update_user(uid, xp=new_xp, level=new_lvl)
    return (new_l > u['level'] if 'new_l' in locals() else False), total_gain

def get_content_logic(c_type, path='general', level=1):
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    if c_type == 'signal':
        cur.execute("SELECT id, text FROM content WHERE type = 'signal' ORDER BY RANDOM() LIMIT 1")
    else:
        cur.execute("SELECT id, text FROM content WHERE type = 'protocol' AND (path = %s OR path = 'general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, level))
    res = cur.fetchone()
    conn.close()
    return res

def raid_step_logic(uid):
    conn = db.get_db_connection(); cur = conn.cursor(cursor_factory=db.RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: return False, "Сессия не найдена", None
    
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    event = cur.fetchone()
    if not event: event = {"text": "Тишина. Иди вперед.", "type": "empty", "val": 5}

    riddle = None
    text = event['text']
    if "(Ответ:" in text:
        parts = text.split("(Ответ:")
        q = parts[0].strip()
        ans = parts[1].split(")")[0].strip()
        pool = SYNC_TERMS if any(t.lower() in ans.lower() for t in SYNC_TERMS) else GENERAL_TERMS
        wrong = random.sample([t for t in pool if t.lower() != ans.lower()], 2)
        opts = wrong + [ans]; random.shuffle(opts)
        riddle = {"correct": ans, "options": opts}
        text = q + "\n\n🧩 **ДЕШИФРОВКА ТЕРМИНА:**"

    dmg = event['val'] if event['type'] == 'trap' else random.randint(2, 5)
    new_sig = max(0, s['signal'] - (dmg if event['type'] != 'heal' else -15))
    if new_sig <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,)); conn.commit(); conn.close()
        return False, f"💀 **СИГНАЛ ПОТЕРЯН.**\nПотеряно в буфере.", None

    cur.execute("UPDATE raid_sessions SET depth=depth+1, signal=%s, buffer_xp=buffer_xp+%s WHERE uid=%s", 
                (new_sig, (event['val'] if event['type'] == 'loot' else 0), uid))
    conn.commit(); conn.close()
    
    icon = "🟢" if new_sig > 60 else "🟡" if new_sig > 30 else "🔴"
    msg = f"⚓️ ГЛУБИНА: {s['depth']+1}м\n\n{text}\n\n🎒 Буфер: {s['buffer_xp']} XP | 📡 Сигнал: {icon} {new_sig}%"
    return True, msg, riddle

import random, time
from datetime import datetime, timedelta
from config import *
import database as db

def process_xp_logic(uid, amount):
    u = db.get_user(uid)
    if not u: return False, 0
    
    today = datetime.now().date()
    # Обработка даты из БД
    last_active = u['last_active']
    if isinstance(last_active, str): last_active = datetime.strptime(last_active, "%Y-%m-%d").date()
    
    new_streak = u['streak']
    if last_active < today:
        if (today - last_active).days == 1:
            new_streak += 1
        else:
            if u['cryo'] > 0:
                db.update_user(uid, cryo=u['cryo']-1)
            else:
                new_streak = 1
        db.update_user(uid, streak=new_streak, last_active=today)

    total_gain = amount + (new_streak * 5)
    new_xp = u['xp'] + total_gain
    
    # Расчет уровня
    new_lvl = u['level']
    for lvl, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr: new_lvl = lvl; break
    
    db.update_user(uid, xp=new_xp, level=new_lvl)
    return (new_lvl > u['level']), total_gain

def raid_step_logic(uid):
    conn = db.get_db_connection(); cur = conn.cursor(cursor_factory=db.RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    event = cur.fetchone()
    if not event: return True, "Тишина...", None

    # Вырезаем ответ для кнопок
    riddle = None
    text = event['text']
    if "(Ответ:" in text:
        parts = text.split("(Ответ:")
        q = parts[0].strip()
        ans = parts[1].split(")")[0].strip()
        pool = SYNC_TERMS if any(t.lower() in ans.lower() for t in SYNC_TERMS) else GENERAL_TERMS
        wrong = random.sample([t for t in pool if t.lower() != ans.lower()], 2)
        opts = wrong + [ans]
        random.shuffle(opts)
        riddle = {"correct": ans, "options": opts}
        text = q + "\n\n🧩 **ДЕШИФРОВКА ТЕРМИНА:**"

    # Урон и Сигнал
    dmg = event['val'] if event['type'] == 'trap' else random.randint(2, 5)
    new_sig = max(0, s['signal'] - dmg)
    if new_sig <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        conn.commit(); conn.close(); return False, "💀 **СИГНАЛ ПОТЕРЯН.**", None

    db.update_user(uid, max_depth=max(u['max_depth'], s['depth']+1)) if (u := db.get_user(uid)) else None
    cur.execute("UPDATE raid_sessions SET depth=depth+1, signal=%s, buffer_xp=buffer_xp+%s WHERE uid=%s", 
                (new_sig, (event['val'] if event['type'] == 'loot' else 0), uid))
    conn.commit(); conn.close()
    
    msg = f"⚓️ ГЛУБИНА: {s['depth']+1}м\n\n{text}\n\n🎒 Буфер: {s['buffer_xp']} XP | 📡 Сигнал: {new_sig}%"
    return True, msg, riddle

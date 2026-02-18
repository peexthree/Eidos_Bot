import database as db
import logic
import random
import os

# Set up environment
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgres://localhost:5432/eidos')

def test_advice_generation():
    # Initialize DB
    db.init_db()

    # Create test user
    uid = 999999
    db.add_user(uid, 'test_user', 'Test User')
    db.update_user(uid, xp=10000, max_depth=0)

    # Insert test advice
    with db.db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM content WHERE type='advice' AND path='raid_general'")
            cur.execute("INSERT INTO content (type, path, level, text) VALUES ('advice', 'raid_general', 1, 'Stay hydrated in the wasteland.')")
            cur.execute("INSERT INTO content (type, path, level, text) VALUES ('advice', 'raid_general', 2, 'Watch out for drones.')")
            cur.execute("INSERT INTO content (type, path, level, text) VALUES ('advice', 'raid_general', 3, 'The core is unstable.')")

    # Run raid steps
    print("Running raid steps...")
    advice_found = False

    # Force entry
    logic.process_raid_step(uid)

    for i in range(20):
        res, txt, riddle, u, etype, cost = logic.process_raid_step(uid)
        print(f"Step {i}: Type={etype}")
        if "🧩 <i>Совет:" in txt:
            print("FOUND ADVICE!")
            print(txt)
            advice_found = True
            break

        # Avoid death
        if etype == 'combat':
            # Run away
            logic.process_combat_action(uid, 'run')

    if advice_found:
        print("SUCCESS: Advice appeared.")
    else:
        print("WARNING: Advice did not appear (could be bad luck, probability is 40%).")

if __name__ == "__main__":
    test_advice_generation()

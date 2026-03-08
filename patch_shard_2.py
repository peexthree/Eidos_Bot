filepath = 'modules/services/ai_worker.py'
with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'current_level = max(1, total_spent // 500)' in line or "item_id = 'eidos_shard'" in line or 'new_custom_data = json.dumps({' in line:
        pass
    if 'DELETE FROM user_equipment WHERE uid = %s AND item_id' in line:
        pass

# I will simply find the start of the try block at line ~295 and skip lines till the print about sending text

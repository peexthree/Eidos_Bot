with open("keyboards.py", "r") as f:
    content = f.read()

pattern = "is_visual_dist = (u.get('anomaly_buff_type') == 'visual_distortion' and u.get('anomaly_buff_expiry', 0) > time.time())"
replacement = "is_visual_dist = (u.get('anomaly_buff_type') == 'visual_distortion' and float(u.get('anomaly_buff_expiry') or 0) > time.time())"

content = content.replace(pattern, replacement)

with open("keyboards.py", "w") as f:
    f.write(content)

print("Patched keyboards.py")

import re

with open("modules/services/user.py", "r") as f:
    content = f.read()

# 1. Fix check_daily_streak
content = re.sub(
    r"import datetime\n\s*now_hour = datetime\.datetime\.now\(\)\.hour",
    "import datetime\n    now_hour = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).hour",
    content
)

# 2. Fix get_user_stats
content = re.sub(
    r"top_user_data = db\.get_leaderboard\(limit=1, sort_by='xp'\)",
    "import cache_db\n        top_user_data = cache_db.get_cached_state('top_1_user_imposter', lambda: db.get_leaderboard(limit=1, sort_by='xp'), ttl=300.0)",
    content
)

with open("modules/services/user.py", "w") as f:
    f.write(content)

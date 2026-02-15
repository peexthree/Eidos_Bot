import os

# --- ТЕХНИЧЕСКИЕ ДАННЫЕ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
DATABASE_URL = os.environ.get('DATABASE_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800      # 30 мин
COOLDOWN_ACCEL = 900      # 15 мин
COOLDOWN_SIGNAL = 300     # 5 мин
XP_GAIN = 25              
XP_SIGNAL = 15            
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
RAID_COST = 100           

PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПРОГРЕССИЯ ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# --- ТЕРМИНЫ ДЛЯ ЗАГАДОК ---
SYNC_TERMS = ["Щенок", "Выбор без выбора", "Рефрейминг", "Адвокат Дьявола", "LTV", "Якорь", "Дефицит", "Win-Win"]
GENERAL_TERMS = ["Тишина", "Тень", "Эхо", "Время", "Дыхание", "Шаги"]

# --- ДОСТИЖЕНИЯ (Lambda-условия из твоего фундамента) ---
ACHIEVEMENTS_LIST = {
    "first_steps": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: u['xp'] >= 25, "xp": 50},
    "streak_7": {"name": "🔥 СТОИК (Неделя)", "cond": lambda u: u['streak'] >= 7, "xp": 150},
    "rich_1000": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200},
    "diver_50": {"name": "🕳 СТАЛКЕР (Глубина 50)", "cond": lambda u: u.get('max_depth', 0) >= 50, "xp": 300}
}

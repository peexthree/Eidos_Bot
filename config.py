import os

# --- ТЕХНИЧЕСКИЕ ДАННЫЕ ---
TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

# --- ЭКОНОМИКА ---
RAID_COST = 100
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# --- ТЕРМИНЫ ДЛЯ ЗАГАДОК ---
SYNC_TERMS = [
    "Щенок", "Выбор без выбора", "Рефрейминг", "Адвокат Дьявола", 
    "Радость неудачи", "Цена ошибки", "Круг влияния", "Цифровой клон", 
    "Твердое и Пустое", "Якорь", "Зеркальные нейроны", "LTV", 
    "Эго-смерть", "Масштабирование", "Дефицит", "Win-Win"
]
GENERAL_TERMS = ["Тишина", "Тень", "Эхо", "Время", "Дыхание", "Шаги"]

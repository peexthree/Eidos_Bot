# -*- coding: utf-8 -*-
"""
Скрипт для сопоставления файлов из telegram_dump/photos/ на основе mapping.json.
Автоматически конвертирует и копирует их в app/src/main/res/drawable/<item_id>.png.
"""

import os
import re
import sys
import json

# Попробуем импортировать Pillow для честной конвертации в PNG.
# Если Pillow нет, мы упадем с ошибкой, но так как этот скрипт запускается локально Игорем,
# ему просто нужно будет установить Pillow (pip install Pillow), что является стандартным решением.
try:
    from PIL import Image
except ImportError:
    print("❌ Ошибка: Для работы скрипта требуется библиотека Pillow (PIL).")
    print("Пожалуйста, установите её: pip install Pillow")
    sys.exit(1)


def extract_number_from_filename(filename):
    """
    Извлекает первое число (индекс/номер) из имени файла.
    Например: 'file_12.jpg' -> 12, 'photo_12@20-02-2026_00-31-29.jpg' -> 12.
    """
    basename = os.path.basename(filename)
    match = re.search(r'\d+', basename)
    return int(match.group()) if match else None


def process_dump():
    mapping_path = "mapping.json"
    dump_dir = os.path.join("telegram_dump", "photos")
    target_dir = os.path.join("app", "src", "main", "res", "drawable")

    if not os.path.exists(mapping_path):
        print(f"❌ Файл {mapping_path} не найден в корне проекта.")
        print("Пожалуйста, поместите полученный из бота mapping.json в корень проекта.")
        return

    if not os.path.exists(dump_dir):
        print(f"❌ Папка дампа {dump_dir} не найдена.")
        print("Создаю пустую папку telegram_dump/photos для вас.")
        os.makedirs(dump_dir, exist_ok=True)
        return

    os.makedirs(target_dir, exist_ok=True)

    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # Сканируем локальные файлы в дампе
    dump_files = os.listdir(dump_dir)
    dump_map = {}
    for f in dump_files:
        f_path = os.path.join(dump_dir, f)
        if os.path.isfile(f_path):
            num = extract_number_from_filename(f)
            if num is not None:
                dump_map[num] = f_path

    print(f"/// Найдено локальных файлов в дампе: {len(dump_files)}")
    print(f"/// Найдено записей сопоставления в mapping.json: {len(mapping)}")

    success_count = 0
    not_found_count = 0
    error_count = 0

    for item_id, tg_file_path in mapping.items():
        if not tg_file_path:
            print(f"⚠️ Пропущен {item_id}: отсутствует file_path в mapping.json")
            continue

        # Получаем номер из пути, полученного от Telegram API (например, 'photos/file_12.jpg')
        tg_num = extract_number_from_filename(tg_file_path)
        if tg_num is None:
            print(f"⚠️ Не удалось извлечь номер из пути Telegram: {tg_file_path} для {item_id}")
            continue

        local_src_path = dump_map.get(tg_num)
        if not local_src_path:
            print(f"❌ Файл с номером {tg_num} не найден в {dump_dir} для {item_id} (ожидался для {tg_file_path})")
            not_found_count += 1
            continue

        # Целевой файл
        clean_item_id = str(item_id).lower().strip()
        target_filename = f"{clean_item_id}.png"
        target_path = os.path.join(target_dir, target_filename)

        try:
            # Честная конвертация через Pillow
            with Image.open(local_src_path) as img:
                img.save(target_path, "PNG")
            print(f"✅ Успешно конвертирован и скопирован: {os.path.basename(local_src_path)} -> {target_filename}")
            success_count += 1
        except Exception as e:
            print(f"❌ Ошибка конвертации {local_src_path} для {item_id}: {e}")
            error_count += 1

    print("\n--- ИТОГИ ОБРАБОТКИ ДАМПА ---")
    print(f"Успешно обработано: {success_count}")
    print(f"Не найдено локально в дампе: {not_found_count}")
    print(f"Ошибок конвертации: {error_count}")
    print(f"Результаты сохранены в {target_dir}")


if __name__ == "__main__":
    process_dump()

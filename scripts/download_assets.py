# -*- coding: utf-8 -*-
"""
Скрипт для автоматического скачивания изображений предметов из Telegram и привязки их.
Сохраняет картинки локально в директорию ресурсов Android-приложения 'app/src/main/res/drawable/'.
При отсутствии токена или сети генерирует валидные заглушки в формате PNG.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Добавляем корневую папку в PYTHONPATH, чтобы импортировать config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_minimal_png():
    """Возвращает байтовую последовательность минимального валидного PNG-файла 1x1."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x01'
        b'\x00\x00\xff\xff\x03\x00\x00\x06\x00\x05\x57\xbf\xab\xcc\x00\x00\x00'
        b'\x00IEND\xaeB`\x82'
    )


def download_or_generate_assets():
    target_dir = os.path.join("app", "src", "main", "res", "drawable")
    os.makedirs(target_dir, exist_ok=True)

    token = getattr(config, "TOKEN", None)
    item_images = getattr(config, "ITEM_IMAGES", {})

    print(f"/// Найдено предметов для обработки: {len(item_images)}")
    success_count = 0
    fallback_count = 0

    for item_id, file_id in item_images.items():
        # Требование: имя файла строго по item_id в нижнем регистре
        clean_item_id = str(item_id).lower().strip()
        filename = f"{clean_item_id}.png"
        file_path = os.path.join(target_dir, filename)

        downloaded = False

        if token and token != "None" and file_id:
            try:
                # 1. Запрос getFile к Telegram API
                get_file_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
                req = urllib.request.Request(get_file_url, method="GET")
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        file_info = json.loads(response.read().decode("utf-8"))
                        if file_info.get("ok"):
                            tg_file_path = file_info["result"]["file_path"]
                            # 2. Скачивание самого файла
                            download_url = f"https://api.telegram.org/file/bot{token}/{tg_file_path}"
                            with urllib.request.urlopen(download_url, timeout=10) as file_resp:
                                if file_resp.status == 200:
                                    with open(file_path, "wb") as f:
                                        f.write(file_resp.read())
                                    print(f"✅ Успешно скачан {filename} из Telegram.")
                                    downloaded = True
                                    success_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при скачивании {clean_item_id} ({file_id}): {e}")

        if not downloaded:
            # Генерация локальной заглушки, если нет токена/сети или произошла ошибка
            try:
                with open(file_path, "wb") as f:
                    f.write(get_minimal_png())
                print(f"ℹ️ Сгенерирована PNG-заглушка для {filename}.")
                fallback_count += 1
            except Exception as e:
                print(f"❌ Не удалось записать файл {filename}: {e}")

    print("\n--- ИТОГИ РАБОТЫ СКРИПТА ---")
    print(f"Всего обработано: {len(item_images)}")
    print(f"Скачано напрямую: {success_count}")
    print(f"Сгенерировано заглушек: {fallback_count}")
    print(f"Ресурсы сохранены в {target_dir}")


if __name__ == "__main__":
    download_or_generate_assets()

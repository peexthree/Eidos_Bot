# -*- coding: utf-8 -*-
import unittest
import os
import json
import shutil
import tempfile
from scripts.process_dump import extract_number_from_filename

class TestProcessDump(unittest.TestCase):
    def test_extract_number_from_filename(self):
        self.assertEqual(extract_number_from_filename("file_12.jpg"), 12)
        self.assertEqual(extract_number_from_filename("photos/file_99.jpg"), 99)
        self.assertEqual(extract_number_from_filename("photo_15@20-02-2026_00-59-22.jpg"), 15)
        self.assertEqual(extract_number_from_filename("no_numbers_here.jpg"), None)

    def test_process_dump_logic(self):
        # Нам нужно сымитировать структуру папок и запустить логику process_dump в тестовом окружении
        from scripts.process_dump import process_dump

        # Подменяем пути и окружение временно, создаем временные папки
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Создаем структуру папок
            os.makedirs("telegram_dump/photos", exist_ok=True)
            os.makedirs("app/src/main/res/drawable", exist_ok=True)

            # Создаем тестовую картинку (минимальный валидный 1x1 GIF или PNG, чтобы Pillow мог открыть)
            minimal_gif = (
                b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9'
                b'\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
                b'\x02D\x01\x00;'
            )
            src_image_path = "telegram_dump/photos/photo_42@20-02-2026.jpg"
            with open(src_image_path, "wb") as f:
                f.write(minimal_gif)

            # Создаем mapping.json
            mapping = {
                "plasma_rifle": "photos/file_42.jpg"
            }
            with open("mapping.json", "w", encoding="utf-8") as f:
                json.dump(mapping, f)

            # Запускаем process_dump
            process_dump()

            # Проверяем, что файл в drawable создан и имеет расширение .png
            target_file = "app/src/main/res/drawable/plasma_rifle.png"
            self.assertTrue(os.path.exists(target_file))
            self.assertTrue(os.path.getsize(target_file) > 0)

        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()

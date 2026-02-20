import unittest
import sys
from unittest.mock import MagicMock

# Mock database module before importing logic
sys.modules['database'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()

from logic import parse_riddle

class TestRiddleParsing(unittest.TestCase):
    def test_strict_match(self):
        text = "Загадка простая (Ответ: 42)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "42")
        self.assertEqual(clean_text, "Загадка простая")

    def test_strict_match_protocol(self):
        text = "Протокол доступа (Протокол: Secure)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Secure")
        self.assertEqual(clean_text, "Протокол доступа")

    def test_strict_match_with_trailing_text(self):
        # Case where strict match is used but text follows
        text = "Загадка: Сколько? (Ответ: Два) Это просто."
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Два")
        self.assertEqual(clean_text, "Загадка: Сколько? Это просто.")

    def test_broken_riddle_fallback(self):
        # The case reported by the user
        text = "👣 ЗАГАДКА: Если ты пишешь одно и то же дважды — ты тратишь жизнь. Стань им. (Цифровой Клон)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Цифровой Клон")
        self.assertEqual(clean_text, "👣 ЗАГАДКА: Если ты пишешь одно и то же дважды — ты тратишь жизнь. Стань им.")

    def test_broken_riddle_fallback_with_trailing_text(self):
        # This is the critical fix case
        text = "ЗАГАДКА: Какая птица не вьет гнезда? (Кукушка) Правильно! Это кукушка"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Кукушка")
        # Ensure it truncated the trailing spoiler
        self.assertEqual(clean_text, "ЗАГАДКА: Какая птица не вьет гнезда?")

    def test_broken_riddle_fallback_multiple_parens(self):
        # Should pick the LAST parens content
        text = "ЗАГАДКА: (Подсказка) Вопрос? (Ответ)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Ответ")
        self.assertEqual(clean_text, "ЗАГАДКА: (Подсказка) Вопрос?")

    def test_broken_riddle_fallback_case_insensitive(self):
        text = "загадка: Что-то странное (Ответ)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Ответ")
        self.assertEqual(clean_text, "загадка: Что-то странное")

    def test_no_riddle_keyword_no_match(self):
        # Parens at end but NO "ЗАГАДКА" keyword -> should not match strict or fallback
        text = "Просто текст (комментарий)"
        answer, clean_text = parse_riddle(text)
        self.assertIsNone(answer)
        self.assertEqual(clean_text, text)

    def test_riddle_keyword_but_no_parens(self):
        text = "ЗАГАДКА: найди меня"
        answer, clean_text = parse_riddle(text)
        self.assertIsNone(answer)
        self.assertEqual(clean_text, text)

    def test_complex_fallback(self):
        # "ЗАГАДКА" is present, answer at the end in parens
        text = "Это сложная ЗАГАДКА (подсказка) и текст (Ответ)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Ответ")
        self.assertEqual(clean_text, "Это сложная ЗАГАДКА (подсказка) и текст")

    def test_complex_fallback_middle_parens(self):
        # Now this should work
        text = "ЗАГАДКА (скрытая) в тексте."
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "скрытая")
        self.assertEqual(clean_text, "ЗАГАДКА")

if __name__ == '__main__':
    unittest.main()

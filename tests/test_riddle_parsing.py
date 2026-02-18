import unittest
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

    def test_broken_riddle_fallback(self):
        # The case reported by the user
        text = "👣 ЗАГАДКА: Если ты пишешь одно и то же дважды — ты тратишь жизнь. Стань им. (Цифровой Клон)"
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Цифровой Клон")
        self.assertEqual(clean_text, "👣 ЗАГАДКА: Если ты пишешь одно и то же дважды — ты тратишь жизнь. Стань им.")

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
        # The regex r'\s*\(([^()]+)\)\s*$' matches the LAST parens group at the end of string
        answer, clean_text = parse_riddle(text)
        self.assertEqual(answer, "Ответ")
        self.assertEqual(clean_text, "Это сложная ЗАГАДКА (подсказка) и текст")

    def test_complex_fallback_middle_parens(self):
        # "ЗАГАДКА" present, but parens in middle, not end.
        # Logic says: fallback searches at the end of string.
        text = "ЗАГАДКА (скрытая) в тексте."
        # Here parens are not at the very end (there is a dot, but wait... regex matches at end)
        # Regex: r'\s*\(([^()]+)\)\s*$'
        # If there is a dot after parens, it won't match unless \s* eats it? No \s* eats whitespace.
        # So "text." does not end with parens.
        answer, clean_text = parse_riddle(text)
        self.assertIsNone(answer)

        # If the user input has no dot at end?
        text2 = "ЗАГАДКА (скрытая)"
        answer2, clean_text2 = parse_riddle(text2)
        self.assertEqual(answer2, "скрытая")

if __name__ == '__main__':
    unittest.main()

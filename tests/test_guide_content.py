import unittest
import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Mock database
db_mock = MagicMock()
sys.modules['database'] = db_mock

import logic
import keyboards

class TestGuideContent(unittest.TestCase):
    def test_guide_keys_match(self):
        """Verify that all keys used in keyboards.py exist in logic.GAME_GUIDE_TEXTS"""
        expected_keys = ['intro', 'raids', 'combat', 'stats', 'items', 'pvp', 'social', 'tips']

        for key in expected_keys:
            self.assertIn(key, logic.GAME_GUIDE_TEXTS, f"Key '{key}' missing from GAME_GUIDE_TEXTS")

        # Check that values are non-empty strings
        for key, text in logic.GAME_GUIDE_TEXTS.items():
            self.assertIsInstance(text, str)
            self.assertTrue(len(text) > 0)

    def test_html_tags(self):
        """Basic check for unclosed HTML tags"""
        for key, text in logic.GAME_GUIDE_TEXTS.items():
            # Check specific tags
            tags = ['b', 'i', 'code']
            for tag in tags:
                open_tag = f"<{tag}>"
                close_tag = f"</{tag}>"
                self.assertEqual(text.count(open_tag), text.count(close_tag), f"Mismatch {tag} tags in {key}")

if __name__ == '__main__':
    unittest.main()

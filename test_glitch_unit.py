import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock database and other modules before importing glitch_system
sys.modules['database'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()

import modules.services.glitch_system as glitch_system
import modules.services.utils as utils

class TestGlitchSystem(unittest.TestCase):
    def setUp(self):
        self.uid = 12345
        glitch_system.db = MagicMock()

    def test_apply_zalgo_effect(self):
        text = "Hello"
        glitched = utils.apply_zalgo_effect(text, 1)
        self.assertNotEqual(text, glitched)
        self.assertTrue(len(glitched) > len(text))
        for char in text:
            self.assertIn(char, glitched)

    @patch('random.random', return_value=0.0) # Force trigger
    @patch('random.choice')
    def test_check_micro_glitch_adhd(self, mock_choice, mock_random):
        glitch_system.db.get_user_shadow_metrics.return_value = {'fast_sync_clicks': 10}
        glitch_system.db.get_user.return_value = {'uid': self.uid, 'level': 5}

        # We need to make sure the adhd glitch is in the possible list
        # The function now picks a random one if multiple exist.
        # Since we only have one metric high, it should be the only one.

        mock_choice.side_effect = lambda l: l[0]

        glitch = glitch_system.check_micro_glitch(self.uid, 5)
        self.assertIsNotNone(glitch)
        self.assertEqual(glitch['type'], 'adhd_clicks')
        self.assertIn('БУФЕР ПЕРЕПОЛНЕН', glitch['message'])
        self.assertEqual(glitch['xp_modifier'], 2.0)
        self.assertEqual(glitch['effect'], 'visual_distortion')

    @patch('random.random', return_value=0.0)
    @patch('random.choice')
    def test_check_micro_glitch_insomnia(self, mock_choice, mock_random):
        glitch_system.db.get_user_shadow_metrics.return_value = {'night_sessions_count': 5}
        glitch_system.db.get_user.return_value = {'uid': self.uid, 'level': 5}

        # Mock time to night
        with patch('time.localtime') as mock_time:
            mock_time.return_value.tm_hour = 2
            mock_choice.side_effect = lambda l: l[0]

            glitch = glitch_system.check_micro_glitch(self.uid, 5)
            self.assertIsNotNone(glitch)
            self.assertEqual(glitch['type'], 'insomnia')
            self.assertIn('СИСТЕМА СПИТ', glitch['message'])

if __name__ == '__main__':
    unittest.main()

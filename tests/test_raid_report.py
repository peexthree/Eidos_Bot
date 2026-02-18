import unittest
import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()
db_mock = MagicMock()
sys.modules['database'] = db_mock

import logic

class TestRaidReport(unittest.TestCase):
    def test_generate_raid_report_success(self):
        s = {
            'start_time': 1000,
            'kills': 5,
            'riddles_solved': 2,
            'buffer_xp': 500,
            'buffer_coins': 200,
            'buffer_items': 'battery,compass',
            'depth': 10
        }

        report = logic.generate_raid_report(1, s, success=True)

        self.assertIn("✅ <b>ЭВАКУАЦИЯ УСПЕШНА</b>", report)
        self.assertIn("ПОЛУЧЕНО:", report)
        self.assertIn("Глубина: 10", report)
        self.assertIn("Убийств: 5", report)
        self.assertIn("Загадок: 2", report)
        self.assertIn("500", report) # XP
        self.assertIn("200", report) # Coins

    def test_generate_raid_report_death(self):
        s = {
            'start_time': 1000,
            'kills': 1,
            'riddles_solved': 0,
            'buffer_xp': 50,
            'buffer_coins': 20,
            'buffer_items': '',
            'depth': 2
        }

        report = logic.generate_raid_report(1, s, success=False)

        self.assertIn("СВЯЗЬ ПРЕРВАНА", report)
        self.assertIn("УТЕРЯНО:", report)
        self.assertNotIn("Глубина:", report)
        self.assertIn("50", report)

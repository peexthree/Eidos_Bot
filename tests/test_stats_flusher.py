import sys
import os
import unittest
from unittest.mock import MagicMock, patch

class TestStatsFlusher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mock dependencies to avoid errors during import of bot
        cls.mock_modules = {
            'telebot': MagicMock(),
            'telebot.types': MagicMock(),
            'telebot.apihelper': MagicMock(),
            'redis': MagicMock(),
            'psycopg2': MagicMock(),
            'psycopg2.pool': MagicMock(),
            'psycopg2.extras': MagicMock(),
            'apscheduler': MagicMock(),
            'apscheduler.schedulers': MagicMock(),
            'apscheduler.schedulers.background': MagicMock(),
            'sentry_sdk': MagicMock(),
            'sentry_sdk.integrations.flask': MagicMock(),
            'flask': MagicMock(),
            'requests': MagicMock(),
        }

        # Apply mocks to sys.modules
        cls.patchers = []
        for mod_name, mock_mod in cls.mock_modules.items():
            patcher = patch.dict(sys.modules, {mod_name: mock_mod})
            patcher.start()
            cls.patchers.append(patcher)

        # Mock the scheduler decorator BEFORE importing bot
        mock_scheduler = MagicMock()
        cls.mock_modules['apscheduler.schedulers.background'].BackgroundScheduler.return_value = mock_scheduler

        def mock_scheduled_job(*args, **kwargs):
            def decorator(f):
                return f
            return decorator
        mock_scheduler.scheduled_job = mock_scheduled_job

        # Ensure we can import from root
        if os.getcwd() not in sys.path:
            sys.path.append(os.getcwd())

        # Import bot after mocks are set up
        import bot
        cls.bot = bot

    @classmethod
    def tearDownClass(cls):
        # Stop all patchers
        for patcher in reversed(cls.patchers):
            patcher.stop()

    def test_stats_flusher_calls_flush_stats(self):
        """Verify that stats_flusher calls flush_stats once."""
        with patch('bot.flush_stats') as mock_flush:
            self.bot.stats_flusher()
            mock_flush.assert_called_once()

    def test_stats_flusher_handles_exception(self):
        """Verify that stats_flusher handles exceptions from flush_stats using try...except."""
        with patch('bot.flush_stats') as mock_flush:
            mock_flush.side_effect = Exception("Test error")
            # Should not raise exception
            self.bot.stats_flusher()
            mock_flush.assert_called_once()

if __name__ == "__main__":
    unittest.main()

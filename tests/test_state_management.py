import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables
os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost:5432/db'

# Mock psycopg2 before importing database
mock_psycopg2 = MagicMock()
sys.modules['psycopg2'] = mock_psycopg2
mock_extras = MagicMock()
sys.modules['psycopg2.extras'] = mock_extras

# Import database AFTER mocking psycopg2
import database as db

class TestStateManagement(unittest.TestCase):
    def setUp(self):
        # Reset mocks if necessary
        pass

    @patch('database.db_session')
    def test_set_state(self, mock_db_session):
        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        uid = 123
        state = 'TEST_STATE'
        data = 'test_data'

        # Call the function
        db.set_state(uid, state, data)

        # Verify execute was called with correct SQL and params
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        self.assertIn("INSERT INTO bot_states", args[0])
        self.assertIn("ON CONFLICT (uid) DO UPDATE", args[0])
        self.assertEqual(args[1], (uid, state, data))

    @patch('database.db_cursor')
    def test_get_state_exists(self, mock_db_cursor):
        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('TEST_STATE', 'test_data')

        uid = 123
        result = db.get_state(uid)

        # Verify result
        self.assertEqual(result, 'TEST_STATE')
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        self.assertIn("SELECT state, data FROM bot_states WHERE uid = %s", args[0])
        self.assertEqual(args[1], (uid,))

    @patch('database.db_cursor')
    def test_get_state_not_exists(self, mock_db_cursor):
        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        uid = 123
        result = db.get_state(uid)

        # Verify result is None
        self.assertIsNone(result)

    @patch('database.db_cursor')
    def test_get_state_no_cursor(self, mock_db_cursor):
        # Simulate db_cursor returning None (no connection)
        mock_db_cursor.return_value.__enter__.return_value = None

        result = db.get_state(123)
        self.assertIsNone(result)

    @patch('database.db_cursor')
    def test_get_full_state_exists(self, mock_db_cursor):
        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        expected_res = ('TEST_STATE', 'test_data')
        mock_cursor.fetchone.return_value = expected_res

        uid = 123
        result = db.get_full_state(uid)

        # Verify result
        self.assertEqual(result, expected_res)
        mock_cursor.execute.assert_called_once_with("SELECT state, data FROM bot_states WHERE uid = %s", (uid,))

    @patch('database.db_cursor')
    def test_get_full_state_not_exists(self, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = db.get_full_state(123)
        self.assertIsNone(result)

    @patch('database.db_session')
    def test_delete_state(self, mock_db_session):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        uid = 123
        db.delete_state(uid)

        mock_cursor.execute.assert_called_once_with("DELETE FROM bot_states WHERE uid = %s", (uid,))

if __name__ == '__main__':
    unittest.main()

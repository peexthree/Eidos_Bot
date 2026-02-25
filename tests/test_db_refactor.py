import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables
os.environ['DATABASE_URL'] = 'postgres://user:pass@localhost:5432/db'

# We need to mock psycopg2 before importing database
# Note: Since database.py imports psycopg2 at the top level, we must mock it in sys.modules
mock_psycopg2 = MagicMock()
sys.modules['psycopg2'] = mock_psycopg2
mock_extras = MagicMock()
sys.modules['psycopg2.extras'] = mock_extras

import database as db

class TestDBRefactor(unittest.TestCase):
    def test_get_item_count_reuses_cursor(self):
        # Create a mock cursor
        mock_cursor = MagicMock()
        # Simulate RealDictCursor result (dict)
        mock_cursor.fetchone.return_value = {'total': 10}

        # Call get_item_count with the mock cursor
        uid = 123
        item_id = 'test_item'
        result = db.get_item_count(uid, item_id, cursor=mock_cursor)

        # Verify result
        self.assertEqual(result, 10)

        # Verify execute was called on the PASSED cursor
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        self.assertIn("SELECT SUM(quantity) as total FROM inventory", args[0])
        self.assertEqual(args[1], (uid, item_id))

        # Verify db_cursor is NOT called
        with patch('database.db_cursor') as mock_db_cursor:
            db.get_item_count(uid, item_id, cursor=mock_cursor)
            mock_db_cursor.assert_not_called()

    def test_get_item_count_creates_cursor_if_none(self):
        # Mock db_cursor context manager
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,) # Tuple cursor default

        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_cursor
        mock_ctx.__exit__.return_value = None

        with patch.object(db, 'db_cursor', return_value=mock_ctx) as mock_db_cursor_func:
            result = db.get_item_count(123, 'item')
            self.assertEqual(result, 5)
            mock_db_cursor_func.assert_called_once()

    def test_get_villain_by_id_reuses_cursor(self):
        mock_cursor = MagicMock()
        expected_villain = {'name': 'Test Villain'}
        mock_cursor.fetchone.return_value = expected_villain

        result = db.get_villain_by_id(1, cursor=mock_cursor)
        self.assertEqual(result, expected_villain)
        mock_cursor.execute.assert_called_once()

        with patch('database.db_cursor') as mock_db_cursor:
            db.get_villain_by_id(1, cursor=mock_cursor)
            mock_db_cursor.assert_not_called()

    def test_get_inventory_reuses_cursor(self):
        mock_cursor = MagicMock()
        expected_inv = [{'item_id': 'k1', 'quantity': 1}]
        mock_cursor.fetchall.return_value = expected_inv

        result = db.get_inventory(123, cursor=mock_cursor)
        self.assertEqual(result, expected_inv)
        mock_cursor.execute.assert_called_once()

        with patch('database.db_cursor') as mock_db_cursor:
            db.get_inventory(123, cursor=mock_cursor)
            mock_db_cursor.assert_not_called()

if __name__ == '__main__':
    unittest.main()

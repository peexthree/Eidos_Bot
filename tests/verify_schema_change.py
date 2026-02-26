import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock psycopg2
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# Import database after mocking
import database as db

class TestSchemaUpdate(unittest.TestCase):
    def test_schema_definition(self):
        self.assertIn('current_event_type', db.TABLE_SCHEMAS['raid_sessions'])
        self.assertEqual(db.TABLE_SCHEMAS['raid_sessions']['current_event_type'], ('TEXT', 'NULL'))

    @patch('database.db_session')
    def test_ensure_table_schema_call(self, mock_session):
        # Mock the session and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock table existing
        mock_cursor.fetchone.side_effect = [
            (1,), # Table exists
            # Columns fetchall
            [('uid', 'bigint'), ('depth', 'bigint'), ('signal', 'bigint'), ('next_event_type', 'text')],
        ]

        db.ensure_table_schema('raid_sessions', db.TABLE_SCHEMAS['raid_sessions'])

        # Check if ALTER TABLE was called for current_event_type
        found = False
        for call in mock_cursor.execute.call_args_list:
            sql = call[0][0]
            if "ALTER TABLE raid_sessions ADD COLUMN current_event_type TEXT" in sql:
                found = True
                break

        self.assertTrue(found, "SQL to add current_event_type not found")

if __name__ == '__main__':
    unittest.main()

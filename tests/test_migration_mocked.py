import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock psycopg2 before import
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database

class TestMigrationMocked(unittest.TestCase):
    @patch('database.pg_pool', new_callable=MagicMock)
    def test_fix_column_types(self, mock_pool):
        # We need to simulate db_session context manager
        mock_conn = MagicMock()
        mock_cur = MagicMock()

        # When db_session() is called, it returns a context manager that yields mock_conn
        # database.db_session implementation:
        # yield conn -> conn.commit()

        # When db_cursor() is called, it yields mock_cur
        # But fix_column_types uses `with db_session() as conn: with conn.cursor() as cur:`

        # Mock pool behavior
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Mock table check
        # First call: Check if table exists -> returns (1,)
        # Second call: Get columns -> returns list of tuples

        # Note: fix_column_types executes:
        # 1. SELECT 1 FROM information_schema.tables WHERE table_name='players'
        # 2. SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'players'
        # 3. ALTER TABLE statements...

        mock_cur.fetchone.side_effect = [(1,)] # Table exists

        # Mock columns: xp as text, level as integer
        mock_cur.fetchall.return_value = [
            ('xp', 'text'),
            ('level', 'integer'),
            ('last_active', 'text'), # Date field as text
            ('notified', 'text') # Boolean field as text
        ]

        # Call the function
        # We need to ensure db_session uses the mock_pool we patched
        # Since database.pg_pool is global, patching it works if we patch specifically inside database module

        # Re-patch pg_pool inside database module to be sure
        with patch('database.pg_pool', mock_pool):
            database.fix_column_types()

        # Verify executions
        calls = mock_cur.execute.call_args_list
        # Extract SQL statements
        sql_statements = [str(c[0][0]) for c in calls]

        print("Executed SQL:")
        for sql in sql_statements:
            print(sql)

        # Assertions

        # 1. Check table existence check
        self.assertTrue(any("SELECT 1 FROM information_schema.tables" in sql for sql in sql_statements))

        # 2. Check column fetching
        self.assertTrue(any("SELECT column_name, data_type" in sql for sql in sql_statements))

        # 3. Check fixes
        # XP -> Integer
        xp_fix = [s for s in sql_statements if "ALTER COLUMN xp TYPE INTEGER" in s]
        self.assertTrue(xp_fix, "xp should be converted to integer")
        self.assertIn("USING (NULLIF(xp, '')::INTEGER)", xp_fix[0])

        # Level -> Integer (already integer, so NO fix expected)
        level_fix = [s for s in sql_statements if "ALTER COLUMN level TYPE INTEGER" in s]
        self.assertFalse(level_fix, "level is already integer, should not be fixed")

        # Last Active -> Date
        date_fix = [s for s in sql_statements if "ALTER COLUMN last_active TYPE DATE" in s]
        self.assertTrue(date_fix, "last_active should be converted to date")
        self.assertIn("USING (NULLIF(last_active, '')::DATE)", date_fix[0])

        # Notified -> Boolean
        bool_fix = [s for s in sql_statements if "ALTER COLUMN notified TYPE BOOLEAN" in s]
        self.assertTrue(bool_fix, "notified should be converted to boolean")
        self.assertIn("USING (NULLIF(notified, '')::BOOLEAN)", bool_fix[0])

if __name__ == '__main__':
    unittest.main()

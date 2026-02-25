import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# Mock psycog2 before importing database
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

import database

class TestVillainsLoading(unittest.TestCase):

    def test_load_villains_data_success(self):
        mock_data = {
            "villains": [{"name": "TestVillain"}],
            "old_names": ["OldName"]
        }
        json_content = json.dumps(mock_data)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json_content)):
                villains, old_names = database._load_villains_data()

                self.assertEqual(len(villains), 1)
                self.assertEqual(villains[0]['name'], "TestVillain")
                self.assertEqual(len(old_names), 1)
                self.assertEqual(old_names[0], "OldName")

    def test_load_villains_data_file_not_found(self):
        with patch("os.path.exists", return_value=False):
            villains, old_names = database._load_villains_data()
            self.assertEqual(villains, [])
            self.assertEqual(old_names, ())

    def test_load_villains_data_json_error(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="INVALID JSON")):
                villains, old_names = database._load_villains_data()
                self.assertEqual(villains, [])
                self.assertEqual(old_names, ())

    def test_populate_villains_calls_db(self):
        # Mock _load_villains_data to return sample data
        with patch.object(database, '_load_villains_data') as mock_load:
            mock_load.return_value = ([{"name": "V1", "level": 1, "hp": 10, "atk": 1, "def": 0, "xp": 1, "coin": 1, "desc": "D", "image": "I"}], ("Old1",))

            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            with patch('database.db_session') as mock_session:
                mock_session.return_value.__enter__.return_value = mock_conn
                mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

                database.populate_villains()

                # Check DELETE call
                calls = mock_cursor.execute.call_args_list
                delete_called = False
                insert_called = False

                for c in calls:
                    query = c[0][0]
                    if "DELETE FROM villains" in query:
                        delete_called = True
                        self.assertEqual(c[0][1], (("Old1",),))
                    if "INSERT INTO villains" in query:
                        insert_called = True
                        self.assertEqual(c[0][1]['name'], "V1")

                self.assertTrue(delete_called)
                self.assertTrue(insert_called)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import hmac
import hashlib
import time
import sys

# Mocking modules that are missing in the environment
sys.modules['flask'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['apscheduler'] = MagicMock()
sys.modules['apscheduler.schedulers'] = MagicMock()
sys.modules['apscheduler.schedulers.background'] = MagicMock()
sys.modules['sentry_sdk'] = MagicMock()
sys.modules['sentry_sdk.integrations'] = MagicMock()
sys.modules['sentry_sdk.integrations.flask'] = MagicMock()

# Mocking TOKEN in bot_instance before it's imported anywhere
bot_instance_mock = MagicMock()
bot_instance_mock.TOKEN = "12345:ABCDE"
sys.modules['modules.bot_instance'] = bot_instance_mock

# Now we can import our auth service
from modules.services.auth import verify_init_data, require_telegram_auth

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.token = "12345:ABCDE"
        if 'DEBUG_MODE' in os.environ:
            del os.environ['DEBUG_MODE']

    def create_valid_init_data(self, user_id=12345):
        params = {
            'auth_date': str(int(time.time())),
            'user': json.dumps({'id': user_id, 'first_name': 'TestUser'})
        }
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hmac.new(b"WebAppData", self.token.encode(), hashlib.sha256).digest()
        h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return f"{data_check_string.replace('\n', '&')}&hash={h}"

    def test_verify_init_data_valid(self):
        init_data = self.create_valid_init_data()
        user = verify_init_data(init_data, self.token)
        self.assertIsNotNone(user)
        self.assertEqual(user['id'], 12345)

    def test_verify_init_data_invalid_hash(self):
        init_data = self.create_valid_init_data() + "extra"
        user = verify_init_data(init_data, self.token)
        self.assertIsNone(user)

    def test_verify_init_data_expired(self):
        params = {
            'auth_date': str(int(time.time()) - 90000), # > 24h
            'user': json.dumps({'id': 12345})
        }
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hmac.new(b"WebAppData", self.token.encode(), hashlib.sha256).digest()
        h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        init_data = f"{data_check_string.replace('\n', '&')}&hash={h}"

        user = verify_init_data(init_data, self.token)
        self.assertIsNone(user)

    def test_require_auth_missing_header(self):
        flask_mock = sys.modules['flask']
        flask_mock.request.headers.get.return_value = None

        decorated = require_telegram_auth(lambda: "success")
        response = decorated()

        flask_mock.jsonify.assert_called_with({"error": "Unauthorized - Missing InitData"})
        self.assertNotEqual(response, "success")

    def test_require_auth_uid_mismatch(self):
        flask_mock = sys.modules['flask']
        valid_init_data = self.create_valid_init_data(user_id=12345)

        flask_mock.request.headers.get.return_value = valid_init_data
        flask_mock.request.args.get.return_value = "99999" # Mismatch
        flask_mock.request.is_json = False

        decorated = require_telegram_auth(lambda: "success")
        response = decorated()

        flask_mock.jsonify.assert_called_with({"error": "Forbidden - UID Mismatch"})
        self.assertNotEqual(response, "success")

    def test_require_auth_success(self):
        flask_mock = sys.modules['flask']
        valid_init_data = self.create_valid_init_data(user_id=12345)

        flask_mock.request.headers.get.return_value = valid_init_data
        flask_mock.request.args.get.return_value = "12345" # Match
        flask_mock.request.is_json = False

        decorated = require_telegram_auth(lambda: "success")
        response = decorated()

        self.assertEqual(response, "success")

    def test_debug_mode_bypass(self):
        os.environ['DEBUG_MODE'] = 'true'
        decorated = require_telegram_auth(lambda: "success")
        response = decorated()
        self.assertEqual(response, "success")

if __name__ == '__main__':
    unittest.main()

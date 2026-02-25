
import unittest
from unittest.mock import MagicMock, patch
import sys
import json

# Import the module under test
# We import it normally. If it crashes due to missing dependencies in sys.modules, we might need to mock them first.
# But since we are running in an environment where modules exist (or we can mock sys.modules just for import),
# let's try to import it.
# However, pvp imports database, which might connect to DB.
# So we still need to mock sys.modules for the initial import if we are in a vacuum.
# But assuming the environment is set up (since other tests run), we can just import.

# To be safe, we mock dependencies in sys.modules ONLY for the import, then restore?
# Or we just assume we can patch attributes.

class TestPvpBuyHandler(unittest.TestCase):
    def setUp(self):
        # 1. Setup mocks
        self.mock_bot = MagicMock()
        # Configure callback_query_handler to be a transparent decorator
        def handler_decorator(*args, **kwargs):
            def wrapper(f):
                return f
            return wrapper
        self.mock_bot.callback_query_handler.side_effect = handler_decorator
        self.mock_bot.message_handler.side_effect = handler_decorator

        self.mock_bot_instance = MagicMock()
        self.mock_bot_instance.bot = self.mock_bot

        self.mock_db = MagicMock()

        self.mock_config = MagicMock()
        self.mock_config.SOFTWARE_DB = {
            "soft_1": {"name": "Software 1", "cost": 100, "type": "atk", "power": 1, "desc": "Desc 1", "icon": "🔴"},
            "soft_2": {"name": "Software 2", "cost": 200, "type": "def", "power": 2, "desc": "Desc 2", "icon": "🔵"}
        }
        self.mock_config.ITEMS_INFO = {
            "hw_1": {"name": "Hardware 1", "desc": "HW Desc 1"},
            "hw_2": {"name": "Hardware 2", "desc": "HW Desc 2"}
        }
        self.mock_config.PRICES = {
            "hw_1": 500,
            "hw_2": 1000
        }
        self.mock_config.ITEM_IMAGES = {
            "soft_1": "http://img/soft1",
            "hw_1": "http://img/hw1"
        }
        self.mock_config.QUARANTINE_LEVEL = 5
        self.mock_config.MENU_IMAGES = {}

        self.mock_kb = MagicMock()
        self.mock_utils = MagicMock()
        self.mock_pvp_service = MagicMock()
        self.mock_telebot = MagicMock()

        # 2. Patch sys.modules
        self.patcher_sys = patch.dict(sys.modules, {
            'modules.bot_instance': self.mock_bot_instance,
            'database': self.mock_db,
            'config': self.mock_config,
            'keyboards': self.mock_kb,
            'modules.services.utils': self.mock_utils,
            'modules.services.pvp': self.mock_pvp_service,
            'telebot': self.mock_telebot,
            'telebot.types': MagicMock()
        })
        self.patcher_sys.start()

        # 3. Import/Reload pvp module
        # Since we patched sys.modules, we can import pvp safely.
        # If it was already imported, we reload it to use our mocks.
        if 'modules.handlers.pvp' in sys.modules:
            # Note: reloading uses the module object already in sys.modules if present?
            # Or it re-executes.
            # If sys.modules['modules.handlers.pvp'] is present (from previous test or real run),
            # reload will update it.
            # But wait, patch.dict might hide the original 'modules.handlers.pvp' if we didn't include it in dict?
            # patch.dict only updates keys in the dict. It preserves others unless clear=True.
            # We didn't set clear=True.
            import modules.handlers.pvp
            import importlib
            importlib.reload(modules.handlers.pvp)
        else:
            import modules.handlers.pvp

        self.pvp_module = sys.modules['modules.handlers.pvp']

        # We don't need to patch attributes manually if we reloaded the module with mocked sys.modules!
        # Because the module uses `import config`, `import database` etc.
        # Reloading makes it resolve imports again using our patched sys.modules.

        # However, we mocked pvp_shop_handler which is defined in the module itself.
        self.orig_pvp_shop_handler = self.pvp_module.pvp_shop_handler
        self.mock_pvp_shop_handler = MagicMock()
        self.pvp_module.pvp_shop_handler = self.mock_pvp_shop_handler

    def tearDown(self):
        # Restore pvp_shop_handler
        self.pvp_module.pvp_shop_handler = self.orig_pvp_shop_handler

        self.patcher_sys.stop()

        # We should reload pvp again to restore it to original state?
        # If we don't, subsequent tests might use the pvp module that is linked to our mocks (which are now stopped/invalid?)
        # Yes, we should reload it.
        # But we need to make sure we can reload it (dependencies exist).
        # Since we stopped patcher, sys.modules is restored.
        if 'modules.handlers.pvp' in sys.modules:
            import modules.handlers.pvp
            import importlib
            try:
                importlib.reload(modules.handlers.pvp)
            except Exception as e:
                # If dependencies are missing in the restored sys.modules (e.g. if run in isolation), reload might fail.
                # But typically unittest discover runs in an environment where deps are available or mocked globally.
                print(f"Warning: Failed to restore pvp module: {e}")

    def test_buy_software_confirm(self):
        # Test buying software (confirm action)
        call = MagicMock()
        call.data = "pvp_buy_confirm_soft_1"
        call.from_user.id = 123
        call.id = "call_id_1"

        self.mock_pvp_service.buy_software.return_value = (True, "Success")
        self.mock_db.get_user.return_value = {'biocoin': 1000}

        self.pvp_module.pvp_buy_handler(call)

        self.mock_pvp_service.buy_software.assert_called_with(123, "soft_1", is_hardware=False)
        self.mock_bot.answer_callback_query.assert_called_with("call_id_1", "Success", show_alert=True)
        # Verify pvp_shop_handler was called
        self.mock_pvp_shop_handler.assert_called_with(call)

    def test_buy_hardware_confirm(self):
        # Test buying hardware (confirm action)
        call = MagicMock()
        call.data = "pvp_buy_confirm_hw_hw_1"
        call.from_user.id = 123
        call.id = "call_id_2"

        self.mock_pvp_service.buy_software.return_value = (True, "Success HW")
        self.mock_db.get_user.return_value = {'biocoin': 1000}

        self.pvp_module.pvp_buy_handler(call)

        self.mock_pvp_service.buy_software.assert_called_with(123, "hw_1", is_hardware=True)
        self.mock_bot.answer_callback_query.assert_called_with("call_id_2", "Success HW", show_alert=True)

    def test_show_info_software(self):
        # Test showing info for software
        call = MagicMock()
        call.data = "pvp_buy_soft_1"
        call.from_user.id = 123

        self.pvp_module.pvp_buy_handler(call)

        # Should call menu_update with item info
        self.mock_utils.menu_update.assert_called()
        args, kwargs = self.mock_utils.menu_update.call_args
        msg = args[1]
        self.assertIn("Software 1", msg)
        self.assertIn("100 BC", msg)
        self.assertEqual(kwargs['image_url'], "http://img/soft1")
        self.mock_kb.pvp_shop_confirm.assert_called_with("soft_1", is_hardware=False)

    def test_show_info_hardware(self):
        # Test showing info for hardware
        call = MagicMock()
        call.data = "pvp_buy_hw_hw_1"
        call.from_user.id = 123

        self.pvp_module.pvp_buy_handler(call)

        # Should call menu_update with item info
        self.mock_utils.menu_update.assert_called()
        args, kwargs = self.mock_utils.menu_update.call_args
        msg = args[1]
        self.assertIn("Hardware 1", msg)
        self.assertIn("500 BC", msg)
        self.assertEqual(kwargs['image_url'], "http://img/hw1")
        self.mock_kb.pvp_shop_confirm.assert_called_with("hw_1", is_hardware=True)

if __name__ == '__main__':
    unittest.main()

import sys
from unittest.mock import MagicMock

# Mocking external dependencies that might be imported by cache_db or its dependencies
sys.modules['redis'] = MagicMock()
sys.modules['database'] = MagicMock()

import os
from datetime import date, datetime
import json

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cache_db import json_serial

def test_json_serial_datetime():
    dt = datetime(2023, 10, 27, 12, 30, 45)
    result = json_serial(dt)
    assert result == dt.isoformat()
    assert result == "2023-10-27T12:30:45"

def test_json_serial_date():
    d = date(2023, 10, 27)
    result = json_serial(d)
    assert result == d.isoformat()
    assert result == "2023-10-27"

def test_json_serial_other_types():
    # Test integer
    assert json_serial(123) == "123"
    # Test string
    assert json_serial("hello") == "hello"
    # Test custom object
    class CustomObj:
        def __str__(self):
            return "custom"
    assert json_serial(CustomObj()) == "custom"

def test_json_dumps_integration():
    data = {
        "name": "Test",
        "date": date(2023, 10, 27),
        "timestamp": datetime(2023, 10, 27, 12, 0, 0)
    }

    # This should fail without default=json_serial
    # try:
    #     json.dumps(data)
    # except TypeError:
    #     pass

    json_string = json.dumps(data, default=json_serial)
    loaded_data = json.loads(json_string)

    assert loaded_data["name"] == "Test"
    assert loaded_data["date"] == "2023-10-27"
    assert loaded_data["timestamp"] == "2023-10-27T12:00:00"

if __name__ == "__main__":
    # Manual execution if needed
    test_json_serial_datetime()
    test_json_serial_date()
    test_json_serial_other_types()
    test_json_dumps_integration()
    print("All tests passed!")

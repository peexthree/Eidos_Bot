import sys
from unittest.mock import MagicMock
sys.modules['openai'] = MagicMock()
sys.modules['sentry_sdk'] = MagicMock()
sys.modules['sentry_sdk.integrations'] = MagicMock()
sys.modules['sentry_sdk.integrations.flask'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['requests'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()

import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.services.utils import split_long_message

def test_split_long_message():
    # Test 1: Small message
    small = "Hello World"
    chunks = split_long_message(small, 100)
    assert len(chunks) == 1
    assert chunks[0] == small
    print("Test 1 Passed: Small message")

    # Test 2: Exact boundary
    exact = "A" * 100
    chunks = split_long_message(exact, 100)
    assert len(chunks) == 1
    print("Test 2 Passed: Exact boundary")

    # Test 3: Structured Data
    # Blocks of 50 chars including \n\n
    block = "A" * 48 + "\n\n"
    # Create 10 blocks = 500 chars
    text = block * 10

    # Chunk size 120. Should fit 2 blocks (100 chars) per chunk.
    chunks = split_long_message(text, 120)

    assert len(chunks) == 5
    for c in chunks:
        assert len(c) <= 120
        assert c.endswith("\n\n")
        assert c.count("\n\n") == 2

    print("Test 3 Passed: Structured Data")

    # Test 4: Verify Content Integrity
    reconstructed = "".join(chunks)
    assert reconstructed == text
    print("Test 4 Passed: Integrity Check")

if __name__ == "__main__":
    test_split_long_message()

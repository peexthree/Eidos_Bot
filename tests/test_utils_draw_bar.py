import sys
import os
import unittest

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.services.utils import draw_bar

class TestDrawBar(unittest.TestCase):
    def test_zero_filled(self):
        # 0/10 -> Empty (10 chars)
        result = draw_bar(0, 10, length=10)
        self.assertEqual(result, "░" * 10)

    def test_half_filled(self):
        # 5/10 -> 50% -> 5 filled
        result = draw_bar(5, 10, length=10)
        self.assertEqual(result, "█" * 5 + "░" * 5)

    def test_full_filled(self):
        # 10/10 -> 100% -> 10 filled
        result = draw_bar(10, 10, length=10)
        self.assertEqual(result, "█" * 10)

    def test_overflow(self):
        # 15/10 -> 150% -> max 100% -> 10 filled
        result = draw_bar(15, 10, length=10)
        self.assertEqual(result, "█" * 10)

    def test_underflow(self):
        # -5/10 -> min 0% -> 0 filled
        result = draw_bar(-5, 10, length=10)
        self.assertEqual(result, "░" * 10)

    def test_zero_total(self):
        # 5/0 -> Invalid total -> Should return empty bar (as per logic: if total <= 0: return "░" * length)
        result = draw_bar(5, 0, length=10)
        self.assertEqual(result, "░" * 10)

    def test_negative_total(self):
        # 5/-10 -> Invalid total -> Empty bar
        result = draw_bar(5, -10, length=10)
        self.assertEqual(result, "░" * 10)

    def test_custom_length(self):
        # 5/10 with length 20 -> 50% of 20 = 10 filled
        result = draw_bar(5, 10, length=20)
        self.assertEqual(result, "█" * 10 + "░" * 10)

        # 5/10 with length 4 -> 50% of 4 = 2 filled
        result = draw_bar(5, 10, length=4)
        self.assertEqual(result, "█" * 2 + "░" * 2)

    def test_float_values(self):
        # 2.5/10 -> 25% of 10 = 2.5 -> int(2.5) = 2 filled
        result = draw_bar(2.5, 10, length=10)
        self.assertEqual(result, "█" * 2 + "░" * 8)

        # 7.9/10 -> 79% of 10 = 7.9 -> int(7.9) = 7 filled
        result = draw_bar(7.9, 10, length=10)
        self.assertEqual(result, "█" * 7 + "░" * 3)

if __name__ == '__main__':
    unittest.main()

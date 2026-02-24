import unittest

from navscan.features.liquidity import compute_dollar_volume
from navscan.features.premium_discount import compute_premium_discount_pct


class TestFormulas(unittest.TestCase):
    def test_premium_discount_pct(self):
        self.assertAlmostEqual(compute_premium_discount_pct(110.0, 100.0), 10.0)
        self.assertAlmostEqual(compute_premium_discount_pct(90.0, 100.0), -10.0)

    def test_premium_discount_invalid_nav(self):
        self.assertIsNone(compute_premium_discount_pct(100.0, 0.0))
        self.assertIsNone(compute_premium_discount_pct(100.0, -5.0))
        self.assertIsNone(compute_premium_discount_pct(None, 100.0))
        self.assertIsNone(compute_premium_discount_pct(100.0, None))

    def test_dollar_volume(self):
        self.assertAlmostEqual(compute_dollar_volume(10.5, 1000.0), 10500.0)

    def test_dollar_volume_missing(self):
        self.assertIsNone(compute_dollar_volume(None, 1000.0))
        self.assertIsNone(compute_dollar_volume(10.5, None))


if __name__ == "__main__":
    unittest.main()


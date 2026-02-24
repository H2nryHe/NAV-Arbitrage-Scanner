import unittest

from navscan.signals.mean_reversion import estimate_half_life_days


class TestHalfLife(unittest.TestCase):
    def test_insufficient_history(self):
        out = estimate_half_life_days([1.0, 0.9, 0.8], min_points=10, max_half_life_days=252.0)
        self.assertIsNone(out["half_life_days"])
        self.assertEqual(out["reason"], "insufficient_history")

    def test_zero_variance(self):
        out = estimate_half_life_days([1.0] * 25, min_points=20, max_half_life_days=252.0)
        self.assertIsNone(out["half_life_days"])
        self.assertEqual(out["reason"], "zero_variance")

    def test_non_mean_reverting_beta(self):
        # Monotonic acceleration trend should not be mean-reverting.
        series = [float(i * i) for i in range(1, 40)]
        out = estimate_half_life_days(series, min_points=20, max_half_life_days=252.0)
        self.assertIsNone(out["half_life_days"])
        self.assertEqual(out["reason"], "non_mean_reverting_beta")

    def test_valid_half_life(self):
        series = [10.0]
        for _ in range(40):
            series.append(series[-1] * 0.92)  # mean-reverting decay
        out = estimate_half_life_days(series, min_points=20, max_half_life_days=252.0)
        self.assertIsNotNone(out["half_life_days"])
        self.assertEqual(out["reason"], "ok")
        self.assertGreater(out["half_life_days"], 0.0)


if __name__ == "__main__":
    unittest.main()


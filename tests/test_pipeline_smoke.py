import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def write_ndjson(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class TestPipelineSmoke(unittest.TestCase):
    def test_stage3_build_candidates_from_synthetic_silver(self):
        repo_root = Path(__file__).resolve().parents[1]

        date_str = "2026-02-20"
        symbol = "TESTCEF"

        # Build minimal silver history (half-life will be "insufficient_history", which is fine)
        all_rows = []
        for d, pd in [
            ("2026-02-16", 1.0),
            ("2026-02-17", 2.0),
            ("2026-02-18", 3.0),
            ("2026-02-19", 4.0),
            (date_str, 10.0),  # extreme by abs_pd_threshold=5%
        ]:
            all_rows.append(
                {
                    "date": d,
                    "symbol": symbol,
                    "premium_discount_pct": pd,
                    "dollar_volume": 5_000_000.0,  # pass liquidity (>= 2,000,000)
                    "distribution_event_flag": False,  # pass event filter
                    "nav_staleness_flag": False,
                    "data_quality_flags": [],
                    # optional: provide zscore so detect_extreme can use it; not required
                    "pd_zscore_20d": 3.0 if d == date_str else None,
                }
            )

        day_rows = [r for r in all_rows if r["date"] == date_str]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            silver_root = tmpdir / "silver"
            output_root = tmpdir / "signals"

            write_ndjson(silver_root / "all_dates.ndjson", all_rows)
            write_ndjson(silver_root / f"date={date_str}" / "snapshot.ndjson", day_rows)

            cmd = [
                "python3",
                "scripts/stage3_build_candidates.py",
                "--silver-root",
                str(silver_root),
                "--output-root",
                str(output_root),
                "--config",
                "configs/stage3_signals.json",
                "--date",
                date_str,
            ]
            proc = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, msg=f"stderr={proc.stderr}\nstdout={proc.stdout}")

            candidates_path = output_root / f"date={date_str}" / "candidates_ranked.ndjson"
            self.assertTrue(candidates_path.exists())

            rows = [
                json.loads(line)
                for line in candidates_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertGreater(len(rows), 0)

            first = rows[0]
            self.assertIn("rationale", first)
            self.assertIn("risk_flags", first)


if __name__ == "__main__":
    unittest.main()

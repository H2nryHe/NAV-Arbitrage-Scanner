import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestPipelineSmoke(unittest.TestCase):
    def test_stage3_build_candidates_from_existing_silver(self):
        repo_root = Path(__file__).resolve().parents[1]
        silver_root = repo_root / "data" / "silver"
        self.assertTrue((silver_root / "date=2026-02-20" / "snapshot.ndjson").exists())
        self.assertTrue((silver_root / "all_dates.ndjson").exists())

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "signals"
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
                "2026-02-20",
            ]
            proc = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, msg=f"stderr={proc.stderr}\nstdout={proc.stdout}")

            candidates_path = output_root / "date=2026-02-20" / "candidates_ranked.ndjson"
            self.assertTrue(candidates_path.exists())
            rows = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertGreater(len(rows), 0)
            first = rows[0]
            self.assertIn("rationale", first)
            self.assertIn("risk_flags", first)


if __name__ == "__main__":
    unittest.main()

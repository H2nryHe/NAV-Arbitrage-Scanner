from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from navscan.reporting.csv_export import export_candidates_csv
from navscan.reporting.markdown_report import build_markdown_report, write_markdown_report


def _parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.lower() in ("true", "false"):
            data[k] = v.lower() == "true"
        else:
            try:
                data[k] = int(v) if "." not in v else float(v)
            except ValueError:
                data[k] = v
    return data


def _valid_date(date_str: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))


def _run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_ndjson(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def cmd_run(args: argparse.Namespace) -> int:
    if not _valid_date(args.date):
        print("error: --date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"error: config not found: {config_path}", file=sys.stderr)
        return 2
    universe_path = Path(args.universe)
    if not universe_path.exists():
        print(f"error: universe not found: {universe_path}", file=sys.stderr)
        return 2

    cfg = _parse_simple_yaml(config_path)
    raw_root = str(cfg.get("raw_root", "data/raw"))
    silver_root = str(cfg.get("silver_root", "data/silver"))
    signals_root = str(cfg.get("signals_root", "data/gold/signals"))
    reports_root = Path(args.output_dir or cfg.get("reports_root", "reports"))
    stage3_cfg = str(cfg.get("stage3_signals_config", "configs/stage3_signals.json"))
    top_n = int(cfg.get("top_n", 10))

    common_stage_args = []
    if args.verbose:
        common_stage_args.append("--verbose")

    # Stage 1
    code, out, err = _run_cmd(
        [
            sys.executable,
            "scripts/stage1_ingest.py",
            "--dates",
            args.date,
            "--universe",
            str(universe_path),
            "--raw-root",
            raw_root,
            *common_stage_args,
        ]
    )
    if code != 0:
        print(err or out, file=sys.stderr)
        return 2

    # Stage 2
    code, out, err = _run_cmd(
        [
            sys.executable,
            "scripts/stage2_build_silver.py",
            "--raw-root",
            raw_root,
            "--silver-root",
            silver_root,
            "--universe",
            str(universe_path),
            "--dates",
            args.date,
            "--zscore-window",
            "20",
            *common_stage_args,
        ]
    )
    if code != 0:
        print(err or out, file=sys.stderr)
        return 2

    # Stage 3
    code, out, err = _run_cmd(
        [
            sys.executable,
            "scripts/stage3_build_candidates.py",
            "--silver-root",
            silver_root,
            "--output-root",
            signals_root,
            "--config",
            stage3_cfg,
            "--date",
            args.date,
            *common_stage_args,
        ]
    )
    if code != 0:
        print(err or out, file=sys.stderr)
        return 2

    # Stage 4 reporting
    run_raw = _read_json(Path(raw_root) / "run_summaries" / f"date={args.date}.json")
    run_silver = _read_json(Path(silver_root) / "run_summary.json")
    run_signal = _read_json(Path(signals_root) / f"date={args.date}" / "summary.json")
    candidates = _read_ndjson(Path(signals_root) / f"date={args.date}" / "candidates_ranked.ndjson")
    top_rows = candidates[:top_n]

    coverage = {
        "raw_price_ok": run_raw["datasets"]["price_volume"]["ok"],
        "raw_nav_ok": run_raw["datasets"]["nav"]["ok"],
        "raw_events_ok": run_raw["datasets"]["events"]["ok"],
        "raw_metadata_ok": run_raw["datasets"]["metadata"]["ok"],
        "silver_records": run_silver["dates"].get(args.date, {}).get("records", 0),
        "silver_missing_nav": run_silver["dates"].get(args.date, {}).get("missing_nav", 0),
        "silver_invalid_nav": run_silver["dates"].get(args.date, {}).get("invalid_nav", 0),
    }

    out_dir = reports_root / f"date={args.date}"
    csv_path = out_dir / "top_opportunities.csv"
    md_path = out_dir / "daily_report.md"
    export_candidates_csv(csv_path, top_rows)
    md = build_markdown_report(args.date, top_rows, coverage, run_signal)
    write_markdown_report(md_path, md)

    print(f"generated_csv={csv_path}")
    print(f"generated_markdown={md_path}")
    if not candidates:
        print("warning: no candidates passed filters", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="navscan")
    sub = p.add_subparsers(dest="command")
    run = sub.add_parser("run", help="Run Stage 1-4 MVP flow for a date")
    run.add_argument("--date", required=True)
    run.add_argument("--config", default="configs/default.yaml")
    run.add_argument("--universe", default="configs/universe_example.yaml")
    run.add_argument("--output-dir", default="")
    run.add_argument("--verbose", action="store_true")
    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


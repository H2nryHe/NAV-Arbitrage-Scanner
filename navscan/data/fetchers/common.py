from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_universe_symbols(path: Path) -> List[str]:
    symbols: List[str] = []
    inside_symbols = False
    pattern = re.compile(r"^\s*-\s*([A-Za-z0-9.\-]+)(?:\s*#.*)?\s*$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s*symbols:\s*$", raw_line):
            inside_symbols = True
            continue
        if inside_symbols:
            m = pattern.match(raw_line.rstrip())
            if m:
                symbols.append(m.group(1).upper())
            elif raw_line.strip() and not raw_line.startswith(" "):
                break
    if not symbols:
        raise ValueError(f"No symbols found under 'symbols:' in {path}")
    return symbols


def http_get_json_with_retry(
    url: str,
    *,
    attempts: int = 3,
    timeout_seconds: int = 20,
    sleep_seconds: float = 1.25,
) -> Any:
    last_error: Optional[Exception] = None
    for i in range(1, attempts + 1):
        try:
            proc = subprocess.run(
                ["curl", "-sS", "-L", "--max-time", str(timeout_seconds), url],
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(proc.stdout)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if i < attempts:
                time.sleep(sleep_seconds * i)
    raise RuntimeError(f"Failed GET after {attempts} attempts: {url}; err={last_error}")


def write_ndjson(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

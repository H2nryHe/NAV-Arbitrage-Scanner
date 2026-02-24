from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _row_hash(row: Dict[str, Any]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_ts TEXT NOT NULL,
            mode TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price_close REAL,
            nav REAL,
            premium_discount_pct REAL,
            dollar_volume REAL,
            data_quality_flags_json TEXT,
            source_path TEXT,
            row_hash TEXT NOT NULL,
            first_seen_ts TEXT NOT NULL,
            last_seen_ts TEXT NOT NULL,
            PRIMARY KEY (date, symbol)
        );

        CREATE TABLE IF NOT EXISTS candidates (
            scan_date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rank INTEGER,
            score REAL,
            premium_discount_pct_at_scan REAL,
            dollar_volume_at_scan REAL,
            rationale TEXT,
            risk_flags_json TEXT,
            source_path TEXT,
            row_hash TEXT NOT NULL,
            first_seen_ts TEXT NOT NULL,
            last_seen_ts TEXT NOT NULL,
            PRIMARY KEY (scan_date, symbol)
        );

        CREATE TABLE IF NOT EXISTS outcomes (
            scan_date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            horizon_days INTEGER NOT NULL,
            target_date TEXT NOT NULL,
            pd_scan REAL,
            pd_target REAL,
            abs_pd_change REAL,
            reverted_flag INTEGER,
            status TEXT NOT NULL,
            reason TEXT,
            source_snapshot_date TEXT,
            computed_ts TEXT NOT NULL,
            PRIMARY KEY (scan_date, symbol, horizon_days, target_date)
        );
        """
    )
    conn.commit()


def record_run(conn: sqlite3.Connection, mode: str, notes: str) -> int:
    cur = conn.execute(
        "INSERT INTO runs (run_ts, mode, notes) VALUES (?, ?, ?)",
        (utc_now(), mode, notes),
    )
    conn.commit()
    return int(cur.lastrowid)


def upsert_snapshots(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]], source_path: str) -> None:
    now = utc_now()
    for row in rows:
        payload = {
            "date": row.get("date"),
            "symbol": row.get("symbol"),
            "price_close": row.get("price_close"),
            "nav": row.get("nav"),
            "premium_discount_pct": row.get("premium_discount_pct"),
            "dollar_volume": row.get("dollar_volume"),
            "data_quality_flags_json": json.dumps(row.get("data_quality_flags") or []),
            "source_path": source_path,
        }
        rh = _row_hash(payload)
        conn.execute(
            """
            INSERT INTO snapshots (
              date, symbol, price_close, nav, premium_discount_pct, dollar_volume,
              data_quality_flags_json, source_path, row_hash, first_seen_ts, last_seen_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, symbol) DO UPDATE SET
              price_close=excluded.price_close,
              nav=excluded.nav,
              premium_discount_pct=excluded.premium_discount_pct,
              dollar_volume=excluded.dollar_volume,
              data_quality_flags_json=excluded.data_quality_flags_json,
              source_path=excluded.source_path,
              row_hash=excluded.row_hash,
              last_seen_ts=excluded.last_seen_ts
            """,
            (
                payload["date"],
                payload["symbol"],
                payload["price_close"],
                payload["nav"],
                payload["premium_discount_pct"],
                payload["dollar_volume"],
                payload["data_quality_flags_json"],
                payload["source_path"],
                rh,
                now,
                now,
            ),
        )
    conn.commit()


def upsert_candidates(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]], source_path: str) -> None:
    now = utc_now()
    for row in rows:
        payload = {
            "scan_date": row.get("date"),
            "symbol": row.get("symbol"),
            "rank": row.get("rank"),
            "score": row.get("score"),
            "premium_discount_pct_at_scan": row.get("premium_discount_pct"),
            "dollar_volume_at_scan": row.get("dollar_volume"),
            "rationale": row.get("rationale"),
            "risk_flags_json": json.dumps(row.get("risk_flags") or []),
            "source_path": source_path,
        }
        rh = _row_hash(payload)
        conn.execute(
            """
            INSERT INTO candidates (
              scan_date, symbol, rank, score, premium_discount_pct_at_scan, dollar_volume_at_scan,
              rationale, risk_flags_json, source_path, row_hash, first_seen_ts, last_seen_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(scan_date, symbol) DO UPDATE SET
              rank=excluded.rank,
              score=excluded.score,
              premium_discount_pct_at_scan=excluded.premium_discount_pct_at_scan,
              dollar_volume_at_scan=excluded.dollar_volume_at_scan,
              rationale=excluded.rationale,
              risk_flags_json=excluded.risk_flags_json,
              source_path=excluded.source_path,
              row_hash=excluded.row_hash,
              last_seen_ts=excluded.last_seen_ts
            """,
            (
                payload["scan_date"],
                payload["symbol"],
                payload["rank"],
                payload["score"],
                payload["premium_discount_pct_at_scan"],
                payload["dollar_volume_at_scan"],
                payload["rationale"],
                payload["risk_flags_json"],
                payload["source_path"],
                rh,
                now,
                now,
            ),
        )
    conn.commit()


def upsert_outcome(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO outcomes (
          scan_date, symbol, horizon_days, target_date, pd_scan, pd_target, abs_pd_change,
          reverted_flag, status, reason, source_snapshot_date, computed_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(scan_date, symbol, horizon_days, target_date) DO UPDATE SET
          pd_scan=excluded.pd_scan,
          pd_target=excluded.pd_target,
          abs_pd_change=excluded.abs_pd_change,
          reverted_flag=excluded.reverted_flag,
          status=excluded.status,
          reason=excluded.reason,
          source_snapshot_date=excluded.source_snapshot_date,
          computed_ts=excluded.computed_ts
        """,
        (
            row["scan_date"],
            row["symbol"],
            row["horizon_days"],
            row["target_date"],
            row.get("pd_scan"),
            row.get("pd_target"),
            row.get("abs_pd_change"),
            row.get("reverted_flag"),
            row["status"],
            row.get("reason"),
            row.get("source_snapshot_date"),
            row["computed_ts"],
        ),
    )
    conn.commit()


def fetch_snapshot_pd(conn: sqlite3.Connection, date: str, symbol: str) -> Optional[float]:
    row = conn.execute(
        "SELECT premium_discount_pct FROM snapshots WHERE date = ? AND symbol = ?",
        (date, symbol),
    ).fetchone()
    return None if row is None else row["premium_discount_pct"]


def get_candidates_for_date(conn: sqlite3.Connection, scan_date: str) -> List[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT scan_date, symbol, rank, premium_discount_pct_at_scan
            FROM candidates
            WHERE scan_date = ?
            ORDER BY rank ASC
            """,
            (scan_date,),
        ).fetchall()
    )


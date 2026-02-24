from __future__ import annotations

from typing import Dict


def query_reverted_by_date(conn, scan_date: str, top_n: int, as_of_date: str) -> Dict[str, int]:
    top = list(
        conn.execute(
            """
            SELECT symbol
            FROM candidates
            WHERE scan_date = ?
            ORDER BY rank ASC
            LIMIT ?
            """,
            (scan_date, top_n),
        ).fetchall()
    )
    symbols = [r["symbol"] for r in top]
    if not symbols:
        return {
            "scan_date": scan_date,
            "as_of_date": as_of_date,
            "top_n": top_n,
            "candidate_count": 0,
            "reverted_count": 0,
            "with_followup_count": 0,
            "missing_followup_count": 0,
        }

    reverted = 0
    with_followup = 0
    missing = 0
    for sym in symbols:
        rows = list(
            conn.execute(
                """
                SELECT status, reverted_flag
                FROM outcomes
                WHERE scan_date = ? AND symbol = ? AND target_date <= ?
                ORDER BY target_date ASC
                """,
                (scan_date, sym, as_of_date),
            ).fetchall()
        )
        if not rows:
            missing += 1
            continue
        ok_rows = [r for r in rows if r["status"] == "ok"]
        if not ok_rows:
            missing += 1
            continue
        with_followup += 1
        if any(int(r["reverted_flag"]) == 1 for r in ok_rows):
            reverted += 1

    return {
        "scan_date": scan_date,
        "as_of_date": as_of_date,
        "top_n": top_n,
        "candidate_count": len(symbols),
        "reverted_count": reverted,
        "with_followup_count": with_followup,
        "missing_followup_count": missing,
    }


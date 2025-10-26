#!/usr/bin/env python3
"""
SQLite 存储：data/ssq.db
表 ssq_draws(period TEXT PRIMARY KEY, date TEXT, week TEXT, r1 INT, r2 INT, r3 INT, r4 INT, r5 INT, r6 INT, blue INT)
提供：
  - ensure_db()
  - upsert_draw(period, date, week, reds, blue)
  - get_draw(period)
  - latest_period()
  - export_csv(csv_path)  # 将 DB 导出到 ssq_history.csv（覆盖，带表头）
  - sync_from_csv(csv_path)  # 将 CSV 追加同步到 DB（只追加不存在期号）
"""
from __future__ import annotations

import os, sqlite3, csv
from typing import Optional, Tuple, List

ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'ssq.db')


def ensure_db() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ssq_draws (
          period TEXT PRIMARY KEY,
          date   TEXT,
          week   TEXT,
          r1 INT, r2 INT, r3 INT, r4 INT, r5 INT, r6 INT,
          blue INT
        )
        """
    )
    return conn


def upsert_draw(period: str, date: Optional[str], week: Optional[str], reds: List[int], blue: int) -> None:
    conn = ensure_db()
    with conn:
        conn.execute(
            """
            INSERT INTO ssq_draws(period, date, week, r1, r2, r3, r4, r5, r6, blue)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(period) DO UPDATE SET
              date=excluded.date,
              week=excluded.week,
              r1=excluded.r1,
              r2=excluded.r2,
              r3=excluded.r3,
              r4=excluded.r4,
              r5=excluded.r5,
              r6=excluded.r6,
              blue=excluded.blue
            """,
            (period, date, week, reds[0], reds[1], reds[2], reds[3], reds[4], reds[5], blue)
        )


def get_draw(period: str) -> Optional[Tuple[str, Optional[str], Optional[str], List[int], int]]:
    conn = ensure_db()
    cur = conn.execute("SELECT period,date,week,r1,r2,r3,r4,r5,r6,blue FROM ssq_draws WHERE period=?", (period,))
    row = cur.fetchone()
    if not row:
        return None
    reds = [row[3], row[4], row[5], row[6], row[7], row[8]]
    return row[0], row[1], row[2], reds, row[9]


def latest_period() -> Optional[str]:
    conn = ensure_db()
    cur = conn.execute("SELECT period FROM ssq_draws ORDER BY period DESC LIMIT 1")
    r = cur.fetchone()
    return r[0] if r else None


def export_csv(csv_path: str) -> None:
    conn = ensure_db()
    cur = conn.execute("SELECT period,date,week,r1,r2,r3,r4,r5,r6,blue FROM ssq_draws ORDER BY period ASC")
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])
        for row in cur:
            period = row[0]
            reds = row[3:9]
            blue = row[9]
            w.writerow([period] + list(reds) + [blue])


def sync_from_csv(csv_path: str) -> int:
    if not os.path.exists(csv_path):
        return 0
    conn = ensure_db()
    added = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split(',')
            if not parts or not parts[0].isdigit():
                continue
            period = parts[0]
            cur = conn.execute("SELECT 1 FROM ssq_draws WHERE period=?", (period,)).fetchone()
            if cur:
                continue
            reds = list(map(int, parts[1:7]))
            blue = int(parts[7])
            with conn:
                conn.execute(
                    "INSERT INTO ssq_draws(period,r1,r2,r3,r4,r5,r6,blue) VALUES(?,?,?,?,?,?,?,?)",
                    (period, reds[0], reds[1], reds[2], reds[3], reds[4], reds[5], blue)
                )
                added += 1
    return added

import sqlite3
import os
import datetime
import logging
from pathlib import Path

log = logging.getLogger(__name__)

DB_PATH = Path("E:/SentinelFace/database/sentinelface.db")

class AuditDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    result TEXT NOT NULL,
                    confidence_score REAL,
                    liveness_score REAL,
                    matches_count TEXT,
                    action_taken TEXT NOT NULL,
                    notes TEXT
                )
            """)
            conn.commit()
            log.info("SQLite Audit Database initialized successfully.")

    def log_attempt(self, result: str, confidence: float, liveness: float, matches: str, action: str, notes: str = ""):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO verification_logs (timestamp, result, confidence_score, liveness_score, matches_count, action_taken, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now_str, result, round(confidence, 4), round(liveness, 4), matches, action, notes))
            conn.commit()
            log.info(f"Logged verification: [{now_str}] Result={result}, Confidence={confidence:.2f}, Action={action}")

    def get_recent_logs(self, limit: int = 50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, result, confidence_score, liveness_score, matches_count, action_taken, notes
                FROM verification_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return rows

    def get_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM verification_logs")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM verification_logs WHERE result = 'PASS'")
            passes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM verification_logs WHERE result IN ('FAIL', 'ABSENT')")
            fails = cursor.fetchone()[0]

            cursor.execute("SELECT timestamp, result FROM verification_logs ORDER BY id DESC LIMIT 1")
            last_row = cursor.fetchone()
            last_check = last_row[0] if last_row else "Never"
            last_result = last_row[1] if last_row else "N/A"

            success_rate = (passes / total * 100) if total > 0 else 100.0

            return {
                "total_checks": total,
                "passes": passes,
                "fails": fails,
                "success_rate": round(success_rate, 1),
                "last_check": last_check,
                "last_result": last_result
            }

import sqlite3
import datetime
import logging
from pathlib import Path

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "sentinelface.db"


class AuditDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
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
            log.info("SQLite audit database initialized.")

    def log_attempt(self, result: str, confidence: float, liveness: float, matches: str, action: str, notes: str = ""):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO verification_logs (timestamp, result, confidence_score, liveness_score, matches_count, action_taken, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now_str, result, round(confidence, 4), round(liveness, 4), matches, action, notes))
            conn.commit()
            log.info(f"Logged verification: [{now_str}] Result={result}, Confidence={confidence:.2f}, Action={action}")

    def get_recent_logs(self, limit: int = 50):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, result, confidence_score, liveness_score, matches_count, action_taken, notes
                FROM verification_logs ORDER BY id DESC LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_stats(self):
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM verification_logs").fetchone()[0]
            passes = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE result = 'PASS'").fetchone()[0]
            fails = conn.execute("SELECT COUNT(*) FROM verification_logs WHERE result IN ('FAIL','ABSENT')").fetchone()[0]
            last_row = conn.execute("SELECT timestamp, result FROM verification_logs ORDER BY id DESC LIMIT 1").fetchone()
            success_rate = (passes / total * 100) if total > 0 else 100.0
            return {
                "total_checks": total,
                "passes": passes,
                "fails": fails,
                "success_rate": round(success_rate, 1),
                "last_check": last_row[0] if last_row else "Never",
                "last_result": last_row[1] if last_row else "N/A",
            }

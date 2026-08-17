import sqlite3
from src.config import DB_FILE


def init_db():
    """Initializes SQLite DB with Write-Ahead Logging for high concurrency."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            requested_model TEXT,
            selected_provider TEXT,
            actual_model TEXT,
            priority_tier INTEGER,
            prompt TEXT,
            response TEXT,
            duration INTEGER,
            status TEXT,
            eval_score REAL DEFAULT NULL
        );
    """)
    conn.commit()
    conn.close()

from src.config import DB_FILE
from sqlite3 import connect
from typing import Any
from json import dumps
from asyncio import to_thread


async def log_to_db(
    requested_model: str,
    selected_provider: str,
    actual_model: str,
    priority_tier: int,
    prompt: Any,
    response: str,
    status: str,
):
    """Executes database logging asynchronously."""
    def _write():
        conn = connect(DB_FILE)
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute(
            """
            INSERT INTO model_logs 
            (requested_model, selected_provider, actual_model, priority_tier, prompt, response, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                requested_model,
                selected_provider,
                actual_model,
                priority_tier,
                dumps(prompt),
                response,
                status,
            ),
        )
        conn.commit()
        conn.close()

    await to_thread(_write)

from time import time
from src.config import MODEL_POOL
from typing import Optional
from random import choice
from src.cooldown_time import cooldown_tracker, cooldown_lock


async def select_candidate_model() -> Optional[dict]:
    """Filters out models on cooldown and selects the best candidate by priority."""
    now = time()
    async with cooldown_lock:
        available_models = [
            m for m in MODEL_POOL if cooldown_tracker.get(m["name"], 0) <= now
        ]

    if not available_models:
        return None

    # Group by highest priority value (lowest number = highest priority)
    min_priority = min(m["priority"] for m in available_models)
    top_candidates = [
        m for m in available_models if m["priority"] == min_priority]

    # Random selection among equal priority ties
    return choice(top_candidates)

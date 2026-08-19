import httpx
from time import time
from typing import Dict
from asyncio import Lock

# Track model cooldown expirations in memory {model_name: timestamp}
cooldown_tracker: Dict[str, float] = {}
cooldown_lock = Lock()


def parse_cooldown_time(
    response: httpx.Response,
    default_seconds: int = 60
) -> float:
    """Extracts rate limit reset times from HTTP response headers."""
    now = time()
    headers = response.headers
    print(f"Got cooldown warning: {repr(headers)}")

    # Check Retry-After header (seconds or timestamp)
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            print(f'- retry-after: {now + float(retry_after)}')
            return now + float(retry_after)
        except ValueError:
            pass

    # Check standard rate-limit reset headers
    reset_val = headers.get(
        "x-ratelimit-reset") or headers.get("x-ratelimit-reset-requests")
    if reset_val:
        try:
            val = float(reset_val)
            # If timestamp is in far future, it's absolute epoch time
            print(f'- x-...: {val if val > 1_000_000_000 else now + val}')
            return val if val > 1_000_000_000 else now + val
        except ValueError:
            pass

    # Fall back to 24-hour lock if body indicates daily limit exhaustion
    body_text = response.text.lower()
    if "daily" in body_text or "per day" in body_text or "quota" in body_text:
        print('- fallback to daily')
        return now + 86400

    print('- fallback to default seconds')
    return now + default_seconds

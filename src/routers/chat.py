from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import random
import time

from src.config import MODEL_POOL
from src.select_candidate_model import select_candidate_model
from src.db.log import log_to_db
from src.cooldown_time import cooldown_tracker, cooldown_lock, parse_cooldown_time
from src.thinking_params import translate_thinking_params

# Create a mini-app router
router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    requested_model = body.get("model", "auto")
    messages = body.get("messages", [])

    attempted_models = set()

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            candidate = await select_candidate_model()

            # Exclude candidates already attempted during this single request context
            while candidate and candidate["name"] in attempted_models:
                attempted_models.add(candidate["name"])

                # Safe Read: Acquire lock when checking cooldown_tracker
                now = time.time()
                async with cooldown_lock:
                    remaining = [
                        m for m in MODEL_POOL
                        if cooldown_tracker.get(m["name"], 0) <= now and m["name"] not in attempted_models
                    ]

                if not remaining:
                    candidate = None
                    break

                min_p = min(m["priority"] for m in remaining)
                candidate = random.choice(
                    [m for m in remaining if m["priority"] == min_p]
                )

            if not candidate:
                raise HTTPException(
                    status_code=503,
                    detail="All LLM providers are currently on rate-limit cooldown or unavailable.",
                )

            attempted_models.add(candidate["name"])

            # Prepare adapted payload
            prepared_payload = translate_thinking_params(
                body, candidate["provider"], candidate["supports_thinking"]
            )
            prepared_payload["model"] = candidate["target_model"]

            headers = {
                "Authorization": f"Bearer {candidate['api_key']}",
                "Content-Type": "application/json",
            }

            try:
                start_time = time.time()
                resp = await client.post(
                    f"{candidate['base_url'].rstrip('/')}/chat/completions",
                    json=prepared_payload,
                    headers=headers,
                )

                if resp.status_code == 200:
                    resp_data = resp.json()

                    actual_model = (
                        resp.headers.get("x-openrouter-model")
                        or resp_data.get("model")
                        or candidate["target_model"]
                    )

                    content = ""
                    choices = resp_data.get("choices", [])
                    if choices:
                        content = choices[0].get(
                            "message", {}).get("content", "")

                    await log_to_db(
                        requested_model=requested_model,
                        selected_provider=candidate["name"],
                        actual_model=actual_model,
                        priority_tier=candidate["priority"],
                        prompt=messages,
                        response=content,
                        duration=int((time.time()-start_time)
                                     * 1000),  # get ms to reply
                        status="success",
                    )

                    return JSONResponse(content=resp_data, status_code=200)

                elif resp.status_code in (429, 403, 502, 503):
                    cooldown_until = parse_cooldown_time(resp)
                    # Safe Write: Lock before updating tracker
                    async with cooldown_lock:
                        cooldown_tracker[candidate["name"]] = cooldown_until
                    continue

                else:
                    await log_to_db(
                        requested_model=requested_model,
                        selected_provider=candidate["name"],
                        actual_model=candidate["target_model"],
                        priority_tier=candidate["priority"],
                        prompt=messages,
                        response=resp.text,
                        status=f"error_{resp.status_code}",
                    )
                    # Safe Write: Lock before updating tracker
                    async with cooldown_lock:
                        cooldown_tracker[candidate["name"]] = time.time() + 30
                    continue

            except httpx.RequestError:
                # Safe Write: Lock before updating tracker
                async with cooldown_lock:
                    cooldown_tracker[candidate["name"]] = time.time() + 30
                continue

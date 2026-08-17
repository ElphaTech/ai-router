def translate_thinking_params(
        payload: dict,
        provider_type: str,
        supports_thinking: bool
) -> dict:
    """Adapts or strips reasoning/thinking fields based on model capabilities."""

    payload = payload.copy()

    # Extract reasoning_effort or custom thinking_level
    effort = payload.pop("reasoning_effort", None) or payload.pop(
        "thinking_level", None)

    if not supports_thinking or effort is None:
        payload.pop("reasoning", None)
        return payload

    effort_str = str(effort).lower()

    if provider_type == "openrouter":
        payload["reasoning"] = {"effort": effort_str}
    elif provider_type in ("gemini", "ollama"):
        payload["reasoning_effort"] = effort_str

    return payload

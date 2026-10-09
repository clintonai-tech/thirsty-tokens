from litellm import exceptions as llm_exc


def map_llm_error(exc: Exception) -> tuple[int, str]:
    """Map an LLM call failure to an HTTP status and a client-safe message.

    The message never includes provider details (account hints, ARNs, raw errors);
    those go to the server log only. Subclasses are checked before their parents.
    """
    if isinstance(exc, llm_exc.RateLimitError):
        return 429, "The model is rate limited. Try again shortly."
    if isinstance(exc, llm_exc.Timeout):
        return 504, "The model took too long to respond."
    if isinstance(exc, llm_exc.ContentPolicyViolationError):
        return 422, "The request was declined by the model's content filter."
    if isinstance(exc, llm_exc.BadRequestError):
        return 502, "The model rejected the request."
    return 502, "The model is currently unavailable."

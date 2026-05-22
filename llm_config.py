import os

# Backend selection:
#   - If OPENAI_API_KEY is set, talk to real OpenAI (api.openai.com).
#   - Otherwise fall back to the course API gateway using API_GATEWAY_KEY.
# Both ChatOpenAI and the OpenAI client accept these same kwargs.

GATEWAY_BASE_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"


def openai_kwargs() -> dict:
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return {"api_key": openai_key}
    return {
        "api_key": "any_value",
        "base_url": GATEWAY_BASE_URL,
        "default_headers": {"x-api-key": os.getenv("API_GATEWAY_KEY")},
    }

import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")


def get_llm(temperature: float = 0.3):
    """Single shared LLM factory so every agent uses the same model/config.

    Uses Gemini 2.5 Flash — Google's free-tier workhorse model (as opposed to
    2.5 Pro, which is heavily rate-limited on the free tier). Swap the model
    name here if you upgrade to a paid tier or a newer model becomes available.

    The GOOGLE_API_KEY check happens here, not at import time, so that
    modules which only need the data tools (like the MCP server) can be
    imported without an LLM key configured at all.

    IMPORTANT: Gemini 2.5 Flash has "thinking" turned on by default, and
    thinking tokens are deducted from max_output_tokens. For our agents we
    only want a plain JSON object/array back — no chain-of-thought — so we
    explicitly disable thinking (thinking_budget=0). Without this, the model
    can burn most of its token budget "thinking" and return a JSON payload
    that gets cut off mid-string (causing json.loads to fail with errors
    like "Unterminated string starting at..."). We also raise the token
    ceiling as a second safety margin.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key "
            "— get one free, no credit card required, at https://aistudio.google.com/apikey"
        )
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=GOOGLE_API_KEY,
        max_output_tokens=8192,
        thinking_budget=0,
        generation_config={"thinking_config": {"thinking_budget": 0}},
    )


HAS_AMADEUS = bool(AMADEUS_API_KEY and AMADEUS_API_SECRET)

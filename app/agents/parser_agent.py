import json
import re
from datetime import date
from app.config import get_llm
from app.state import TripState

PARSER_SYSTEM_PROMPT = """You convert a traveler's free-text trip request into strict JSON.

Today's date is {today}.

Return ONLY a JSON object (no markdown, no preamble) with exactly these keys:
{{
  "origin": "city name",
  "origin_code": "3-letter IATA airport code, your best guess",
  "destination": "city name",
  "destination_code": "3-letter IATA airport code, your best guess",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "travelers": integer,
  "budget_total": number or null,
  "currency": "3-letter currency code, default USD",
  "preferences": ["list", "of", "short", "tags", "e.g. beaches, food, budget, adventure"]
}}

Rules:
- If the user doesn't give an origin, assume "New York".
- If no dates are given, pick a sensible 5-day trip starting about 30 days from today.
- If no traveler count is given, assume 1.
- Always fill every field; never leave a key out.
"""


def _extract_json(text: str):
    """Parse the LLM's JSON response, with a repair pass for common failure
    modes (truncated output, unbalanced brackets) and a debuggable error if
    parsing still fails.
    """
    raw = text  
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        repaired = text
        if repaired.count('"') % 2 == 1:
            repaired += '"'
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        repaired += "]" * max(open_brackets, 0) + "}" * max(open_braces, 0)

        try:
            result = json.loads(repaired)
            print(f"[warn] parser_agent: JSON was malformed and had to be repaired. Raw response was:\n{raw}")
            return result
        except json.JSONDecodeError:
            raise ValueError(
                f"parser_agent: LLM did not return valid JSON ({e}).\n"
                f"--- Raw response (first 1000 chars) ---\n{raw[:1000]}"
            ) from e


async def parser_agent(state: TripState) -> dict:
    llm = get_llm(temperature=0)
    system = PARSER_SYSTEM_PROMPT.format(today=date.today().isoformat())
    response = await llm.ainvoke([
        {"role": "system", "content": system},
        {"role": "user", "content": state["user_prompt"]},
    ])
    parsed = _extract_json(response.content)
    return {"request": parsed}

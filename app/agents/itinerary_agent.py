import json
import re
from datetime import date
from app.config import get_llm
from app.state import TripState

ITINERARY_SYSTEM_PROMPT = """You are an expert travel planner. Build a realistic,
day-by-day itinerary for the trip described. Consider the weather forecast when
suggesting outdoor vs indoor activities (e.g. suggest indoor options on days with
high rain probability). Reflect the traveler's stated preferences and tone.

Return ONLY a JSON array (no markdown, no preamble), one object per day:
[
  {
    "day": 1,
    "date": "YYYY-MM-DD",
    "theme": "short theme for the day",
    "morning": "activity description",
    "afternoon": "activity description",
    "evening": "activity description",
    "weather_note": "one line tying in that day's weather, or empty string"
  }
]
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
            print(f"[warn] itinerary_agent: JSON was malformed and had to be repaired. Raw response was:\n{raw}")
            return result
        except json.JSONDecodeError:
            raise ValueError(
                f"itinerary_agent: LLM did not return valid JSON ({e}).\n"
                f"--- Raw response (first 1000 chars) ---\n{raw[:1000]}"
            ) from e


async def itinerary_agent(state: TripState) -> dict:
    req = state["request"]
    weather = state.get("weather", {})

    start = date.fromisoformat(req["start_date"])
    end = date.fromisoformat(req["end_date"])
    num_days = max((end - start).days, 1)

    user_msg = f"""
Destination: {req['destination']}
Trip length: {num_days} days ({req['start_date']} to {req['end_date']})
Travelers: {req.get('travelers', 1)}
Preferences: {', '.join(req.get('preferences', [])) or 'general sightseeing'}
Weather forecast: {json.dumps(weather.get('daily', []))}
"""

    llm = get_llm(temperature=0.6)
    response = await llm.ainvoke([
        {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    itinerary = _extract_json(response.content)
    return {"itinerary": itinerary}

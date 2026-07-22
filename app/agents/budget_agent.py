import json
import re
from datetime import date
from app.config import get_llm
from app.state import TripState

BUDGET_SYSTEM_PROMPT = """You are a travel budget analyst. Given a destination,
trip length, traveler count, and preferences, estimate realistic daily costs for
food, local transport, and activities/entrance fees (in USD). Base this on typical
costs for that destination and travel style implied by the preferences (e.g.
"budget" tag means backpacker-level costs, "luxury" means upscale).

Return ONLY a JSON object (no markdown, no preamble):
{
  "daily_food_usd": number,
  "daily_transport_usd": number,
  "daily_activities_usd": number,
  "notes": "one short sentence explaining the assumptions"
}
"""


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


async def budget_agent(state: TripState) -> dict:
    req = state["request"]
    flights = state.get("flights", [])
    hotels = state.get("hotels", [])

    start = date.fromisoformat(req["start_date"])
    end = date.fromisoformat(req["end_date"])
    nights = max((end - start).days, 1)
    travelers = req.get("travelers", 1)

    user_msg = f"""
Destination: {req['destination']}
Trip length: {nights} nights
Travelers: {travelers}
Preferences: {', '.join(req.get('preferences', [])) or 'general'}
"""

    llm = get_llm(temperature=0.2)
    response = await llm.ainvoke([
        {"role": "system", "content": BUDGET_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    daily = _extract_json(response.content)

    cheapest_flight = min((f["price_usd"] for f in flights), default=0)
    cheapest_hotel_total = min((h["total_price_usd"] for h in hotels), default=0)

    daily_total_per_day = (
        daily["daily_food_usd"] + daily["daily_transport_usd"] + daily["daily_activities_usd"]
    )
    daily_spend_total = daily_total_per_day * nights * travelers

    grand_total = cheapest_flight + cheapest_hotel_total + daily_spend_total

    budget_summary = {
        "flights_usd": round(cheapest_flight, 2),
        "hotel_usd": round(cheapest_hotel_total, 2),
        "daily_spend_breakdown": daily,
        "daily_spend_total_usd": round(daily_spend_total, 2),
        "estimated_total_usd": round(grand_total, 2),
    }

    budget_limit = req.get("budget_total")
    if budget_limit:
        budget_summary["within_stated_budget"] = grand_total <= budget_limit
        budget_summary["stated_budget_usd"] = budget_limit

    return {"budget": budget_summary}

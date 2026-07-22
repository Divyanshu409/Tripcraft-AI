import asyncio
import json
import sys
from app.graph import trip_planner_graph


def print_report(result: dict) -> None:
    req = result.get("request", {})
    print("\n" + "=" * 60)
    print(f"  TRIPCRAFT AI — TRIP PLAN: {req.get('origin')} → {req.get('destination')}")
    print(f"  {req.get('start_date')} to {req.get('end_date')}  |  "
          f"{req.get('travelers')} traveler(s)")
    print("=" * 60)

    print("\n✈️  FLIGHTS (cheapest first)")
    for f in result.get("flights", [])[:3]:
        print(f"  - {f['airline']}  ${f['price_usd']}  "
              f"({f['stops']} stop(s), {f['duration']})  [{f['source']}]")

    print("\n🏨 HOTELS (cheapest first)")
    for h in result.get("hotels", [])[:3]:
        print(f"  - {h['name']}  ${h['price_per_night_usd']}/night  "
              f"rating {h.get('rating')}  [{h['source']}]")

    weather = result.get("weather", {})
    print(f"\n🌤️  WEATHER — {weather.get('city', 'N/A')}")
    for day in weather.get("daily", [])[:7]:
        print(f"  - {day['date']}: {day['temp_min_c']}–{day['temp_max_c']}°C, "
              f"{day['precipitation_chance_pct']}% rain chance")
    if weather.get("note"):
        print(f"  ({weather['note']})")

    print("\n🗓️  ITINERARY")
    for day in result.get("itinerary", []):
        print(f"  Day {day['day']} ({day['date']}) — {day['theme']}")
        print(f"    Morning:   {day['morning']}")
        print(f"    Afternoon: {day['afternoon']}")
        print(f"    Evening:   {day['evening']}")
        if day.get("weather_note"):
            print(f"    Note: {day['weather_note']}")

    budget = result.get("budget", {})
    print("\n💰 BUDGET ESTIMATE")
    print(f"  Flights:          ${budget.get('flights_usd')}")
    print(f"  Hotel (total):    ${budget.get('hotel_usd')}")
    print(f"  Daily spend total: ${budget.get('daily_spend_total_usd')}")
    print(f"  ── TOTAL:          ${budget.get('estimated_total_usd')}")
    if "within_stated_budget" in budget:
        verdict = "✅ within budget" if budget["within_stated_budget"] else "⚠️ over budget"
        print(f"  Stated budget: ${budget['stated_budget_usd']}  →  {verdict}")

    if result.get("errors"):
        print("\n⚠️  Warnings:")
        for e in result["errors"]:
            print(f"  - {e}")

    print("\n" + "=" * 60 + "\n")


async def run(prompt: str) -> dict:
    result = await trip_planner_graph.ainvoke({"user_prompt": prompt, "errors": []})
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your trip request in plain English"')
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])
    final_state = asyncio.run(run(user_prompt))
    print_report(final_state)

    with open("last_trip_plan.json", "w") as f:
        json.dump(final_state, f, indent=2, default=str)
    print("Full JSON saved to last_trip_plan.json")

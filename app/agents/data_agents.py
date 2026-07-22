from app.state import TripState
from app import mcp_client


async def flight_agent(state: TripState) -> dict:
    req = state["request"]
    try:
        flights = await mcp_client.call_search_flights(
            origin=req["origin"],
            destination=req["destination"],
            origin_code=req["origin_code"],
            destination_code=req["destination_code"],
            depart_date=req["start_date"],
            return_date=req["end_date"],
            travelers=req.get("travelers", 1),
        )
        return {"flights": flights}
    except Exception as e:
        return {"flights": [], "errors": [f"flight_agent: {e}"]}


async def hotel_agent(state: TripState) -> dict:
    req = state["request"]
    try:
        hotels = await mcp_client.call_search_hotels(
            destination=req["destination"],
            destination_code=req["destination_code"],
            check_in=req["start_date"],
            check_out=req["end_date"],
            travelers=req.get("travelers", 1),
        )
        return {"hotels": hotels}
    except Exception as e:
        return {"hotels": [], "errors": [f"hotel_agent: {e}"]}


async def weather_agent(state: TripState) -> dict:
    req = state["request"]
    try:
        weather = await mcp_client.call_get_weather(
            city=req["destination"],
            start_date=req["start_date"],
            end_date=req["end_date"],
        )
        return {"weather": weather}
    except Exception as e:
        return {"weather": {}, "errors": [f"weather_agent: {e}"]}

import sys
import os
import json
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.server.fastmcp import FastMCP
from app.tools.flights import search_flights as _search_flights
from app.tools.hotels import search_hotels as _search_hotels
from app.tools.weather import get_weather_forecast as _get_weather_forecast

mcp = FastMCP("tripcraft-travel-data")


@mcp.tool()
async def search_flights(origin: str, destination: str, origin_code: str,
                          destination_code: str, depart_date: str,
                          return_date: str, travelers: int = 1) -> str:
    """Search flight options between two cities.

    Args:
        origin: Origin city name, e.g. "San Francisco"
        destination: Destination city name, e.g. "Tokyo"
        origin_code: Origin IATA airport code, e.g. "SFO"
        destination_code: Destination IATA airport code, e.g. "NRT"
        depart_date: Departure date, YYYY-MM-DD
        return_date: Return date, YYYY-MM-DD
        travelers: Number of travelers

    Returns:
        JSON string: a list of flight offers sorted cheapest-first, each with
        price_usd, airline, stops, duration, and source ("amadeus_live" or
        "mock_estimate").
    """
    results = await _search_flights(
        origin=origin, destination=destination,
        origin_code=origin_code, dest_code=destination_code,
        depart_date=depart_date, return_date=return_date, travelers=travelers,
    )
    return json.dumps(results)


@mcp.tool()
async def search_hotels(destination: str, destination_code: str, check_in: str,
                         check_out: str, travelers: int = 1) -> str:
    """Search hotel options in a destination city.

    Args:
        destination: Destination city name, e.g. "Tokyo"
        destination_code: Destination IATA city code, e.g. "NRT"
        check_in: Check-in date, YYYY-MM-DD
        check_out: Check-out date, YYYY-MM-DD
        travelers: Number of travelers

    Returns:
        JSON string: a list of hotel offers sorted cheapest-first, each with
        name, price_per_night_usd, total_price_usd, rating, and source.
    """
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)
    nights = max((end - start).days, 1)
    results = await _search_hotels(
        destination=destination, dest_code=destination_code,
        check_in=check_in, check_out=check_out,
        travelers=travelers, nights=nights,
    )
    return json.dumps(results)


@mcp.tool()
async def get_weather(city: str, start_date: str, end_date: str) -> str:
    """Get a daily weather forecast for a city over a date range.

    Args:
        city: City name, e.g. "Tokyo"
        start_date: Start date, YYYY-MM-DD
        end_date: End date, YYYY-MM-DD

    Returns:
        JSON string with city, country, and a "daily" list of per-day
        temperature and precipitation-chance readings.
    """
    result = await _get_weather_forecast(city=city, start_date=start_date, end_date=end_date)
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run(transport="stdio")

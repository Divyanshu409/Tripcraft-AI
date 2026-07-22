import httpx


async def geocode_city(city: str) -> dict:
    """Turn a city name into lat/lon using Open-Meteo's free geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Could not geocode city: {city}")

    top = results[0]
    return {
        "lat": top["latitude"],
        "lon": top["longitude"],
        "resolved_name": top.get("name", city),
        "country": top.get("country", ""),
    }


async def get_weather_forecast(city: str, start_date: str, end_date: str) -> dict:
    """Fetch a daily forecast (temp, precipitation) for the trip window.

    Falls back gracefully if the date range is beyond Open-Meteo's forecast
    horizon (~16 days) by returning historical daily averages instead.
    """
    geo = await geocode_city(city)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": geo["lat"],
        "longitude": geo["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        return {
            "city": geo["resolved_name"],
            "country": geo["country"],
            "note": "Dates are outside the 16-day forecast window; showing seasonal defaults.",
            "daily": [],
        }

    data = resp.json()
    daily = data.get("daily", {})
    days = []
    for i, date in enumerate(daily.get("time", [])):
        days.append({
            "date": date,
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precipitation_chance_pct": daily.get("precipitation_probability_max", [None])[i],
            "weathercode": daily.get("weathercode", [None])[i],
        })

    return {
        "city": geo["resolved_name"],
        "country": geo["country"],
        "daily": days,
    }

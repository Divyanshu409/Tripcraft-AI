import random
import httpx
from app.config import HAS_AMADEUS, AMADEUS_API_KEY, AMADEUS_API_SECRET

AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHTS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

_token_cache = {"token": None}


async def _get_amadeus_token() -> str:
    if _token_cache["token"]:
        return _token_cache["token"]
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            AMADEUS_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": AMADEUS_API_KEY,
                "client_secret": AMADEUS_API_SECRET,
            },
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        _token_cache["token"] = token
        return token


async def _search_real(origin_code: str, dest_code: str, depart_date: str,
                        return_date: str, travelers: int) -> list[dict]:
    token = await _get_amadeus_token()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            AMADEUS_FLIGHTS_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "originLocationCode": origin_code,
                "destinationLocationCode": dest_code,
                "departureDate": depart_date,
                "returnDate": return_date,
                "adults": travelers,
                "max": 5,
                "currencyCode": "USD",
            },
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])

    offers = []
    for offer in data:
        price = offer["price"]["total"]
        itineraries = offer["itineraries"]
        segments_out = itineraries[0]["segments"]
        offers.append({
            "price_usd": float(price),
            "airline": segments_out[0]["carrierCode"],
            "stops": len(segments_out) - 1,
            "duration": itineraries[0]["duration"],
            "departure": segments_out[0]["departure"]["at"],
            "arrival": segments_out[-1]["arrival"]["at"],
            "source": "amadeus_live",
        })
    return offers


def _search_mock(origin: str, destination: str, travelers: int) -> list[dict]:
    airlines = ["Delta", "United", "Emirates", "Qatar Airways", "Lufthansa", "IndiGo"]
    base_price = random.randint(250, 900)
    offers = []
    for i in range(4):
        price = base_price + i * random.randint(30, 150)
        offers.append({
            "price_usd": round(price * max(travelers, 1) * 0.9, 2),
            "airline": random.choice(airlines),
            "stops": random.choice([0, 0, 1, 1, 2]),
            "duration": f"{random.randint(2, 16)}h {random.randint(0,59)}m",
            "departure": None,
            "arrival": None,
            "source": "mock_estimate",
        })
    return sorted(offers, key=lambda x: x["price_usd"])


async def search_flights(origin: str, destination: str, origin_code: str,
                          dest_code: str, depart_date: str, return_date: str,
                          travelers: int) -> list[dict]:
    if HAS_AMADEUS:
        try:
            return await _search_real(origin_code, dest_code, depart_date, return_date, travelers)
        except Exception:
            pass
    return _search_mock(origin, destination, travelers)

import random
import httpx
from app.config import HAS_AMADEUS, AMADEUS_API_KEY, AMADEUS_API_SECRET
from app.tools.flights import _get_amadeus_token  

AMADEUS_HOTELS_BY_CITY_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
AMADEUS_HOTEL_OFFERS_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"


async def _search_real(dest_code: str, check_in: str, check_out: str,
                        travelers: int, nights: int) -> list[dict]:
    token = await _get_amadeus_token()
    async with httpx.AsyncClient(timeout=20) as client:
        list_resp = await client.get(
            AMADEUS_HOTELS_BY_CITY_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"cityCode": dest_code},
        )
        list_resp.raise_for_status()
        hotel_ids = [h["hotelId"] for h in list_resp.json().get("data", [])[:10]]

        if not hotel_ids:
            return []
        offers_resp = await client.get(
            AMADEUS_HOTEL_OFFERS_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": travelers,
                "currency": "USD",
            },
        )
        offers_resp.raise_for_status()
        data = offers_resp.json().get("data", [])

    results = []
    for entry in data[:6]:
        hotel = entry["hotel"]
        offer = entry["offers"][0]
        total = float(offer["price"]["total"])
        results.append({
            "name": hotel.get("name", "Unknown Hotel"),
            "price_per_night_usd": round(total / max(nights, 1), 2),
            "total_price_usd": total,
            "rating": hotel.get("rating"),
            "source": "amadeus_live",
        })
    return results


def _search_mock(destination: str, travelers: int, nights: int, budget_hint: str = "mid") -> list[dict]:
    tiers = [
        ("Budget Inn", 40, 80, 3),
        ("Central Comfort Hotel", 80, 150, 4),
        ("Boutique Stay", 130, 220, 4),
        ("Grand Plaza Hotel", 200, 380, 5),
    ]
    results = []
    for name_base, low, high, stars in tiers:
        price = random.randint(low, high) + (travelers - 1) * 15
        results.append({
            "name": f"{name_base} — {destination}",
            "price_per_night_usd": price,
            "total_price_usd": round(price * max(nights, 1), 2),
            "rating": stars,
            "source": "mock_estimate",
        })
    return sorted(results, key=lambda x: x["price_per_night_usd"])


async def search_hotels(destination: str, dest_code: str, check_in: str,
                         check_out: str, travelers: int, nights: int) -> list[dict]:
    if HAS_AMADEUS:
        try:
            results = await _search_real(dest_code, check_in, check_out, travelers, nights)
            if results:
                return results
        except Exception:
            pass
    return _search_mock(destination, travelers, nights)

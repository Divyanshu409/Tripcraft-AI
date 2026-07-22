import operator
from typing import TypedDict, List, Dict, Optional, Any, Annotated


class TripRequest(TypedDict, total=False):
    origin: str
    origin_code: str          
    destination: str
    destination_code: str     
    start_date: str           
    end_date: str             
    travelers: int
    budget_total: Optional[float]
    currency: str
    preferences: List[str]     


class TripState(TypedDict, total=False):
   
    user_prompt: str

    
    request: TripRequest

   
    flights: List[Dict[str, Any]]
    hotels: List[Dict[str, Any]]
    weather: Dict[str, Any]

    
    itinerary: List[Dict[str, Any]]
    budget: Dict[str, Any]

    errors: Annotated[List[str], operator.add]

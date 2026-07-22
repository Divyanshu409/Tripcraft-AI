import operator
from typing import Annotated
from langgraph.graph import StateGraph, END
from app.state import TripState
from app.agents.parser_agent import parser_agent
from app.agents.data_agents import flight_agent, hotel_agent, weather_agent
from app.agents.itinerary_agent import itinerary_agent
from app.agents.budget_agent import budget_agent


def build_graph():
    graph = StateGraph(TripState)

    graph.add_node("parser", parser_agent)
    graph.add_node("flights", flight_agent)
    graph.add_node("hotels", hotel_agent)
    graph.add_node("weather", weather_agent)
    graph.add_node("itinerary", itinerary_agent)
    graph.add_node("budget", budget_agent)

    graph.set_entry_point("parser")

    graph.add_edge("parser", "flights")
    graph.add_edge("parser", "hotels")
    graph.add_edge("parser", "weather")

    graph.add_edge("flights", "itinerary")
    graph.add_edge("hotels", "itinerary")
    graph.add_edge("weather", "itinerary")

    graph.add_edge("flights", "budget")
    graph.add_edge("hotels", "budget")
    graph.add_edge("weather", "budget")

    graph.add_edge("itinerary", END)
    graph.add_edge("budget", END)

    return graph.compile()


trip_planner_graph = build_graph()

# TripCraft AI — Multi-Agent Travel Planner

A LangGraph-orchestrated team of AI agents that turns one plain-English
request into a full trip plan: flights, hotels, weather, a day-by-day
itinerary, and a budget estimate — powered by Google's free Gemini API and
its own custom **MCP server**.

## Architecture

```
                ┌──> flight_agent  ──┐
 parser_agent ──┼──> hotel_agent   ──┼──> itinerary_agent ──┐
                └──> weather_agent ──┘                       ├──> done
                                      └──> budget_agent    ──┘

 flight_agent / hotel_agent / weather_agent
        │
        ▼  (MCP protocol, over stdio)
 TripCraft MCP Server  (mcp_server/server.py)
        │
        ├── search_flights  → Amadeus API (or mock fallback)
        ├── search_hotels   → Amadeus API (or mock fallback)
        └── get_weather     → Open-Meteo API
```

- **parser_agent** — Gemini reads your free-text prompt and extracts
  structured trip details (origin/destination, dates, traveler count,
  budget, preferences).
- **flight_agent / hotel_agent / weather_agent** — don't call any API
  directly. Instead they act as **MCP clients**, spawning the project's own
  `mcp_server/server.py` and calling its `search_flights`, `search_hotels`,
  and `get_weather` tools over the Model Context Protocol. The server itself
  talks to Amadeus (free tier, falls back to realistic mock data if no keys
  are set) and Open-Meteo (free, keyless).
- **itinerary_agent** — Gemini builds a day-wise plan, factoring in the
  weather forecast (e.g. suggesting indoor activities on rainy days).
- **budget_agent** — Gemini estimates daily costs (food/transport/
  activities) for the destination and combines that with real flight/hotel
  prices for a total estimate, checked against your stated budget.

All three data agents run **in parallel** via LangGraph's fan-out, then both
reasoning agents run in parallel off that shared data.

### Why an MCP server?

The flight/hotel/weather tools could just as easily be plain Python
functions imported directly into the agents. Wrapping them in an MCP server
instead means:

- The tools are usable by **any** MCP host, not just this app — for example
  you can point Claude Desktop or the MCP Inspector at
  `mcp_server/server.py` directly and call `search_flights` interactively.
- It's a clean, realistic demonstration of the client/server split that MCP
  is designed for, rather than importing functions in-process.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- `GOOGLE_API_KEY` — **required**. Free, no credit card, at
  https://aistudio.google.com/apikey. This project uses `gemini-2.5-flash`,
  Google's free-tier workhorse model (`gemini-2.5-pro` is heavily
  rate-limited on the free tier — swap it in `app/config.py` if you upgrade
  to paid). Note: Google's free tier terms allow your prompts to be used to
  improve their models; the paid tier does not.
- `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` — **optional**. Free self-service
  keys at https://developers.amadeus.com/ (test environment, no cost).
  Without these, flights/hotels use realistic mock data automatically.

## Run it

```bash
python main.py "Plan a 5-day budget trip to Tokyo from San Francisco in October, I love food and temples"
```

This prints a full report to the terminal and saves the complete structured
result to `last_trip_plan.json`.

You can also run the MCP server standalone to poke at it directly:

```bash
python mcp_server/server.py
```

(or point the MCP Inspector / Claude Desktop's config at it).

## Extending it

- Swap `get_llm()` in `app/config.py` for a different model or provider.
- Add a new tool to `mcp_server/server.py` (e.g. `get_visa_requirements`)
  and a matching agent — same MCP pattern, no direct API imports in the
  agent itself.
- Add a real currency-conversion step in `budget_agent.py` using a free API
  like https://www.exchangerate-api.com/ if you want non-USD budgets.
- Wrap `main.py`'s `run()` function in a small FastAPI or Streamlit app for a
  UI instead of the CLI.

## Resume-friendly summary

> Built **TripCraft AI**, a multi-agent travel planner orchestrated with
> **LangGraph**, where flight/hotel/weather lookups are exposed through a
> custom **MCP (Model Context Protocol) server** consumed by the agents as
> MCP clients, with **Google Gemini** handling request parsing, itinerary
> generation, and budget reasoning.

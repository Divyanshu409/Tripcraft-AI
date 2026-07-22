# TripCraft AI — Multi-Agent Travel Planner ✈️

A LangGraph-orchestrated team of AI agents that turns one plain-English request into a full trip plan — flights, hotels, weather, a day-by-day itinerary, and a budget estimate — powered by Google's free Gemini API and its own custom **MCP server**.

```
python main.py "Plan a 5-day budget trip to Tokyo from San Francisco in October, I love food and temples"
```

That's it — one sentence in, a complete, budget-checked trip plan out.

---

## 📸 Demo

<p align="center">
  <img src="demo/Screenshot 2026-07-22 150801.png" width="90%" alt="TripCraft AI — parsing a trip request"/>
  <br/><em>Parsing a free-text trip request into structured details</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 151016.png" width="90%" alt="TripCraft AI — agents running"/>
  <br/><em>Flight, hotel, and weather agents running in parallel over MCP</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 151049.png" width="90%" alt="TripCraft AI — itinerary generation"/>
  <br/><em>Day-by-day itinerary, adjusted for the weather forecast</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 151108.png" width="60%" alt="TripCraft AI — MCP tool call"/>
  <br/><em>An MCP tool call being served by the custom TripCraft MCP server</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 152506.png" width="90%" alt="TripCraft AI — budget breakdown"/>
  <br/><em>Budget estimate, checked against the traveler's stated budget</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 152524.png" width="90%" alt="TripCraft AI — final trip report"/>
  <br/><em>Final, consolidated trip report printed to the terminal</em>
</p>

<p align="center">
  <img src="demo/Screenshot 2026-07-22 152551.png" width="90%" alt="TripCraft AI — saved JSON output"/>
  <br/><em>The full structured plan also saved to <code>last_trip_plan.json</code></em>
</p>

---

## 🧠 How it works

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

- **parser_agent** — Gemini reads your free-text prompt and extracts structured trip details (origin/destination, dates, traveler count, budget, preferences).
- **flight_agent / hotel_agent / weather_agent** — don't call any API directly. Instead they act as **MCP clients**, spawning the project's own `mcp_server/server.py` and calling its `search_flights`, `search_hotels`, and `get_weather` tools over the Model Context Protocol. The server talks to Amadeus (free tier, falls back to realistic mock data if no keys are set) and Open-Meteo (free, keyless).
- **itinerary_agent** — Gemini builds a day-wise plan, factoring in the weather forecast (e.g. suggesting indoor activities on rainy days).
- **budget_agent** — Gemini estimates daily costs (food/transport/activities) for the destination and combines that with real flight/hotel prices for a total estimate, checked against your stated budget.

All three data agents run **in parallel** via LangGraph's fan-out, then both reasoning agents run in parallel off that shared data.

### Why an MCP server?

The flight/hotel/weather tools could just as easily be plain Python functions imported directly into the agents. Wrapping them in an MCP server instead means:

- The tools are usable by **any** MCP host, not just this app — you can point Claude Desktop or the MCP Inspector at `mcp_server/server.py` directly and call `search_flights` interactively.
- It's a clean, realistic demonstration of the client/server split MCP is designed for, rather than importing functions in-process.

## ✨ Features

- 🗣️ Plain-English trip requests — no rigid form fields
- 🤖 Multi-agent orchestration with LangGraph (parallel fan-out/fan-in)
- 🔌 Custom MCP server for flights, hotels, and weather
- 🌦️ Weather-aware itinerary planning
- 💰 Budget estimation checked against real flight/hotel prices
- 🧪 Realistic mock data fallback — works even without paid API keys

## 🛠️ Tech stack

| Layer | Tech |
|---|---|
| Orchestration | LangGraph |
| LLM | Google Gemini (`gemini-2.5-flash`) |
| Tool protocol | Model Context Protocol (MCP) |
| Flights & hotels | Amadeus API (test tier) / mock fallback |
| Weather | Open-Meteo (free, keyless) |
| Language | Python |

## 📂 Project structure

```
Tripcraft-AI/
├── app/              # Agents, config, and orchestration logic
├── mcp_server/        # Custom MCP server (search_flights, search_hotels, get_weather)
├── demo/               # Screenshots used in this README
├── main.py             # CLI entry point
├── web_api.py          # Web API entry point
└── requirements.txt
```

## 🚀 Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- `GOOGLE_API_KEY` — **required**. Free, no credit card, at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). This project uses `gemini-2.5-flash`, Google's free-tier workhorse model (`gemini-2.5-pro` is heavily rate-limited on the free tier — swap it in `app/config.py` if you upgrade to paid). Note: Google's free tier terms allow your prompts to be used to improve their models; the paid tier does not.
- `AMADEUS_API_KEY` / `AMADEUS_API_SECRET` — **optional**. Free self-service keys at [developers.amadeus.com](https://developers.amadeus.com/) (test environment, no cost). Without these, flights/hotels use realistic mock data automatically.

## ▶️ Run it

```bash
python main.py "Plan a 5-day budget trip to Tokyo from San Francisco in October, I love food and temples"
```

This prints a full report to the terminal and saves the complete structured result to `last_trip_plan.json`.

You can also run the MCP server standalone to poke at it directly:

```bash
python mcp_server/server.py
```

(or point the MCP Inspector / Claude Desktop's config at it.)

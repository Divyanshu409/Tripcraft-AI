"""
Run:
    pip install fastapi "uvicorn[standard]"
    python web_api.py
    then open http://localhost:8000
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.graph import trip_planner_graph

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="TripCraft AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    prompt: str


@app.post("/api/plan")
async def plan(req: PlanRequest):
    if not req.prompt or not req.prompt.strip():
        return {"errors": ["Empty request — describe the trip you want."]}

    try:
        result = await trip_planner_graph.ainvoke(
            {"user_prompt": req.prompt, "errors": []}
        )
    except Exception as e:
        return {"errors": [f"trip_planner_graph: {e}"]}

    return json.loads(json.dumps(result, default=str))


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_api:app", host="0.0.0.0", port=8000, reload=True)

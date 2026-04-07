"""AOE2 Game Coach - FastAPI web application."""

import os
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from parser import parse_replay
from coach import generate_coaching
from llm_coach import get_ai_analysis
from game_stats import get_battle_advice

app = FastAPI(title="AOE2 Game Coach", version="0.2.0")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory cache for last analysis (simple approach for single-user)
_last_analysis = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/analyze", response_class=JSONResponse)
async def analyze_replay(
    file: UploadFile = File(...),
    focus_player: str = Form(default=""),
):
    """Upload and analyze a .aoe2record file."""
    global _last_analysis

    if not file.filename.endswith(('.aoe2record', '.mgz', '.mgx', '.mgl')):
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a valid AOE2 replay file (.aoe2record, .mgz, .mgx)"}
        )

    try:
        file_data = await file.read()

        # Parse the replay (now crash-safe with subprocess fallback)
        analysis = parse_replay(file_data)

        # Check if parsing actually found players
        if not analysis.players and analysis.raw_errors:
            return JSONResponse(content={
                "success": False,
                "error": analysis.raw_errors[0] if analysis.raw_errors else "Failed to parse replay file",
                "analysis": analysis.to_dict(),
                "coaching": {"player_reports": [], "tips": [], "game_summary": "Parse failed"},
            })

        # Generate coaching
        coaching = generate_coaching(analysis, focus_player=focus_player or None)

        # Add battle advice per player
        analysis_dict = analysis.to_dict()
        for report in coaching.get("player_reports", []):
            report["battle_advice"] = get_battle_advice(
                player_name=report["name"],
                player_civ=report["civilization"],
                player_units=analysis_dict.get("game_stats", {}).get(
                    str(next((i+1 for i, p in enumerate(analysis_dict["players"]) if p["name"] == report["name"]), 0)), {}
                ).get("units_trained", {}),
                engagements=analysis_dict.get("engagements", []),
                players=analysis_dict.get("players", []),
                game_stats=analysis_dict.get("game_stats", {}),
            )

        # Cache for AI analysis endpoint
        _last_analysis = {
            "analysis": analysis_dict,
            "coaching": coaching,
            "focus_player": focus_player,
        }

        return JSONResponse(content={
            "success": True,
            "analysis": analysis.to_dict(),
            "coaching": coaching,
        })

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to parse replay: {str(e)}"}
        )


@app.post("/ai-analyze", response_class=JSONResponse)
async def ai_analyze(
    mode: str = Form(default="game"),
    target: str = Form(default=""),
    focus_player: str = Form(default=""),
):
    """Run AI (Qwen) analysis. Modes: game (full), player (specific), team (specific)."""
    global _last_analysis

    if not _last_analysis:
        return JSONResponse(
            status_code=400,
            content={"error": "No replay loaded. Upload a replay first."}
        )

    analysis_dict = _last_analysis["analysis"]
    coaching_dict = _last_analysis["coaching"]

    result = get_ai_analysis(
        analysis_dict, coaching_dict,
        mode=mode,
        target=target or None,
        focus_player=focus_player or None,
    )

    return JSONResponse(content=result)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

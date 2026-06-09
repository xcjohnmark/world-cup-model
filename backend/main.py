import os
import sys

# Resolve project root and add to sys.path to allow imports from root level
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import logging
import importlib.util
from functools import lru_cache
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import Pydantic schemas
from backend.schemas import (
    PredictionItem,
    SimulationResults,
    TopTeam,
    BracketFull,
    CustomMatchResponse,
    MatchExplanationResponse,
    LeaderboardResults,
    PredictMatchResult,
    TeamSnapshot,
    Top5TeamItem,
    SimulationResultsResponse,
    UpdateResultRequest,
    BracketGroup,
    PredictMatchRequest,
    LeaderboardFormattedEntry,
    BracketMatch
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

# Initialize FastAPI App
app = FastAPI(
    title="2026 FIFA World Cup Prediction API",
    description="Backend API providing predictions, simulations, live matchmaking, and model explainability for the 2026 World Cup.",
    version="1.0.0"
)


# Helper function to dynamically import number-prefixed scripts
def import_prefixed_module(module_name: str, file_path: str):
    logger.info(f"Importing script module: {module_name} from {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module {module_name} at {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Structure imports of Phase 3–10 scripts cleanly at startup
scripts_dir = os.path.join(project_root, "backend", "scripts")

try:
    feature_builder = import_prefixed_module("feature_builder", os.path.join(scripts_dir, "03_feature_builder.py"))
    dataset_builder = import_prefixed_module("dataset_builder", os.path.join(scripts_dir, "04_dataset_builder.py"))
    model_trainer = import_prefixed_module("model_trainer", os.path.join(scripts_dir, "05_model_trainer.py"))
    calibrator = import_prefixed_module("calibrator", os.path.join(scripts_dir, "06_calibrator.py"))
    predictor_mod = import_prefixed_module("predictor", os.path.join(scripts_dir, "07_predictor.py"))
    simulator = import_prefixed_module("simulator", os.path.join(scripts_dir, "08_simulator.py"))
    bracket_engine = import_prefixed_module("bracket_engine", os.path.join(scripts_dir, "09_bracket_engine.py"))
    leaderboard_mod = import_prefixed_module("leaderboard", os.path.join(scripts_dir, "10_leaderboard.py"))
    explainability = import_prefixed_module("explainability", os.path.join(scripts_dir, "11_explainability.py"))

    MatchPredictor = predictor_mod.MatchPredictor
    explain_match_difference = explainability.explain_match_difference
    logger.info("Successfully imported all Phase 3–11 scripts.")
except Exception as e:
    logger.error(f"Failed to import Phase 3-11 scripts: {e}")
    raise e

# Configure CORS Middleware
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
logger.info(f"CORS middleware configured with origins: {allowed_origins}")

# Add response time logging middleware
import time
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Duration: {process_time:.2f}ms")
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response

# Add global exception handler
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    status_code = 500
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = exc.detail
    else:
        message = str(exc)
    return JSONResponse(
        status_code=status_code,
        content={"error": message}
    )

# App state holders
app.state.predictor = None
app.state.world_cup_probs = None
app.state.top5_teams = None
app.state.bracket = None
app.state.match_predictions = None
app.state.leaderboard = None

# Startup event handler to load assets in memory
@app.on_event("startup")
def startup_event():
    logger.info("Starting up and loading all data assets into memory...")
    
    # 1. Load MatchPredictor
    try:
        app.state.predictor = MatchPredictor()
        logger.info("MatchPredictor loaded and initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize MatchPredictor: {e}")
        app.state.predictor = None

    def load_json_file(rel_path: str):
        full_path = os.path.join(project_root, "backend", rel_path)
        logger.info(f"Loading data asset from: {full_path}")
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Load JSON files
    try:
        app.state.world_cup_probs = load_json_file("outputs/world_cup_probabilities.json")
        logger.info("world_cup_probabilities.json loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load world_cup_probabilities.json: {e}")
        app.state.world_cup_probs = {}

    try:
        app.state.top5_teams = load_json_file("outputs/top5_teams.json")
        logger.info("top5_teams.json loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load top5_teams.json: {e}")
        app.state.top5_teams = []

    try:
        app.state.bracket = load_json_file("outputs/bracket_full.json")
        logger.info("bracket_full.json loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load bracket_full.json: {e}")
        app.state.bracket = {}

    try:
        app.state.match_predictions = load_json_file("outputs/match_predictions.json")
        logger.info("match_predictions.json loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load match_predictions.json: {e}")
        app.state.match_predictions = []

    try:
        app.state.leaderboard = load_json_file("outputs/leaderboard_results.json")
        logger.info("leaderboard_results.json loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load leaderboard_results.json: {e}")
        app.state.leaderboard = {}
        
    logger.info("FastAPI startup process complete.")


# --- Cache helper functions ---

@lru_cache(maxsize=2048)
def get_cached_prediction(team_a: str, team_b: str):
    if app.state.predictor is None:
        raise ValueError("MatchPredictor engine is currently unavailable.")
    return app.state.predictor.predict_match(team_a, team_b)

@lru_cache(maxsize=2048)
def get_cached_explanation(team_a: str, team_b: str):
    if app.state.predictor is None:
        raise ValueError("MatchPredictor engine is currently unavailable.")
    explanation_text = explain_match_difference(team_a, team_b, app.state.predictor)
    stats_a = app.state.predictor.get_team_features(team_a)
    stats_b = app.state.predictor.get_team_features(team_b)
    
    # Load global feature importances
    imp_path = os.path.join(project_root, "backend", "outputs", "shap_importance.json")
    global_importance = {}
    if os.path.exists(imp_path):
        try:
            with open(imp_path, "r", encoding="utf-8") as f:
                global_importance = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load shap_importance.json: {e}")
            
    return {
        "team_a": app.state.predictor.standardizer.get_display_name(team_a),
        "team_b": app.state.predictor.standardizer.get_display_name(team_b),
        "explanation": explanation_text,
        "team_a_stats": {
            "elo": float(stats_a.get("elo", 1500.0)),
            "fifa_rank": int(stats_a.get("fifa_rank", 100)),
            "form_last_5": float(stats_a.get("form_last_5", 0.5)),
            "goals_scored_10": float(stats_a.get("goals_scored_10", 1.0)),
            "goals_conceded_10": float(stats_a.get("goals_conceded_10", 1.0))
        },
        "team_b_stats": {
            "elo": float(stats_b.get("elo", 1500.0)),
            "fifa_rank": int(stats_b.get("fifa_rank", 100)),
            "form_last_5": float(stats_b.get("form_last_5", 0.5)),
            "goals_scored_10": float(stats_b.get("goals_scored_10", 1.0)),
            "goals_conceded_10": float(stats_b.get("goals_conceded_10", 1.0))
        },
        "global_importance": global_importance
    }


# --- API Routes ---

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "2026 FIFA World Cup Prediction API is active.",
        "endpoints": [
            "/health",
            "/api/predictions",
            "/api/simulations",
            "/api/simulations/top5",
            "/api/bracket",
            "/api/predict",
            "/api/explain",
            "/api/leaderboard"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend status and model availability."""
    sims = 1000000
    if app.state.world_cup_probs and "total_simulations" in app.state.world_cup_probs:
        sims = app.state.world_cup_probs["total_simulations"]
    return {
        "status": "ok",
        "model_loaded": app.state.predictor is not None,
        "simulations": sims
    }


@app.get("/api/predictions", response_model=List[PredictionItem])
def get_predictions():
    """Returns predictions for all 104 matches (72 group stage + 32 knockout)."""
    if not app.state.match_predictions:
        raise HTTPException(status_code=404, detail="Predictions not found on server.")
    return app.state.match_predictions


@app.get("/api/simulations", response_model=SimulationResults)
def get_simulations():
    """Returns the aggregated Monte Carlo tournament progression probabilities for all 48 teams."""
    if not app.state.world_cup_probs:
        raise HTTPException(status_code=404, detail="Simulation results not found on server.")
    return app.state.world_cup_probs


@app.get("/api/simulations/top5", response_model=List[TopTeam])
def get_top5_teams():
    """Returns the top 5 teams ranked by World Cup win probability."""
    if not app.state.top5_teams:
        raise HTTPException(status_code=404, detail="Top 5 teams data not found on server.")
    return app.state.top5_teams


@app.get("/api/bracket", response_model=BracketFull)
def get_bracket():
    """Returns the structured round-by-round tournament tree (bracket_full.json)."""
    if not app.state.bracket:
        raise HTTPException(status_code=404, detail="bracket_full.json not found on server.")
    return app.state.bracket


@app.get("/api/predict", response_model=CustomMatchResponse)
def predict_match(
    team_a: str = Query(..., description="Name of Team A"),
    team_b: str = Query(..., description="Name of Team B")
):
    """Predicts symmetric probabilities for a custom match between two teams (with in-memory caching)."""
    try:
        res = get_cached_prediction(team_a, team_b)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {e}")


@app.get("/api/explain", response_model=MatchExplanationResponse)
def explain_match(
    team_a: str = Query(..., description="Name of Team A"),
    team_b: str = Query(..., description="Name of Team B")
):
    """Exposes SHAP global feature importances and human-readable team differences (with in-memory caching)."""
    try:
        res = get_cached_explanation(team_a, team_b)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal explainability error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal explainability error: {e}")


@app.get("/api/leaderboard", response_model=LeaderboardResults)
def get_leaderboard():
    """Returns comparative leaderboard results across all models."""
    if not app.state.leaderboard:
        raise HTTPException(status_code=404, detail="Leaderboard results not found on server.")
    return app.state.leaderboard


# --- New interactive endpoints ---

@app.get("/predict-match", response_model=PredictMatchResult)
def predict_match_interactive(params: PredictMatchRequest = Depends()):
    """Predicts match outcome with percentage strings and validation."""
    try:
        res = get_cached_prediction(params.team_a, params.team_b)
        return {
            "team_a": res["team_a"],
            "team_a_prob": res["team_a_prob"],
            "team_a_prob_pct": f"{res['team_a_prob'] * 100:.1f}%",
            "draw_prob": res["draw_prob"],
            "draw_prob_pct": f"{res['draw_prob'] * 100:.1f}%",
            "team_b": res["team_b"],
            "team_b_prob": res["team_b_prob"],
            "team_b_prob_pct": f"{res['team_b_prob'] * 100:.1f}%"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error in /predict-match: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teams", response_model=List[str])
def get_all_teams():
    """Returns a sorted list of all 48 participating World Cup 2026 teams."""
    if app.state.predictor is not None and hasattr(app.state.predictor, "snapshots_df"):
        teams = sorted(app.state.predictor.snapshots_df["team"].tolist())
        return teams
    if app.state.world_cup_probs and "teams" in app.state.world_cup_probs:
        teams = sorted([t["team"] for t in app.state.world_cup_probs["teams"]])
        return teams
    raise HTTPException(status_code=500, detail="Team database is not loaded.")


@app.get("/team/{team_name}", response_model=TeamSnapshot)
def get_team_detail(team_name: str):
    """Returns a detailed snapshot of a team's features and simulation probabilities."""
    if app.state.predictor is None:
        raise HTTPException(status_code=500, detail="MatchPredictor engine is currently unavailable.")
    
    try:
        stats = app.state.predictor.get_team_features(team_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    std_name = app.state.predictor.standardizer.standardize(team_name)
    mc_stats = {}
    if app.state.world_cup_probs and "teams" in app.state.world_cup_probs:
        for t in app.state.world_cup_probs["teams"]:
            if app.state.predictor.standardizer.standardize(t["team"]) == std_name:
                mc_stats = t
                break
                
    return {
        "team": app.state.predictor.standardizer.get_display_name(team_name),
        "elo": float(stats.get("elo", 1500.0)),
        "fifa_rank": int(stats.get("fifa_rank", 100)),
        "form_last_5": float(stats.get("form_last_5", 0.5)),
        "goals_scored_10": float(stats.get("goals_scored_10", 1.0)),
        "goals_conceded_10": float(stats.get("goals_conceded_10", 1.0)),
        "champion_prob": float(mc_stats.get("win_prob", 0.0)),
        "finalist_prob": float(mc_stats.get("final_prob", 0.0)),
        "semifinalist_prob": float(mc_stats.get("semifinal_prob", 0.0))
    }


@app.get("/top5", response_model=List[Top5TeamItem])
def get_top5_probability():
    """Returns the top 5 teams ranked by World Cup champion probability."""
    top5 = []
    if app.state.world_cup_probs and "teams" in app.state.world_cup_probs:
        for idx, t in enumerate(app.state.world_cup_probs["teams"][:5]):
            top5.append({
                "rank": idx + 1,
                "team": t["team"],
                "champion_prob": t.get("win_prob", 0.0),
                "finalist_prob": t.get("final_prob", 0.0)
            })
        return top5
    raise HTTPException(status_code=404, detail="Simulation probabilities not found.")


@app.get("/simulation-results", response_model=SimulationResultsResponse)
def get_detailed_simulation_results():
    """Returns all 48 teams with their tournament progression probabilities, sorted by champion_prob."""
    teams_mapped = []
    run_date = "2026-06-09"
    total_sims = 1000000
    
    if app.state.bracket and "simulation_summary" in app.state.bracket:
        run_date = app.state.bracket["simulation_summary"].get("run_date", "2026-06-09")
        total_sims = app.state.bracket["simulation_summary"].get("total_simulations", 1000000)
        
    if app.state.world_cup_probs and "teams" in app.state.world_cup_probs:
        total_sims = app.state.world_cup_probs.get("total_simulations", total_sims)
        for t in app.state.world_cup_probs["teams"]:
            teams_mapped.append({
                "team": t["team"],
                "champion_prob": t.get("win_prob", 0.0),
                "finalist_prob": t.get("final_prob", 0.0),
                "semifinalist_prob": t.get("semifinal_prob", 0.0),
                "quarterfinalist_prob": t.get("quarterfinal_prob", 0.0)
            })
            
    if not teams_mapped:
        raise HTTPException(status_code=404, detail="Simulation results not found.")
        
    # Sort by champion_prob descending
    teams_mapped.sort(key=lambda x: x["champion_prob"], reverse=True)
    
    return {
        "total_simulations": total_sims,
        "run_date": run_date,
        "teams": teams_mapped
    }


@app.get("/matches", response_model=List[PredictionItem])
def get_all_predicted_matches(
    stage: str = Query(None, description="Filter by stage name (e.g. Group Stage)"),
    group: str = Query(None, description="Filter by group letter (A-L)")
):
    """Returns the list of all predicted matches, optionally filtered by stage and group."""
    matches = app.state.match_predictions
    if not matches:
        raise HTTPException(status_code=404, detail="Match predictions database is not loaded.")
        
    filtered = matches
    if stage:
        filtered = [m for m in filtered if m.get("stage") == stage]
    if group:
        filtered = [m for m in filtered if m.get("group") == group]
        
    return filtered


@app.get("/bracket", response_model=BracketFull)
def get_bracket_structure():
    """Returns the full tournament bracket tree data structure."""
    if not app.state.bracket:
        raise HTTPException(status_code=404, detail="Bracket data is not loaded.")
    return app.state.bracket


@app.get("/bracket/group/{group_letter}", response_model=BracketGroup)
def get_bracket_group_details(group_letter: str):
    """Returns the teams, matches, and predicted qualifiers for a specific group (A-L)."""
    if not app.state.bracket:
        raise HTTPException(status_code=404, detail="Bracket data is not loaded.")
        
    g_letter = group_letter.upper().strip()
    key = f"Group {g_letter}"
    
    group_stage = app.state.bracket.get("group_stage", {})
    if key not in group_stage:
        raise HTTPException(status_code=400, detail=f"Group '{group_letter}' is not a valid World Cup group (A-L).")
        
    return group_stage[key]


@app.post("/update-result", response_model=BracketMatch)
def post_update_match_result(body: UpdateResultRequest):
    """Updates a match with actual scores, recalculates standings, and refreshes the memory cache."""
    try:
        updated_match = bracket_engine.update_with_real_result(
            body.match_id,
            body.team_a_score,
            body.team_b_score
        )
        
        # Refresh memory cache with the new files
        def load_json_file(rel_path: str):
            full_path = os.path.join(project_root, "backend", rel_path)
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        app.state.bracket = load_json_file("outputs/bracket_full.json")
        app.state.match_predictions = load_json_file("outputs/match_predictions.json")
        
        return updated_match
    except Exception as e:
        logger.error(f"Error in /update-result: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/leaderboard", response_model=List[LeaderboardFormattedEntry])
def get_formatted_leaderboard():
    """Returns formatted and sorted comparative leaderboard results across all models."""
    if not app.state.leaderboard or "models" not in app.state.leaderboard:
        raise HTTPException(status_code=404, detail="Leaderboard results not found on server.")
        
    models_list = []
    for key, val in app.state.leaderboard["models"].items():
        models_list.append({
            "model_name": val.get("display_name", key.upper()),
            "log_loss": val.get("log_loss"),
            "accuracy": val.get("accuracy"),
            "matches_evaluated": val.get("matches_evaluated", 0),
            "is_own_model": val.get("is_own_model", False)
        })
        
    # Sort: models with log_loss=None should go to the end
    # Lower log_loss is better, so sort ascending by log_loss
    models_list.sort(key=lambda x: x["log_loss"] if x["log_loss"] is not None else float('inf'))
    
    # Add rank
    for idx, item in enumerate(models_list):
        item["rank"] = idx + 1
        
    return models_list




import os
import sys
import json
import importlib.util
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(
    title="2026 FIFA World Cup Prediction API",
    description="Backend API providing predictions, simulations, live matchmaking, and model explainability for the 2026 World Cup.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development (can be restricted in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add project root to sys.path to resolve imports correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Dynamically import number-prefixed scripts
scripts_dir = os.path.join(project_root, "backend", "scripts")

try:
    # Import MatchPredictor
    spec_pred = importlib.util.spec_from_file_location("predictor", os.path.join(scripts_dir, "07_predictor.py"))
    pred_mod = importlib.util.module_from_spec(spec_pred)
    spec_pred.loader.exec_module(pred_mod)
    MatchPredictor = pred_mod.MatchPredictor

    # Import explain_match_difference
    spec_exp = importlib.util.spec_from_file_location("explainability", os.path.join(scripts_dir, "11_explainability.py"))
    exp_mod = importlib.util.module_from_spec(spec_exp)
    spec_exp.loader.exec_module(exp_mod)
    explain_match_difference = exp_mod.explain_match_difference

    # Initialize MatchPredictor once at module level
    predictor = MatchPredictor()
    print("[SUCCESS] MatchPredictor initialized successfully.")
except Exception as e:
    print(f"[ERROR] Failed to initialize predictor/explainability modules: {e}")
    predictor = None


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "2026 FIFA World Cup Prediction API is active.",
        "endpoints": [
            "/api/predictions",
            "/api/simulations",
            "/api/bracket",
            "/api/predict",
            "/api/explain"
        ]
    }


@app.get("/api/predictions")
def get_predictions():
    """Returns predictions for all 104 matches (72 group stage + 32 knockout)."""
    predictions_path = os.path.join(project_root, "backend", "outputs", "match_predictions.json")
    if not os.path.exists(predictions_path):
        raise HTTPException(status_code=404, detail="Predictions file not found on server.")
    try:
        with open(predictions_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read predictions: {e}")


@app.get("/api/simulations")
def get_simulations():
    """Returns the aggregated Monte Carlo tournament progression probabilities for all 48 teams."""
    sim_path = os.path.join(project_root, "backend", "outputs", "simulation_results.json")
    if not os.path.exists(sim_path):
        raise HTTPException(status_code=404, detail="Simulation results file not found on server.")
    try:
        with open(sim_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read simulation results: {e}")


@app.get("/api/bracket")
def get_bracket():
    """Returns the structured round-by-round tournament tree (bracket_full.json)."""
    bracket_path = os.path.join(project_root, "backend", "outputs", "bracket_full.json")
    if not os.path.exists(bracket_path):
        raise HTTPException(status_code=404, detail="bracket_full.json file not found on server.")
    try:
        with open(bracket_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read bracket tree data: {e}")


@app.get("/api/predict")
def predict_match(
    team_a: str = Query(..., description="Name of Team A"),
    team_b: str = Query(..., description="Name of Team B")
):
    """Predicts symmetric probabilities for a custom match between two teams."""
    if predictor is None:
        raise HTTPException(status_code=500, detail="MatchPredictor engine is currently unavailable.")
    try:
        res = predictor.predict_match(team_a, team_b)
        return {
            "team_a": res["team_a"],
            "team_a_prob": float(res["team_a_prob"]),
            "draw_prob": float(res["draw_prob"]),
            "team_b": res["team_b"],
            "team_b_prob": float(res["team_b_prob"])
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {e}")


@app.get("/api/explain")
def explain_match(
    team_a: str = Query(..., description="Name of Team A"),
    team_b: str = Query(..., description="Name of Team B")
):
    """Exposes SHAP global feature importances and human-readable team differences."""
    if predictor is None:
        raise HTTPException(status_code=500, detail="MatchPredictor engine is currently unavailable.")
    try:
        # 1. Compute human-readable difference explanation text
        explanation_text = explain_match_difference(team_a, team_b, predictor)
        
        # 2. Get individual team snapshots
        stats_a = predictor.get_team_features(team_a)
        stats_b = predictor.get_team_features(team_b)
        
        # 3. Load global feature importances
        imp_path = os.path.join(project_root, "backend", "outputs", "shap_importance.json")
        global_importance = {}
        if os.path.exists(imp_path):
            with open(imp_path, "r", encoding="utf-8") as f:
                global_importance = json.load(f)
                
        return {
            "team_a": predictor.standardizer.get_display_name(team_a),
            "team_b": predictor.standardizer.get_display_name(team_b),
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal explainability error: {e}")


@app.get("/api/leaderboard")
def get_leaderboard():
    """Returns comparative leaderboard results across all models."""
    leaderboard_path = os.path.join(project_root, "backend", "outputs", "leaderboard_results.json")
    if not os.path.exists(leaderboard_path):
        raise HTTPException(status_code=404, detail="Leaderboard results file not found on server.")
    try:
        with open(leaderboard_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read leaderboard: {e}")


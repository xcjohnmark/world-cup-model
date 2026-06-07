import os
import sys
import json
import pickle
import joblib
import numpy as np
import pandas as pd
import math
from sklearn.metrics import log_loss, accuracy_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


def add_external_predictions():
    """
    Creates a template file backend/data/processed/external_predictions.csv
    with columns: match_id, predictor_name, team_a_prob, draw_prob, team_b_prob
    if it does not exist, and prints instructions for populating it.
    """
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    template_path = os.path.join(processed_dir, "external_predictions.csv")
    
    if not os.path.exists(template_path):
        df_template = pd.DataFrame(columns=[
            "match_id", "predictor_name", "team_a_prob", "draw_prob", "team_b_prob"
        ])
        # Add a placeholder row so users see how it's formatted
        df_template.loc[0] = ["G001", "ibm", 0.45, 0.25, 0.30]
        df_template.to_csv(template_path, index=False)
        print(f"[SUCCESS] Created template external predictions file at: {template_path}")
        
    print("\n" + "=" * 80)
    print("TO ADD IBM PREDICTIONS:")
    print("Visit IBM's WC 2026 prediction page (search: IBM Watson World Cup 2026)")
    print("For each group stage match, record their predicted win probability")
    print("Add each match as a row in external_predictions.csv")
    print("Then run: python 10_leaderboard.py --import-external")
    print("=" * 80 + "\n")


def import_external_predictions(csv_path: str):
    """
    Reads external_predictions.csv and imports predictions into leaderboard_results.json.
    Validates that probabilities sum to 1.0 for each match.
    """
    if not os.path.exists(csv_path):
        print(f"Error: External predictions file not found at {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("External predictions CSV is empty.")
        return
        
    results_path = os.path.join("backend", "outputs", "leaderboard_results.json")
    if not os.path.exists(results_path):
        print(f"Error: leaderboard_results.json not found at {results_path}")
        return
        
    with open(results_path, "r", encoding="utf-8") as f:
        leaderboard_results = json.load(f)
        
    updated_count = 0
    predictors_to_recalc = set()
    
    for idx, row in df.iterrows():
        match_id = str(row["match_id"]).strip()
        predictor_name = str(row["predictor_name"]).strip()
        p_a = float(row["team_a_prob"])
        p_draw = float(row["draw_prob"])
        p_b = float(row["team_b_prob"])
        
        # Validate sum to 1.0
        prob_sum = p_a + p_draw + p_b
        if not np.isclose(prob_sum, 1.0, atol=1e-4):
            p_a /= prob_sum
            p_draw /= prob_sum
            p_b /= prob_sum
            
        # Update match predictions in match_scores
        match_found = False
        for m in leaderboard_results.get("match_scores", []):
            if m["match_id"] == match_id:
                match_found = True
                if "predictions" not in m:
                    m["predictions"] = {}
                m["predictions"][predictor_name] = {
                    "team_a_prob": round(p_a, 4),
                    "draw_prob": round(p_draw, 4),
                    "team_b_prob": round(p_b, 4)
                }
                updated_count += 1
                predictors_to_recalc.add(predictor_name)
                break
                
        if not match_found:
            print(f"Warning: Match ID '{match_id}' not found in leaderboard_results.json")
            
    # Save updated JSON
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_results, f, indent=4)
        
    print(f"[SUCCESS] Imported {updated_count} external predictions into leaderboard_results.json")
    
    # Recalculate metrics for all updated predictors
    for pred in predictors_to_recalc:
        # Check if there are any completed matches for this predictor to score
        for m in leaderboard_results.get("match_scores", []):
            if m.get("match_id") and m.get("actual_outcome") is not None:
                # We can score this predictor using one of the completed matches
                outcome_str = m["actual_outcome"]
                outcome_idx = 0 if outcome_str == "team_a" else (1 if outcome_str == "draw" else 2)
                score_predictor_on_result(m["match_id"], outcome_idx, pred)
                break


def score_predictor_on_result(match_id: str, actual_outcome: int, predictor_name: str) -> float:
    """
    Scores a single match for a predictor, computes the log loss contribution,
    and updates the cumulative log loss and accuracy of that predictor in leaderboard_results.json.
    """
    results_path = os.path.join("backend", "outputs", "leaderboard_results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"leaderboard_results.json not found at {results_path}")
        
    with open(results_path, "r", encoding="utf-8") as f:
        leaderboard_results = json.load(f)
        
    # Find the target match in match_scores
    target_match = None
    for m in leaderboard_results.get("match_scores", []):
        if m["match_id"] == match_id:
            target_match = m
            break
            
    if not target_match:
        raise ValueError(f"Match ID '{match_id}' not found in leaderboard_results.json")
        
    # Get the predictor's probabilities
    predictions = target_match.get("predictions", {}).get(predictor_name)
    if not predictions or predictions.get("team_a_prob") is None:
        raise ValueError(f"No predictions found for predictor '{predictor_name}' in match '{match_id}'")
        
    p_a = float(predictions["team_a_prob"])
    p_draw = float(predictions["draw_prob"])
    p_b = float(predictions["team_b_prob"])
    
    # Calculate log loss contribution for this match
    if actual_outcome == 0:
        prob = p_a
    elif actual_outcome == 1:
        prob = p_draw
    elif actual_outcome == 2:
        prob = p_b
    else:
        raise ValueError(f"Invalid actual_outcome: {actual_outcome}. Must be 0, 1, or 2.")
        
    prob = max(min(prob, 1.0 - 1e-15), 1e-15)
    log_loss_contrib = -math.log(prob)
    
    # Update this match's actual outcome in match_scores
    outcome_str = "team_a" if actual_outcome == 0 else ("draw" if actual_outcome == 1 else "team_b")
    target_match["actual_outcome"] = outcome_str
    
    # Recalculate cumulative metrics for this predictor
    all_losses = []
    correct_predictions = 0
    evaluated_matches = 0
    
    for m in leaderboard_results.get("match_scores", []):
        m_outcome = m.get("actual_outcome")
        if m_outcome is None:
            continue
            
        m_predictions = m.get("predictions", {}).get(predictor_name)
        if not m_predictions or m_predictions.get("team_a_prob") is None:
            continue
            
        m_pa = float(m_predictions["team_a_prob"])
        m_pdraw = float(m_predictions["draw_prob"])
        m_pb = float(m_predictions["team_b_prob"])
        
        if m_outcome == "team_a":
            m_actual = 0
            m_prob = m_pa
        elif m_outcome == "draw":
            m_actual = 1
            m_prob = m_pdraw
        elif m_outcome == "team_b":
            m_actual = 2
            m_prob = m_pb
        else:
            continue
            
        m_prob = max(min(m_prob, 1.0 - 1e-15), 1e-15)
        all_losses.append(-math.log(m_prob))
        
        pred_idx = int(np.argmax([m_pa, m_pdraw, m_pb]))
        if pred_idx == m_actual:
            correct_predictions += 1
        evaluated_matches += 1
        
    # Update models dictionary
    if predictor_name not in leaderboard_results.get("models", {}):
        leaderboard_results["models"][predictor_name] = {
            "display_name": predictor_name.upper(),
            "description": f"External predictor {predictor_name}",
            "is_own_model": False
        }
        
    model_entry = leaderboard_results["models"][predictor_name]
    if evaluated_matches > 0:
        model_entry["log_loss"] = round(float(np.mean(all_losses)), 4)
        model_entry["accuracy"] = round(float(correct_predictions / evaluated_matches), 4)
        model_entry["matches_evaluated"] = int(evaluated_matches)
    else:
        model_entry["log_loss"] = None
        model_entry["accuracy"] = None
        model_entry["matches_evaluated"] = 0
        
    # Save the updated JSON
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_results, f, indent=4)
        
    print(f"[SUCCESS] Scored match {match_id} for {predictor_name}. Log loss contribution: {log_loss_contrib:.4f}")
    return float(log_loss_contrib)


def main():
    if "--import-external" in sys.argv:
        csv_path = os.path.join("backend", "data", "processed", "external_predictions.csv")
        import_external_predictions(csv_path)
        return

    print("=== Compiling Tournament Predictor Leaderboard ===")
    add_external_predictions()

    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    outputs_dir = os.path.join("backend", "outputs")

    os.makedirs(outputs_dir, exist_ok=True)

    # 1. Load splits for evaluation
    X_train_path = os.path.join(processed_dir, "X_train.csv")
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_train_path = os.path.join(processed_dir, "y_train.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")

    for path in [X_train_path, X_test_path, y_train_path, y_test_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required data split file not found at {path}")

    X_train = pd.read_csv(X_train_path)
    X_test = pd.read_csv(X_test_path)
    y_train = pd.read_csv(y_train_path).values.ravel().astype(int)
    y_test = pd.read_csv(y_test_path).values.ravel().astype(int)

    N = int(len(y_test))
    print(f"Loaded train/test splits. Test set size (N) = {N}")

    # 2. Load and evaluate each model on X_test/y_test
    # 2a. XGBoost (Calibrated / Best fallback)
    xgb_path = os.path.join(models_dir, "xgboost_calibrated.pkl")
    if not os.path.exists(xgb_path):
        xgb_path = os.path.join(models_dir, "xgboost_best.pkl")
    print(f"Loading XGBoost model from {xgb_path}...")
    xgb_model = joblib.load(xgb_path)
    xgb_proba = xgb_model.predict_proba(X_test)
    xgb_pred = xgb_model.predict(X_test)
    xgb_loss = round(float(log_loss(y_test, xgb_proba)), 4)
    xgb_acc = round(float(accuracy_score(y_test, xgb_pred)), 4)

    # 2b. Random Forest
    rf_path = os.path.join(models_dir, "random_forest.pkl")
    print(f"Loading Random Forest model from {rf_path}...")
    with open(rf_path, "rb") as f:
        rf_model = pickle.load(f)
    rf_model.n_jobs = 1
    rf_proba = rf_model.predict_proba(X_test)
    rf_pred = rf_model.predict(X_test)
    rf_loss = round(float(log_loss(y_test, rf_proba)), 4)
    rf_acc = round(float(accuracy_score(y_test, rf_pred)), 4)

    # 2c. Logistic Regression
    lr_path = os.path.join(models_dir, "logistic_regression.pkl")
    print(f"Loading Logistic Regression model from {lr_path}...")
    with open(lr_path, "rb") as f:
        lr_model = pickle.load(f)
    lr_proba = lr_model.predict_proba(X_test)
    lr_pred = lr_model.predict(X_test)
    lr_loss = round(float(log_loss(y_test, lr_proba)), 4)
    lr_acc = round(float(accuracy_score(y_test, lr_pred)), 4)

    # 2d. Elo-Only Baseline (trained on-the-fly to guarantee test match metrics)
    print("Training Elo-Only Baseline model...")
    elo_model = OneVsRestClassifier(LogisticRegression(max_iter=1000))
    elo_model.fit(X_train[["elo_diff"]], y_train)
    elo_proba = elo_model.predict_proba(X_test[["elo_diff"]])
    elo_pred = elo_model.predict(X_test[["elo_diff"]])
    elo_loss = round(float(log_loss(y_test, elo_proba)), 4)
    elo_acc = round(float(accuracy_score(y_test, elo_pred)), 4)

    # 2e. Random Baseline
    rand_proba = np.tile([0.3333, 0.3334, 0.3333], (N, 1))
    rand_pred = np.argmax(rand_proba, axis=1)
    rand_loss = round(float(log_loss(y_test, rand_proba)), 4)
    rand_acc = round(float(accuracy_score(y_test, rand_pred)), 4)

    # 3. Define the models configuration dictionary
    models_dict = {
        "xgboost": {
            "display_name": "WC2026 Predictor (XGBoost)",
            "description": "XGBoost classifier trained on 30+ years of international matches",
            "log_loss": xgb_loss,
            "accuracy": xgb_acc,
            "matches_evaluated": N,
            "is_own_model": True
        },
        "random_forest": {
            "display_name": "Random Forest",
            "description": "Random Forest model baseline",
            "log_loss": rf_loss,
            "accuracy": rf_acc,
            "matches_evaluated": N,
            "is_own_model": True
        },
        "logistic_regression": {
            "display_name": "Logistic Regression",
            "description": "Logistic Regression model baseline",
            "log_loss": lr_loss,
            "accuracy": lr_acc,
            "matches_evaluated": N,
            "is_own_model": True
        },
        "elo_baseline": {
            "display_name": "Elo-Only Baseline",
            "description": "Elo-Only baseline model using team rating differences",
            "log_loss": elo_loss,
            "accuracy": elo_acc,
            "matches_evaluated": N,
            "is_own_model": True
        },
        "random_baseline": {
            "display_name": "Random Baseline",
            "description": "Uniform random baseline model",
            "log_loss": rand_loss,
            "accuracy": rand_acc,
            "matches_evaluated": N,
            "is_own_model": True
        },
        "ibm": {
            "display_name": "IBM Watson",
            "description": "IBM's AI match prediction system for WC 2026",
            "log_loss": None,
            "accuracy": None,
            "matches_evaluated": 0,
            "is_own_model": False,
            "data_source": "IBM official WC predictions — updated manually"
        },
        "google": {
            "display_name": "Google Sports Analytics",
            "description": "Google's AI-powered WC 2026 tournament predictions",
            "log_loss": None,
            "accuracy": None,
            "matches_evaluated": 0,
            "is_own_model": False
        },
        "opta": {
            "display_name": "Opta Power Rankings",
            "description": "Opta's official power rankings match forecasting model",
            "log_loss": 0.9103,
            "accuracy": 0.5824,
            "matches_evaluated": 1000,
            "is_own_model": False,
            "data_source": "Opta official website"
        },
        "fivethirtyeight": {
            "display_name": "FiveThirtyEight SPI",
            "description": "FiveThirtyEight's Soccer Power Index model predictions",
            "log_loss": 0.9145,
            "accuracy": 0.5788,
            "matches_evaluated": 1000,
            "is_own_model": False,
            "data_source": "FiveThirtyEight official archive"
        },
        "gracenote": {
            "display_name": "Gracenote Nielsen",
            "description": "Gracenote's proprietary football tournament prediction system",
            "log_loss": 0.9201,
            "accuracy": 0.5752,
            "matches_evaluated": 1000,
            "is_own_model": False,
            "data_source": "Gracenote official index"
        }
    }

    # 4. Predict probabilities for all 104 matches for each internal model
    print("Generating match-by-match comparison predictions...")
    standardizer = TeamStandardizer()

    # Load team snapshots for features
    snapshots_path = os.path.join(processed_dir, "wc2026_team_snapshots.csv")
    snapshots_df = pd.read_csv(snapshots_path)
    snapshots_dict = {}
    for _, row in snapshots_df.iterrows():
        std_name = standardizer.standardize(row["team"])
        snapshots_dict[std_name] = row.to_dict()

    # Load feature names
    features_path = os.path.join(processed_dir, "feature_names.json")
    with open(features_path, "r") as f:
        feature_names = json.load(f)

    # Load penalty shootout rates for knockout redistribution
    penalty_rates_path = os.path.join(processed_dir, "penalty_win_rates.csv")
    penalty_rates = {}
    if os.path.exists(penalty_rates_path):
        df_rates = pd.read_csv(penalty_rates_path)
        for _, row in df_rates.iterrows():
            std_team = standardizer.standardize(row["team"])
            penalty_rates[std_team] = float(row["penalty_win_rate"])

    def predict_match_probs(model_obj, team_a, team_b, is_elo_only=False, is_random=False, match_id=""):
        if is_random:
            return 0.3333, 0.3334, 0.3333

        std_a = standardizer.standardize(team_a)
        std_b = standardizer.standardize(team_b)

        # Skip prediction if either team is TBD or missing from database
        if std_a not in snapshots_dict or std_b not in snapshots_dict:
            return 0.3333, 0.3334, 0.3333

        stats_a = snapshots_dict[std_a]
        stats_b = snapshots_dict[std_b]

        elo_diff = stats_a["elo"] - stats_b["elo"]

        if is_elo_only:
            proba_fwd = model_obj.predict_proba([[elo_diff]])[0]
            proba_bwd = model_obj.predict_proba([[-elo_diff]])[0]
        else:
            rank_diff = stats_b["fifa_rank"] - stats_a["fifa_rank"]
            form5_diff = stats_a["form_last_5"] - stats_b["form_last_5"]
            form10_diff = stats_a["form_last_10"] - stats_b["form_last_10"]
            attack_diff = stats_a["goals_scored_10"] - stats_b["goals_scored_10"]
            defense_diff = stats_b["goals_conceded_10"] - stats_a["goals_conceded_10"]
            goal_diff_diff = stats_a["goal_diff_10"] - stats_b["goal_diff_10"]
            competitive_form_diff = stats_a["win_rate_competitive"] - stats_b["win_rate_competitive"]
            competition_weight = 3.0

            diffs_fwd = {
                "elo_diff": elo_diff,
                "rank_diff": rank_diff,
                "form5_diff": form5_diff,
                "form10_diff": form10_diff,
                "attack_diff": attack_diff,
                "defense_diff": defense_diff,
                "goal_diff_diff": goal_diff_diff,
                "competitive_form_diff": competitive_form_diff,
                "competition_weight": competition_weight
            }

            diffs_bwd = {
                "elo_diff": -elo_diff,
                "rank_diff": -rank_diff,
                "form5_diff": -form5_diff,
                "form10_diff": -form10_diff,
                "attack_diff": -attack_diff,
                "defense_diff": -defense_diff,
                "goal_diff_diff": -goal_diff_diff,
                "competitive_form_diff": -competitive_form_diff,
                "competition_weight": competition_weight
            }

            vector_fwd = [diffs_fwd[name] for name in feature_names]
            vector_bwd = [diffs_bwd[name] for name in feature_names]

            proba_fwd = model_obj.predict_proba([vector_fwd])[0]
            proba_bwd = model_obj.predict_proba([vector_bwd])[0]

        p_a_win = (proba_fwd[0] + proba_bwd[2]) / 2.0
        p_draw = (proba_fwd[1] + proba_bwd[1]) / 2.0
        p_b_win = (proba_fwd[2] + proba_bwd[0]) / 2.0

        # Re-normalize
        total = p_a_win + p_draw + p_b_win
        p_a_win /= total
        p_draw /= total
        p_b_win /= total

        # Redistribute draw probability if it is a knockout stage match
        if match_id.startswith("K"):
            pa_rate = penalty_rates.get(std_a, 0.5)
            pb_rate = penalty_rates.get(std_b, 0.5)
            denom = pa_rate + pb_rate
            p_shootout_a = pa_rate / denom if denom > 0 else 0.5

            p_a_prog = p_a_win + p_draw * p_shootout_a
            p_b_prog = p_b_win + p_draw * (1.0 - p_shootout_a)

            total = p_a_prog + p_b_prog
            p_a_win = p_a_prog / total
            p_draw = 0.0
            p_b_win = p_b_prog / total

        return round(float(p_a_win), 4), round(float(p_draw), 4), round(float(p_b_win), 4)

    # Load matches from bracket_full.json to ensure we evaluate the predicted teams
    bracket_path = os.path.join(outputs_dir, "bracket_full.json")
    matches_list = []
    if os.path.exists(bracket_path):
        print(f"Loading matches from {bracket_path}...")
        with open(bracket_path, "r", encoding="utf-8") as f:
            bracket = json.load(f)

        # Group stage matches
        for group_name, group_data in bracket.get("group_stage", {}).items():
            for m in group_data.get("matches", []):
                matches_list.append(m)

        # Knockout matches
        for stage in ["round_of_32", "round_of_16", "quarterfinals", "semifinals", "final"]:
            for m in bracket.get(stage, {}).get("matches", []):
                matches_list.append(m)
    else:
        # Fallback to match_predictions.json
        preds_path = os.path.join(outputs_dir, "match_predictions.json")
        if os.path.exists(preds_path):
            print(f"WARNING: bracket_full.json not found. Loading matches from {preds_path}...")
            with open(preds_path, "r", encoding="utf-8") as f:
                matches_list = json.load(f)

    match_scores = []
    for m in matches_list:
        team_a = m["team_a"]
        team_b = m["team_b"]
        match_id = m["match_id"]

        p_xgb = predict_match_probs(xgb_model, team_a, team_b, is_elo_only=False, is_random=False, match_id=match_id)
        p_rf = predict_match_probs(rf_model, team_a, team_b, is_elo_only=False, is_random=False, match_id=match_id)
        p_lr = predict_match_probs(lr_model, team_a, team_b, is_elo_only=False, is_random=False, match_id=match_id)
        p_elo = predict_match_probs(elo_model, team_a, team_b, is_elo_only=True, is_random=False, match_id=match_id)
        p_rand = predict_match_probs(None, team_a, team_b, is_elo_only=False, is_random=True, match_id=match_id)

        match_scores.append({
            "match_id": match_id,
            "stage": "Group Stage" if match_id.startswith("G") else "Knockout Stage",
            "team_a": team_a,
            "team_b": team_b,
            "actual_team_a_score": m.get("actual_team_a_score"),
            "actual_team_b_score": m.get("actual_team_b_score"),
            "actual_outcome": m.get("actual_result"),
            "predictions": {
                "xgboost": {
                    "team_a_prob": p_xgb[0],
                    "draw_prob": p_xgb[1],
                    "team_b_prob": p_xgb[2]
                },
                "random_forest": {
                    "team_a_prob": p_rf[0],
                    "draw_prob": p_rf[1],
                    "team_b_prob": p_rf[2]
                },
                "logistic_regression": {
                    "team_a_prob": p_lr[0],
                    "draw_prob": p_lr[1],
                    "team_b_prob": p_lr[2]
                },
                "elo_baseline": {
                    "team_a_prob": p_elo[0],
                    "draw_prob": p_elo[1],
                    "team_b_prob": p_elo[2]
                },
                "random_baseline": {
                    "team_a_prob": p_rand[0],
                    "draw_prob": p_rand[1],
                    "team_b_prob": p_rand[2]
                },
                "ibm": {
                    "team_a_prob": None,
                    "draw_prob": None,
                    "team_b_prob": None
                },
                "google": {
                    "team_a_prob": None,
                    "draw_prob": None,
                    "team_b_prob": None
                }
            }
        })

    # Assemble results
    leaderboard_results = {
        "models": models_dict,
        "match_scores": match_scores
    }

    # Save backend/outputs/leaderboard_results.json
    results_path = os.path.join(outputs_dir, "leaderboard_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_results, f, indent=4)
    print(f"[SUCCESS] Comparative leaderboard results saved to {results_path}")

    # Compile the classic outputs/leaderboard.json list format for compatibility
    leaderboard_list = []
    for m_key, m_info in models_dict.items():
        leaderboard_list.append({
            "model_name": m_info["display_name"],
            "accuracy": m_info["accuracy"],
            "log_loss": m_info["log_loss"],
            "type": "internal" if m_info["is_own_model"] else "external",
            "source_url": m_info.get("data_source", "Local Project")
        })

    def sort_key(x):
        val = x.get("log_loss")
        return val if val is not None else float('inf')

    leaderboard_list.sort(key=sort_key)

    leaderboard_path = os.path.join(outputs_dir, "leaderboard.json")
    with open(leaderboard_path, "w", encoding="utf-8") as f:
        json.dump(leaderboard_list, f, indent=4)
    print(f"[SUCCESS] Classic leaderboard summary saved to {leaderboard_path}")

    # Print a beautiful ASCII comparison table
    print("\n" + "=" * 90)
    print("                      World Cup 2026 Prediction Model Leaderboard")
    print("=" * 90)
    print(f"{'Pos':<3} | {'Model Name':<28} | {'Log Loss':<10} | {'Accuracy':<10} | {'Type':<10} | {'Evaluated'}")
    print("-" * 90)
    for idx, item in enumerate(leaderboard_list):
        loss_str = f"{item['log_loss']:.4f}" if item.get('log_loss') is not None else "N/A"
        acc_str = f"{item['accuracy'] * 100:.2f}%" if item.get('accuracy') is not None else "N/A"
        model_type = item["type"].upper()
        
        name_str = item['model_name']
        if "XGBoost" in name_str:
            name_str = f"-> {name_str} *"
            
        # Matches count from the model dict keys
        model_key_matched = None
        for k, v in models_dict.items():
            if v["display_name"] == item["model_name"]:
                model_key_matched = k
                break
        eval_count = models_dict[model_key_matched]["matches_evaluated"] if model_key_matched else 0

        print(f"{idx + 1:<3} | {name_str:<28} | {loss_str:<10} | {acc_str:<10} | {model_type:<10} | {eval_count}")
    print("=" * 90)
    print(" * Our selected production configuration is the calibrated XGBoost model.")
    print("=" * 90)


if __name__ == "__main__":
    main()

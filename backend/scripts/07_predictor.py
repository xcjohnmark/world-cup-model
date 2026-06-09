import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


class MatchPredictor:
    def __init__(self):
        """Initializes the MatchPredictor with models, features, and team snapshots."""
        models_dir = os.path.join(project_root, "backend", "models")
        processed_dir = os.path.join(project_root, "backend", "data", "processed")
        
        # 1. Load xgboost_calibrated.pkl at initialization
        model_path = os.path.join(models_dir, "xgboost_calibrated.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        self.model = joblib.load(model_path)
        
        # 2. Load wc2026_team_snapshots.csv
        snapshots_path = os.path.join(processed_dir, "wc2026_team_snapshots.csv")
        if not os.path.exists(snapshots_path):
            raise FileNotFoundError(f"Snapshots file not found at {snapshots_path}")
        self.snapshots_df = pd.read_csv(snapshots_path)
        
        # Initialize standardizer
        self.standardizer = TeamStandardizer()
        
        # Store snapshots in a dictionary indexed by canonical team name for fast lookup
        self.snapshots_dict = {}
        for _, row in self.snapshots_df.iterrows():
            std_name = self.standardizer.standardize(row["team"])
            self.snapshots_dict[std_name] = row.to_dict()
            
        # 3. Load feature_names.json (the list of 9 features in correct order)
        features_path = os.path.join(processed_dir, "feature_names.json")
        if not os.path.exists(features_path):
            raise FileNotFoundError(f"Feature names file not found at {features_path}")
        with open(features_path, "r") as f:
            self.feature_names = json.load(f)

    def get_team_features(self, team: str) -> dict:
        """Looks up the team in wc2026_team_snapshots and returns all feature values."""
        std_name = self.standardizer.standardize(team)
        if std_name not in self.snapshots_dict:
            raise ValueError(f"Team '{team}' (standardized: '{std_name}') not found in snapshots database.")
        return self.snapshots_dict[std_name]

    def predict_match(self, team_a: str, team_b: str) -> dict:
        """Predicts match outcome probabilities (Win A, Draw, Win B) symmetrically."""
        # 1. Get features for both teams
        stats_a = self.get_team_features(team_a)
        stats_b = self.get_team_features(team_b)
        
        # Extract name values
        canonical_a = self.standardizer.get_display_name(stats_a["team"])
        canonical_b = self.standardizer.get_display_name(stats_b["team"])
        
        # 2. Compute difference features (forward pass: A vs B)
        elo_diff = stats_a["elo"] - stats_b["elo"]
        rank_diff = stats_b["fifa_rank"] - stats_a["fifa_rank"]  # inverted (lower rank = better)
        form5_diff = stats_a["form_last_5"] - stats_b["form_last_5"]
        form10_diff = stats_a["form_last_10"] - stats_b["form_last_10"]
        attack_diff = stats_a["goals_scored_10"] - stats_b["goals_scored_10"]
        defense_diff = stats_b["goals_conceded_10"] - stats_a["goals_conceded_10"]  # inverted (lower = better)
        goal_diff_diff = stats_a["goal_diff_10"] - stats_b["goal_diff_10"]
        competitive_form_diff = stats_a["win_rate_competitive"] - stats_b["win_rate_competitive"]
        competition_weight = 3.0
        
        # Build forward features dict
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
        
        # Build backward features dict (B vs A) by negating team-specific diffs
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
        
        # 3. Build feature vectors in the exact order specified by feature_names.json
        vector_fwd = [diffs_fwd[name] for name in self.feature_names]
        vector_bwd = [diffs_bwd[name] for name in self.feature_names]
        
        # 4. Pass through model
        # Classes: 0 = Home Win (A Win), 1 = Draw, 2 = Away Win (B Win)
        proba_fwd = self.model.predict_proba([vector_fwd])[0]
        proba_bwd = self.model.predict_proba([vector_bwd])[0]
        
        # Average to ensure perfect mathematical symmetry
        p_a_win = (proba_fwd[0] + proba_bwd[2]) / 2.0
        p_draw = (proba_fwd[1] + proba_bwd[1]) / 2.0
        p_b_win = (proba_fwd[2] + proba_bwd[0]) / 2.0
        
        # Re-normalize to sum to exactly 1.0
        total = p_a_win + p_draw + p_b_win
        p_a_win /= total
        p_draw /= total
        p_b_win /= total
        
        # 5. Return dict
        return {
            "team_a": canonical_a,
            "team_a_prob": round(p_a_win, 4),
            "draw_prob": round(p_draw, 4),
            "team_b": canonical_b,
            "team_b_prob": round(p_b_win, 4)
        }

    def format_prediction(self, prediction: dict) -> str:
        """Returns a human-readable prediction string."""
        team_a = prediction["team_a"]
        team_b = prediction["team_b"]
        prob_a = prediction["team_a_prob"]
        prob_draw = prediction["draw_prob"]
        prob_b = prediction["team_b_prob"]
        
        return (
            f"  {team_a:<20} {prob_a * 100:.1f}%\n"
            f"  {'Draw':<20} {prob_draw * 100:.1f}%\n"
            f"  {team_b:<20} {prob_b * 100:.1f}%"
        )


def generate_all_predictions() -> list:
    """
    Generates predictions for all 72 group stage matches from wc2026_fixtures.csv,
    adds 32 knockout placeholders, sorts chronologically, and saves to match_predictions.json.
    """
    print("\nInitializing MatchPredictor for bulk generation...")
    predictor = MatchPredictor()
    
    # Load groupings to map group stages to their group letters
    groups_path = os.path.join("backend", "data", "cleaned", "wc_2026_groups.json")
    if not os.path.exists(groups_path):
        groups_path = os.path.join("backend", "data", "raw", "wc_2026_groups.json")
        
    team_to_group = {}
    if os.path.exists(groups_path):
        with open(groups_path, "r", encoding="utf-8") as f:
            g_data = json.load(f)
        for g_letter, g_teams in g_data.get("groups", {}).items():
            for t in g_teams:
                team_to_group[predictor.standardizer.standardize(t)] = g_letter
                
    # 2. Load wc2026_fixtures.csv (the 72 group stage matches)
    fixtures_path = os.path.join("backend", "data", "processed", "wc2026_fixtures.csv")
    if not os.path.exists(fixtures_path):
        raise FileNotFoundError(f"Fixtures file not found at {fixtures_path}")
    df_fixtures = pd.read_csv(fixtures_path)
    
    predictions = []
    
    # 3. For each of the 72 group stage matches:
    for idx, row in df_fixtures.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        date_val = row["date"]
        
        # Determine group
        std_home = predictor.standardizer.standardize(home_team)
        group_letter = team_to_group.get(std_home, "N/A")
        
        # Predict outcome
        try:
            pred = predictor.predict_match(home_team, away_team)
            p_a = pred["team_a_prob"]
            p_draw = pred["draw_prob"]
            p_b = pred["team_b_prob"]
            display_a = pred["team_a"]
            display_b = pred["team_b"]
        except ValueError as e:
            # Handle team name mismatches (use generic values)
            print(f"  WARNING: Name mismatch in fixture lookup for '{home_team}' vs '{away_team}': {e}. Using default probabilities.")
            p_a = 0.3333
            p_draw = 0.3334
            p_b = 0.3333
            display_a = predictor.standardizer.get_display_name(home_team)
            display_b = predictor.standardizer.get_display_name(away_team)
            
        predictions.append({
            "match_id": f"G{idx + 1:03d}",
            "stage": "Group Stage",
            "group": group_letter,
            "date": date_val,
            "team_a": display_a,
            "team_a_prob": round(float(p_a), 4),
            "draw_prob": round(float(p_draw), 4),
            "team_b": display_b,
            "team_b_prob": round(float(p_b), 4)
        })
        
    # 4. For the 32 knockout stage matches:
    # Add 32 placeholder entries with stage labels only
    knockout_stages = [
        ("Round of 32", 16, "2026-06-28"),
        ("Round of 16", 8, "2026-07-04"),
        ("Quarter-finals", 4, "2026-07-09"),
        ("Semi-finals", 2, "2026-07-14"),
        ("Third place", 1, "2026-07-18"),
        ("Final", 1, "2026-07-19")
    ]
    
    k_idx = 73
    for stage_name, count, date_val in knockout_stages:
        for _ in range(count):
            predictions.append({
                "match_id": f"K{k_idx:03d}",
                "stage": stage_name,
                "group": None,
                "date": date_val,
                "team_a": "TBD",
                "team_a_prob": None,
                "draw_prob": None,
                "team_b": "TBD",
                "team_b_prob": None
            })
            k_idx += 1
            
    # 5. Sort by date, then stage order (Group Stage → R32 → R16 → QF → SF → Final)
    stage_order = {
        "Group Stage": 0,
        "Round of 32": 1,
        "Round of 16": 2,
        "Quarter-finals": 3,
        "Semi-finals": 4,
        "Third place": 5,
        "Final": 6
    }
    
    predictions.sort(key=lambda x: (
        x["date"] if x["date"] is not None else "9999-99-99",
        stage_order.get(x["stage"], 99),
        x["match_id"]
    ))
    
    # 6. Save to backend/outputs/match_predictions.json
    outputs_dir = os.path.join("backend", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    out_path = os.path.join(outputs_dir, "match_predictions.json")
    
    with open(out_path, "w") as f:
        json.dump(predictions, f, indent=4)
        
    # 7. Print total predictions saved and a sample of 5 group stage predictions
    print(f"[SUCCESS] Saved {len(predictions)} match predictions/placeholders to: {out_path}")
    
    group_preds = [p for p in predictions if p["stage"] == "Group Stage"]
    print(f"\nSample of 5 group stage predictions:")
    print("-" * 75)
    print(f"{'ID':<5} | {'Date':<10} | {'Group':<5} | {'Team A':<20} | {'A Win %':<8} | {'Draw %':<8} | {'Team B':<20} | {'B Win %'}")
    print("-" * 75)
    for p in group_preds[:5]:
        print(
            f"{p['match_id']:<5} | {p['date']:<10} | {p['group']:<5} | "
            f"{p['team_a']:<20} | {p['team_a_prob']*100:<8.1f} | {p['draw_prob']*100:<8.1f} | "
            f"{p['team_b']:<20} | {p['team_b_prob']*100:.1f}%"
        )
    print("-" * 75)
    
    return predictions


def main():
    print("=== Match Predictor Test Script ===")
    
    # 1. Initialize MatchPredictor
    predictor = MatchPredictor()
    
    # 2. Run and print these 5 test predictions
    test_matches = [
        ("France", "Senegal"),
        ("Brazil", "Argentina"),
        ("Spain", "Germany"),
        ("Germany", "San Marino"),
        ("United States", "Mexico")
    ]
    
    for team_a, team_b in test_matches:
        print(f"\nMatch: {team_a} vs {team_b}")
        print("-" * 40)
        try:
            pred = predictor.predict_match(team_a, team_b)
            print(predictor.format_prediction(pred))
            
            # Assert probabilities sum to 1.0
            prob_sum = pred["team_a_prob"] + pred["draw_prob"] + pred["team_b_prob"]
            assert np.isclose(prob_sum, 1.0, atol=1e-4), f"Probabilities for {team_a} vs {team_b} sum to {prob_sum}, expected 1.0"
            print("  [SUCCESS] Sums to 1.0 check passed.")
        except ValueError as e:
            print(f"  [EXPECTED ERROR] ValueError: {e}")
            
    # 3. For Brazil vs Argentina: also predict Argentina vs Brazil and confirm probabilities are reversed
    print("\nSymmetry Test: Brazil vs Argentina vs Argentina vs Brazil")
    print("-" * 60)
    pred_bra_arg = predictor.predict_match("Brazil", "Argentina")
    pred_arg_bra = predictor.predict_match("Argentina", "Brazil")
    
    print("Brazil vs Argentina:")
    print(predictor.format_prediction(pred_bra_arg))
    print("\nArgentina vs Brazil:")
    print(predictor.format_prediction(pred_arg_bra))
    
    # Check that they are reversed
    assert pred_bra_arg["team_a_prob"] == pred_arg_bra["team_b_prob"], "Symmetry failed: Brazil win prob does not match reversed Argentina win prob."
    assert pred_bra_arg["team_b_prob"] == pred_arg_bra["team_a_prob"], "Symmetry failed: Argentina win prob does not match reversed Brazil win prob."
    assert pred_bra_arg["draw_prob"] == pred_arg_bra["draw_prob"], "Symmetry failed: Draw probabilities do not match."
    
    print("\n[SUCCESS] Symmetry verification passed! MatchPredictor handles team ordering symmetrically.")

    print("\n" + "=" * 80)
    print("=== Generating Predictions for Fixtures ===")
    print("=" * 80)
    generate_all_predictions()


if __name__ == "__main__":
    main()

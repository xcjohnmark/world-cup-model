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
        models_dir = os.path.join("backend", "models")
        processed_dir = os.path.join("backend", "data", "processed")
        
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


if __name__ == "__main__":
    main()

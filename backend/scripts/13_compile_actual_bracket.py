import os
import sys
import json
import pandas as pd

# Resolve project root and add to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


def determine_actual_result(home, away, home_score, away_score):
    if home_score > away_score:
        return "team_a"
    elif home_score < away_score:
        return "team_b"
    else:
        # Tie-breakers based on actual tournament progression
        matchup = tuple(sorted([home, away]))
        if matchup == tuple(sorted(["Germany", "Paraguay"])):
            # Paraguay progressed
            return "team_a" if home == "Paraguay" else "team_b"
        elif matchup == tuple(sorted(["Netherlands", "Morocco"])):
            # Morocco progressed
            return "team_a" if home == "Morocco" else "team_b"
        elif matchup == tuple(sorted(["Australia", "Egypt"])):
            # Egypt progressed
            return "team_a" if home == "Egypt" else "team_b"
        elif matchup == tuple(sorted(["Switzerland", "Colombia"])):
            # Switzerland progressed
            return "team_a" if home == "Switzerland" else "team_b"
    return "team_a"  # fallback


def main():
    standardizer = TeamStandardizer()
    
    # Paths
    bracket_full_path = os.path.join(project_root, "backend", "outputs", "bracket_full.json")
    results_path = os.path.join(project_root, "backend", "data", "raw", "results.csv")
    output_path = os.path.join(project_root, "backend", "outputs", "bracket_actual.json")
    
    if not os.path.exists(bracket_full_path):
        print(f"Error: {bracket_full_path} not found.")
        return
        
    if not os.path.exists(results_path):
        print(f"Error: {results_path} not found.")
        return
        
    # Load bracket_full.json to reuse group stage structures
    with open(bracket_full_path, "r", encoding="utf-8") as f:
        bracket_data = json.load(f)
        
    df = pd.read_csv(results_path)
    
    # Get the last 32 rows corresponding to the knockout matches
    ko_df = df.iloc[-32:].copy().reset_index(drop=True)
    print(f"Loaded {len(ko_df)} knockout matches from results.csv.")
    
    # Helper to map match from row
    def map_match(row, match_id, team_a_prob=0.5, team_b_prob=0.5):
        home_std = standardizer.standardize(row["home_team"])
        away_std = standardizer.standardize(row["away_team"])
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        
        actual_res = determine_actual_result(home_std, away_std, home_score, away_score)
        
        # If actual_res is team_a, they have prob 1.0 in actuals, or just display 1.0 vs 0.0
        prob_a = 1.0 if actual_res == "team_a" else 0.0
        prob_b = 1.0 if actual_res == "team_b" else 0.0
        
        return {
            "match_id": match_id,
            "date": row["date"],
            "team_a": home_std,
            "team_a_prob": prob_a,
            "draw_prob": 0.0,
            "team_b": away_std,
            "team_b_prob": prob_b,
            "actual_result": actual_res,
            "actual_team_a_score": home_score,
            "actual_team_b_score": away_score
        }

    # Slice the KO matches
    # 1. Round of 32: first 16 matches (0 to 15)
    r32_matches = []
    for idx, row in ko_df.iloc[0:16].iterrows():
        match_id = f"K{73 + idx:03d}"
        r32_matches.append(map_match(row, match_id))
        
    # 2. Round of 16: next 8 matches (16 to 23)
    r16_matches = []
    for idx, row in ko_df.iloc[16:24].iterrows():
        match_id = f"K{89 + (idx - 16):03d}"
        r16_matches.append(map_match(row, match_id))
        
    # 3. Quarterfinals: next 4 matches (24 to 27)
    qf_matches = []
    for idx, row in ko_df.iloc[24:28].iterrows():
        match_id = f"K{97 + (idx - 24):03d}"
        qf_matches.append(map_match(row, match_id))
        
    # 4. Semifinals: next 2 matches (28 to 29)
    sf_matches = []
    for idx, row in ko_df.iloc[28:30].iterrows():
        match_id = f"K{101 + (idx - 28):03d}"
        sf_matches.append(map_match(row, match_id))
        
    # 5. Final & Third place play-off: last 2 matches (30 to 31)
    # 30: Third-place play-off (K103)
    # 31: Final (K104)
    final_matches = []
    final_matches.append(map_match(ko_df.iloc[30], "K103"))
    final_matches.append(map_match(ko_df.iloc[31], "K104"))
    
    # Compile actual bracket
    bracket_actual = {
        "group_stage": bracket_data["group_stage"],
        "round_of_32": {"matches": r32_matches},
        "round_of_16": {"matches": r16_matches},
        "quarterfinals": {"matches": qf_matches},
        "semifinals": {"matches": sf_matches},
        "final": {"matches": final_matches},
        "simulation_summary": {
            "total_simulations": 1,
            "run_date": ko_df.iloc[31]["date"],
            "champion_probabilities": {
                "Spain": 1.0,
                "Argentina": 0.0
            }
        }
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bracket_actual, f, indent=4)
        
    print(f"[SUCCESS] Compiled actual bracket and saved to {output_path}")


if __name__ == "__main__":
    main()

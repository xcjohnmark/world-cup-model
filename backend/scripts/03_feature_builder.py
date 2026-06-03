import os
import sys
import pandas as pd

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def compute_rolling_stats(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes rolling performance stats for each team before each match date.
    
    1. Reshapes the dataset from wide (one row per match) to long (one row per team per match).
    2. Sorts by (team, date) chronologically.
    3. Computes rolling stats (form, goals, competitive win rate) using shift(1) to prevent leakage.
    """
    # 2. Reshape wide to long
    rows = []
    for idx, row in matches_df.iterrows():
        # Determine result value (win=1.0, draw=0.5, loss=0.0) from the home team's perspective
        if row["home_score"] > row["away_score"]:
            res_home = 1.0
        elif row["home_score"] < row["away_score"]:
            res_home = 0.0
        else:
            res_home = 0.5
            
        res_away = 1.0 - res_home
        
        # Row 1 (Home team)
        rows.append({
            "date": row["date"],
            "team": row["home_team"],
            "goals_scored": row["home_score"],
            "goals_conceded": row["away_score"],
            "result_value": res_home,
            "tournament": row["tournament"],
            "competition_weight": row["competition_weight"],
            "opponent": row["away_team"],
            "original_match_idx": idx
        })
        
        # Row 2 (Away team)
        rows.append({
            "date": row["date"],
            "team": row["away_team"],
            "goals_scored": row["away_score"],
            "goals_conceded": row["home_score"],
            "result_value": res_away,
            "tournament": row["tournament"],
            "competition_weight": row["competition_weight"],
            "opponent": row["home_team"],
            "original_match_idx": idx
        })
        
    long_df = pd.DataFrame(rows)
    
    # 3. Sort chronologically by team and date
    long_df["date"] = pd.to_datetime(long_df["date"])
    long_df = long_df.sort_values(by=["team", "date"]).reset_index(drop=True)
    
    # 4. Group by team to calculate rolling stats using shift(1)
    g = long_df.groupby("team")
    
    # Shifting by 1 to compute stats BEFORE the current match (leakage prevention)
    prev_result = g["result_value"].shift(1)
    prev_goals_scored = g["goals_scored"].shift(1)
    prev_goals_conceded = g["goals_conceded"].shift(1)
    
    # Calculate rolling stats
    long_df["form_last_5"] = prev_result.groupby(long_df["team"]).rolling(window=5, min_periods=5).mean().reset_index(level=0, drop=True)
    long_df["form_last_10"] = prev_result.groupby(long_df["team"]).rolling(window=10, min_periods=10).mean().reset_index(level=0, drop=True)
    
    long_df["goals_scored_10"] = prev_goals_scored.groupby(long_df["team"]).rolling(window=10, min_periods=10).mean().reset_index(level=0, drop=True)
    long_df["goals_conceded_10"] = prev_goals_conceded.groupby(long_df["team"]).rolling(window=10, min_periods=10).mean().reset_index(level=0, drop=True)
    
    # Goal difference (goals_scored - goals_conceded)
    goal_diff_series = long_df["goals_scored"] - long_df["goals_conceded"]
    prev_goal_diff = goal_diff_series.groupby(long_df["team"]).shift(1)
    long_df["goal_diff_10"] = prev_goal_diff.groupby(long_df["team"]).rolling(window=10, min_periods=10).mean().reset_index(level=0, drop=True)
    
    # win_rate_competitive: mean result_value of last 15 matches where competition_weight >= 2.0
    # NaN if < 5 competitive matches.
    comp_df = long_df[long_df["competition_weight"] >= 2.0].copy()
    comp_df = comp_df.sort_values(by=["team", "date"])
    
    comp_shifted = comp_df.groupby("team")["result_value"].shift(1)
    comp_rolling = comp_shifted.groupby(comp_df["team"]).rolling(window=15, min_periods=5).mean().reset_index(level=0, drop=True)
    comp_df["win_rate_competitive"] = comp_rolling
    
    # Merge back to long_df matching the original indices
    long_df["win_rate_competitive"] = comp_df["win_rate_competitive"]
    # Forward fill the competitive win rate within each team to apply to friendlies played later
    long_df["win_rate_competitive"] = long_df.groupby("team")["win_rate_competitive"].ffill()
    
    return long_df


def main():
    # 1. Load clean_matches.csv
    clean_matches_path = os.path.join("backend", "data", "processed", "clean_matches.csv")
    print(f"Loading clean matches from: {clean_matches_path}")
    if not os.path.exists(clean_matches_path):
        print(f"Error: {clean_matches_path} does not exist. Please run 01_data_cleaner.py first.")
        return
        
    matches_df = pd.read_csv(clean_matches_path)
    
    # Compute rolling stats
    print("Computing rolling stats...")
    stats_df = compute_rolling_stats(matches_df)
    
    # 6. Print null count summary
    print("\n=== Null Count Summary ===")
    print(stats_df.isnull().sum())
    
    # 7. Print a sample: show Brazil's last 10 rows
    print("\n=== Brazil Sample (Last 10 Matches) ===")
    brazil_df = stats_df[stats_df["team"] == "Brazil"].tail(10)
    cols_to_print = [
        "date", "opponent", "goals_scored", "goals_conceded", "result_value",
        "form_last_5", "form_last_10", "goals_scored_10", "goals_conceded_10",
        "goal_diff_10", "win_rate_competitive"
    ]
    print(brazil_df[cols_to_print].to_string(index=False))
    
    # 8. Save to backend/data/processed/team_rolling_stats.csv
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, "team_rolling_stats.csv")
    stats_df.to_csv(out_path, index=False)
    print(f"\nSaved rolling stats to: {out_path}")


if __name__ == "__main__":
    main()

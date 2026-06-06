import os
import sys
import pandas as pd

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def build_match_features() -> pd.DataFrame:
    """
    Builds the match features dataset by merging clean matches with pre-match rolling team stats.
    Computes team-level difference features and target outcomes.
    """
    # 1. Load clean_matches.csv
    clean_matches_path = os.path.join("backend", "data", "processed", "clean_matches.csv")
    if not os.path.exists(clean_matches_path):
        raise FileNotFoundError(f"Clean matches not found at {clean_matches_path}")
    clean_matches = pd.read_csv(clean_matches_path)
    
    # 2. Load team_stats_complete.csv
    team_stats_path = os.path.join("backend", "data", "processed", "team_stats_complete.csv")
    if not os.path.exists(team_stats_path):
        raise FileNotFoundError(f"Team stats complete not found at {team_stats_path}")
    team_stats = pd.read_csv(team_stats_path)
    
    # 3. Load rolling_elo.csv
    rolling_elo_path = os.path.join("backend", "data", "processed", "rolling_elo.csv")
    if not os.path.exists(rolling_elo_path):
        raise FileNotFoundError(f"Rolling Elo not found at {rolling_elo_path}")
    rolling_elo = pd.read_csv(rolling_elo_path)
    
    # Standardize date columns to datetime objects for accurate joins
    clean_matches["date"] = pd.to_datetime(clean_matches["date"])
    team_stats["date"] = pd.to_datetime(team_stats["date"])
    rolling_elo["date"] = pd.to_datetime(rolling_elo["date"])
    
    # Merge matches with rolling_elo on ['date', 'home_team', 'away_team']
    # to obtain home_elo_before and away_elo_before
    df = pd.merge(
        clean_matches,
        rolling_elo[["date", "home_team", "away_team", "home_elo_before", "away_elo_before"]],
        on=["date", "home_team", "away_team"],
        how="left"
    )
    
    # Join on (home_team, date) to retrieve the home team's pre-match statistics
    home_cols = {
        "form_last_5": "home_form_last_5",
        "form_last_10": "home_form_last_10",
        "goals_scored_10": "home_goals_scored_10",
        "goals_conceded_10": "home_goals_conceded_10",
        "goal_diff_10": "home_goal_diff_10",
        "win_rate_competitive": "home_win_rate_competitive",
        "fifa_rank": "home_fifa_rank"
    }
    home_stats = team_stats.rename(columns={"team": "home_team"}).rename(columns=home_cols)
    home_keep_cols = ["date", "home_team"] + list(home_cols.values())
    df = pd.merge(
        df,
        home_stats[home_keep_cols],
        on=["date", "home_team"],
        how="left"
    )
    
    # Join on (away_team, date) to retrieve the away team's pre-match statistics
    away_cols = {
        "form_last_5": "away_form_last_5",
        "form_last_10": "away_form_last_10",
        "goals_scored_10": "away_goals_scored_10",
        "goals_conceded_10": "away_goals_conceded_10",
        "goal_diff_10": "away_goal_diff_10",
        "win_rate_competitive": "away_win_rate_competitive",
        "fifa_rank": "away_fifa_rank"
    }
    away_stats = team_stats.rename(columns={"team": "away_team"}).rename(columns=away_cols)
    away_keep_cols = ["date", "away_team"] + list(away_cols.values())
    df = pd.merge(
        df,
        away_stats[away_keep_cols],
        on=["date", "away_team"],
        how="left"
    )
    
    # 4. Compute difference features (Team_A = home, Team_B = away)
    df["elo_diff"] = df["home_elo_before"] - df["away_elo_before"]
    
    # rank_diff is inverted: lower rank value is stronger, so positive diff means home team is stronger
    df["rank_diff"] = df["away_fifa_rank"] - df["home_fifa_rank"]
    
    df["form5_diff"] = df["home_form_last_5"] - df["away_form_last_5"]
    df["form10_diff"] = df["home_form_last_10"] - df["away_form_last_10"]
    df["attack_diff"] = df["home_goals_scored_10"] - df["away_goals_scored_10"]
    
    # defense_diff is inverted: lower goals conceded is better defense, so positive means home team is better
    df["defense_diff"] = df["away_goals_conceded_10"] - df["home_goals_conceded_10"]
    
    df["goal_diff_diff"] = df["home_goal_diff_10"] - df["away_goal_diff_10"]
    df["competitive_form_diff"] = df["home_win_rate_competitive"] - df["away_win_rate_competitive"]
    
    # 5. Add target label: 0 = home win, 1 = draw, 2 = away win
    def determine_target(row):
        if row["home_score"] > row["away_score"]:
            return 0
        elif row["home_score"] == row["away_score"]:
            return 1
        else:
            return 2
            
    df["target"] = df.apply(determine_target, axis=1)
    
    # 6. Organize metadata, features, and target labels
    metadata_cols = ["date", "home_team", "away_team"]
    feature_cols = [
        "elo_diff",
        "rank_diff",
        "form5_diff",
        "form10_diff",
        "attack_diff",
        "defense_diff",
        "goal_diff_diff",
        "competitive_form_diff",
        "competition_weight"
    ]
    all_keep_cols = metadata_cols + feature_cols + ["target"]
    df = df[all_keep_cols]
    
    # 7. Drop rows where ANY feature column has NaN (removes early matches with missing rolling history)
    initial_shape = df.shape
    df = df.dropna(subset=feature_cols).reset_index(drop=True)
    final_shape = df.shape
    
    # Convert date back to string format for easier readability/saving
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    
    # 8. Print information
    print("=== Match Feature Dataset Generation ===")
    print(f"Initial shape: {initial_shape}")
    print(f"Final shape (after dropping NaNs): {final_shape}")
    print(f"Dropped rows: {initial_shape[0] - final_shape[0]}")
    
    print("\nClass distribution (target counts):")
    class_counts = df["target"].value_counts().sort_index()
    total_samples = len(df)
    for label, count in class_counts.items():
        outcome = "Home Win (0)" if label == 0 else "Draw (1)" if label == 1 else "Away Win (2)"
        pct = (count / total_samples) * 100 if total_samples > 0 else 0
        print(f"  {outcome}: {count} ({pct:.2f}%)")
        
    print("\nNull check in final dataset:")
    nulls = df.isnull().sum()
    for col, null_count in nulls.items():
        print(f"  {col}: {null_count}")
        
    # 9. Save to match_features.csv
    output_path = os.path.join("backend", "data", "processed", "match_features.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nSaved feature dataset to: {output_path}")
    
    return df


def main():
    build_match_features()


if __name__ == "__main__":
    main()

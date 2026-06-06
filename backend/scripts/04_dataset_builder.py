import os
import sys
import pandas as pd
import numpy as np
import json

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


def apply_dataset_doubling(features_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Applies dataset doubling for perfect symmetry on neutral grounds.
    For each match, creates a mirrored row where the team roles (home/away) are swapped,
    difference features are negated, and outcome targets are flipped.
    """
    # 1. Load match_features.csv if features_df is not provided
    if features_df is None:
        features_df_path = os.path.join("backend", "data", "processed", "match_features.csv")
        if not os.path.exists(features_df_path):
            raise FileNotFoundError(f"Match features not found at {features_df_path}")
        features_df = pd.read_csv(features_df_path)
        
    # 2. For each row, create a SECOND row where:
    # — All difference features are NEGATED (multiply by -1):
    #   elo_diff, rank_diff, form5_diff, form10_diff, attack_diff, defense_diff,
    #   goal_diff_diff, competitive_form_diff all become their negatives.
    # — competition_weight stays the same (match property, not team property).
    # — Target label is FLIPPED (0 -> 2, 2 -> 0, 1 -> 1).
    # — Metadata: swap home_team and away_team.
    doubled_df = features_df.copy()
    
    diff_cols = [
        "elo_diff",
        "rank_diff",
        "form5_diff",
        "form10_diff",
        "attack_diff",
        "defense_diff",
        "goal_diff_diff",
        "competitive_form_diff"
    ]
    doubled_df[diff_cols] = doubled_df[diff_cols] * -1.0
    
    # Target label flipping map: 0 (home win) -> 2 (away win), 2 -> 0, 1 -> 1
    target_map = {0: 2, 1: 1, 2: 0}
    doubled_df["target"] = doubled_df["target"].map(target_map)
    
    # Metadata swap
    temp_home = doubled_df["home_team"].copy()
    doubled_df["home_team"] = doubled_df["away_team"]
    doubled_df["away_team"] = temp_home
    
    # 3. Concatenate original rows + doubled rows -> final training dataset
    final_df = pd.concat([features_df, doubled_df], ignore_index=True)
    
    # 4. Shuffle the dataset (using random_state=42 for reproducibility)
    # Shuffle WITHIN dates (time periods) to preserve chronological splitting downstream.
    # We standardise date column to datetime, generate random shuffle keys, sort by date
    # and shuffle key, then convert date back to string.
    final_df["date"] = pd.to_datetime(final_df["date"])
    
    rng = np.random.default_rng(42)
    final_df["shuffle_key"] = rng.random(len(final_df))
    
    final_df = final_df.sort_values(by=["date", "shuffle_key"]).drop(columns=["shuffle_key"]).reset_index(drop=True)
    final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")
    
    # 5. Print statistics
    print("\n=== Dataset Doubling & Symmetry Check ===")
    print(f"Shape before doubling: {features_df.shape}")
    print(f"Shape after doubling: {final_df.shape}")
    
    print("\nClass distribution in doubled dataset:")
    class_counts = final_df["target"].value_counts().sort_index()
    total_samples = len(final_df)
    for label, count in class_counts.items():
        outcome = "Home Win (0)" if label == 0 else "Draw (1)" if label == 1 else "Away Win (2)"
        pct = (count / total_samples) * 100 if total_samples > 0 else 0
        print(f"  {outcome}: {count} ({pct:.2f}%)")
        
    home_wins = class_counts.get(0, 0)
    away_wins = class_counts.get(2, 0)
    symmetry_verified = (home_wins == away_wins)
    print(f"\nSymmetry Verification: Label 0 count ({home_wins}) == Label 2 count ({away_wins}) -> {symmetry_verified}")
    if not symmetry_verified:
        print("WARNING: Dataset is NOT symmetric!")
        
    # 6. Save to backend/data/processed/training_data.csv
    output_path = os.path.join("backend", "data", "processed", "training_data.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"Saved training dataset to: {output_path}")
    
    return final_df


def create_train_test_split(training_data_df: pd.DataFrame = None) -> tuple:
    """
    Performs a chronological split of the doubled training dataset.
    Train: everything before 2022-01-01.
    Test: 2022-01-01 to 2026-06-11 (WC 2026 start date).
    Saves split matrices (X_train, X_test, y_train, y_test) and feature names list.
    """
    # 1. Load training_data.csv if training_data_df is not provided
    if training_data_df is None:
        training_data_path = os.path.join("backend", "data", "processed", "training_data.csv")
        if not os.path.exists(training_data_path):
            raise FileNotFoundError(f"Training data not found at {training_data_path}")
        training_data_df = pd.read_csv(training_data_path)
        
    df = training_data_df.copy()
    
    # 2. Ensure sorted chronologically by date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date").reset_index(drop=True)
    
    # Rename target to label for down-stream modeling convenience
    if "target" in df.columns:
        df = df.rename(columns={"target": "label"})
        
    # 3. Create the split
    train_mask = df["date"] < pd.to_datetime("2022-01-01")
    test_mask = (df["date"] >= pd.to_datetime("2022-01-01")) & (df["date"] < pd.to_datetime("2026-06-11"))
    
    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()
    
    # 4. Extract features (X) and target (y)
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
    target_col = "label"
    
    X_train = train_df[feature_cols]
    y_train = train_df[[target_col]]
    
    X_test = test_df[feature_cols]
    y_test = test_df[[target_col]]
    
    # Convert dates to string representation for display
    train_min_date = train_df["date"].min().strftime("%Y-%m-%d")
    train_max_date = train_df["date"].max().strftime("%Y-%m-%d")
    test_min_date = test_df["date"].min().strftime("%Y-%m-%d")
    test_max_date = test_df["date"].max().strftime("%Y-%m-%d")
    
    # 5. Print Split Stats
    print("\n=== Time-Based Train/Test Split ===")
    print(f"Train size: {len(X_train)} rows, date range: {train_min_date} to {train_max_date}")
    print(f"Test size: {len(X_test)} rows, date range: {test_min_date} to {test_max_date}")
    
    print("\nClass distribution in Train set:")
    train_total = len(y_train)
    train_counts = y_train["label"].value_counts().sort_index()
    for label, count in train_counts.items():
        outcome = "Home Win (0)" if label == 0 else "Draw (1)" if label == 1 else "Away Win (2)"
        pct = (count / train_total) * 100 if train_total > 0 else 0
        print(f"  {outcome}: {count} ({pct:.2f}%)")
        
    print("\nClass distribution in Test set:")
    test_total = len(y_test)
    test_counts = y_test["label"].value_counts().sort_index()
    for label, count in test_counts.items():
        outcome = "Home Win (0)" if label == 0 else "Draw (1)" if label == 1 else "Away Win (2)"
        pct = (count / test_total) * 100 if test_total > 0 else 0
        print(f"  {outcome}: {count} ({pct:.2f}%)")
        
    # Date overlap verification
    train_dates = set(train_df["date"])
    test_dates = set(test_df["date"])
    overlap = train_dates.intersection(test_dates)
    print(f"\nDate overlap check: {len(overlap)} overlapping dates (expect 0)")
    
    # 6. Save split datasets to CSV
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    X_train.to_csv(os.path.join(processed_dir, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(processed_dir, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(processed_dir, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(processed_dir, "y_test.csv"), index=False)
    print(f"\nSaved X_train, X_test, y_train, y_test to: {processed_dir}")
    
    # 7. Save the feature column names list to backend/data/processed/feature_names.json
    feature_names_path = os.path.join(processed_dir, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(feature_cols, f, indent=4)
    print(f"Saved feature name configurations to: {feature_names_path}")
    
    return X_train, X_test, y_train, y_test


def main():
    features_df = build_match_features()
    training_data_df = apply_dataset_doubling(features_df)
    create_train_test_split(training_data_df)


if __name__ == "__main__":
    main()

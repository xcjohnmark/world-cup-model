import os
import sys
import pandas as pd
import json

# Add project root to python path to import team_standardizer
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


def inspect_results():
    """
    STEP 1: Inspect results.csv
    Loads, displays and analyzes basic properties of the raw results dataset.
    """
    print("=" * 80)
    print("STEP 1: Inspect results.csv")
    print("=" * 80)

    # 1. Load backend/data/raw/results.csv into a DataFrame
    csv_path = os.path.join("backend", "data", "raw", "results.csv")
    print(f"Loading data from: {csv_path}\n")
    df = pd.read_csv(csv_path)

    # Convert date column to datetime for inspection
    df["date_dt"] = pd.to_datetime(df["date"])

    # 2. Print: shape, column names, dtypes, first 5 rows
    print("-" * 50)
    print("2. Shape of the DataFrame:")
    print(df.shape)
    print("\nColumn names:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())
    print("-" * 50)

    # 3. Print: date range (min and max date)
    print("3. Date range (Min and Max date):")
    min_date = df["date"].min()
    max_date = df["date"].max()
    print(f"Min Date: {min_date}")
    print(f"Max Date: {max_date}")
    print("-" * 50)

    # 4. Print: null counts per column
    print("4. Null counts per column:")
    print(df.isnull().sum())
    print("-" * 50)

    # 5. Print: top 20 tournament types by count
    print("5. Top 20 tournament types by count:")
    print(df["tournament"].value_counts().head(20))
    print("-" * 50)

    # 6. Print: count of matches where neutral == True vs False
    print("6. Count of matches where neutral is True vs False:")
    print(df["neutral"].value_counts())
    print("-" * 50)

    # 7. Print: count of matches per decade (1870s, 1880s, ... 2020s)
    print("7. Count of matches per decade:")
    df["decade"] = (df["date_dt"].dt.year // 10) * 10
    decade_counts = df["decade"].value_counts().sort_index()
    for dec, count in decade_counts.items():
        print(f"{dec}s: {count}")
    print("-" * 50)

    # 8. Print: count of matches where home_score IS null (72 rows expected)
    print("8. Count of matches where home_score is null (expected 72):")
    null_home_score_count = df["home_score"].isnull().sum()
    print(f"Count: {null_home_score_count}")
    print("-" * 50)

    # 9. Print: all matches where date >= 2026-06-01 (these are WC 2026 group stage fixtures)
    print("9. Matches where date >= 2026-06-01 (World Cup 2026 fixtures):")
    wc_matches = df[df["date"] >= "2026-06-01"]
    print(wc_matches.to_string())
    print("-" * 50)

    # 10. From the 2026 WC matches, extract and print the list of unique teams
    print("10. Unique teams in WC 2026 matches (date >= 2026-06-01):")
    unique_teams = pd.concat([wc_matches["home_team"], wc_matches["away_team"]]).unique()
    unique_teams_sorted = sorted(unique_teams)
    print(f"Total Unique Teams: {len(unique_teams_sorted)}")
    for team in unique_teams_sorted:
        print(f" - {team}")
    print("-" * 50)


def inspect_strength_datasets():
    """
    STEP 2: Inspect strength datasets
    Loads, displays and analyzes elo-rating.csv and fifa-ranking.csv.
    """
    print("\n" + "=" * 80)
    print("STEP 2: Inspect strength datasets")
    print("=" * 80)

    # --- elo-rating.csv ---
    print("--- ELO RATING (elo-rating.csv) ---")
    elo_path = os.path.join("backend", "data", "raw", "elo-rating.csv")
    print(f"Loading data from: {elo_path}\n")
    df_elo = pd.read_csv(elo_path)

    # 1. Load and print: shape, columns, top 10 rows (rank, team, rating)
    print(f"Shape: {df_elo.shape}")
    print(f"Columns: {df_elo.columns.tolist()}")
    print("\nTop 10 Elo Teams (rank, team, rating):")
    print(df_elo[["rank", "team", "rating"]].head(10))

    # 2. Print total team count
    print(f"\nTotal team count in Elo dataset: {df_elo['team'].nunique()}")

    # 3. Note
    print("\n[NOTE] This file is for validation only. We will compute Elo dynamically.")
    print("-" * 50)

    # --- fifa-ranking.csv ---
    print("\n--- FIFA RANKINGS (fifa-ranking.csv) ---")
    fifa_path = os.path.join("backend", "data", "raw", "fifa-ranking.csv")
    print(f"Loading data from: {fifa_path}\n")
    df_fifa = pd.read_csv(fifa_path)

    # 1. Load and print: shape, columns, date range of rank_date
    print(f"Shape: {df_fifa.shape}")
    print(f"Columns: {df_fifa.columns.tolist()}")
    df_fifa["rank_date_dt"] = pd.to_datetime(df_fifa["rank_date"])
    min_date = df_fifa["rank_date"].min()
    max_date = df_fifa["rank_date"].max()
    print(f"Date range of rank_date: {min_date} to {max_date}")

    # 2. Print unique dates available (how many distinct ranking dates)
    unique_dates = df_fifa["rank_date"].nunique()
    print(f"Number of distinct ranking dates: {unique_dates}")

    # 3. Print count of unique teams
    unique_teams_fifa = df_fifa["country_full"].nunique()
    print(f"Number of unique teams: {unique_teams_fifa}")

    # 4. Print the top 10 teams in the most recent ranking available
    most_recent_date = df_fifa["rank_date_dt"].max()
    df_recent = df_fifa[df_fifa["rank_date_dt"] == most_recent_date]
    print(f"\nTop 10 teams in the most recent ranking ({most_recent_date.strftime('%Y-%m-%d')}):")
    print(df_recent.sort_values("rank")[["rank", "country_full", "total_points"]].head(10))

    # 5. Print null counts
    print("\nNull counts per column:")
    print(df_fifa.isnull().sum())
    print("-" * 50)


def inspect_supporting_datasets():
    """
    STEP 3: Inspect supporting datasets
    Loads, displays and analyzes shootouts.csv, goalscorers.csv, and former-names.csv.
    """
    print("\n" + "=" * 80)
    print("STEP 3: Inspect supporting datasets")
    print("=" * 80)

    # --- shootouts.csv ---
    print("--- PENALTY SHOOTOUTS (shootouts.csv) ---")
    shootouts_path = os.path.join("backend", "data", "raw", "shootouts.csv")
    print(f"Loading data from: {shootouts_path}\n")
    df_shootouts = pd.read_csv(shootouts_path)

    # 1. Load and print: shape, columns, first 5 rows, date range
    print(f"Shape: {df_shootouts.shape}")
    print(f"Columns: {df_shootouts.columns.tolist()}")
    print("\nFirst 5 rows:")
    print(df_shootouts.head())
    min_date = df_shootouts["date"].min()
    max_date = df_shootouts["date"].max()
    print(f"\nDate Range: {min_date} to {max_date}")

    # 2. Print: top 10 teams by total shootouts won (winner column)
    print("\nTop 10 teams by total shootouts won:")
    print(df_shootouts["winner"].value_counts().head(10))

    # 3. Print: count of null values in first_shooter
    print(f"\nCount of null values in first_shooter: {df_shootouts['first_shooter'].isnull().sum()}")

    # 4. Note
    print("\n[NOTE] This data will be used to compute each team's historical penalty win rate.")
    print("-" * 50)

    # --- goalscorers.csv ---
    print("\n--- GOALSCORERS (goalscorers.csv) ---")
    goalscorers_path = os.path.join("backend", "data", "raw", "goalscorers.csv")
    print(f"Loading data from: {goalscorers_path}\n")
    df_goalscorers = pd.read_csv(goalscorers_path)

    # 1. Load and print: shape, columns, first 5 rows
    print(f"Shape: {df_goalscorers.shape}")
    print(f"Columns: {df_goalscorers.columns.tolist()}")
    print("\nFirst 5 rows:")
    print(df_goalscorers.head())

    # 2. Print: total goals, penalty goals, own goals
    total_goals = len(df_goalscorers)
    penalty_goals = (df_goalscorers["penalty"] == True).sum()
    own_goals = (df_goalscorers["own_goal"] == True).sum()
    print(f"\nTotal Goals: {total_goals}")
    print(f"Penalty Goals: {penalty_goals}")
    print(f"Own Goals: {own_goals}")

    # 3. Note
    print("\n[NOTE] This file will NOT be used as a direct feature — it's supplementary context only.")
    print("-" * 50)

    # --- former-names.csv ---
    print("\n--- FORMER NAMES (former-names.csv) ---")
    former_names_path = os.path.join("backend", "data", "raw", "former-names.csv")
    print(f"Loading data from: {former_names_path}\n")
    df_former = pd.read_csv(former_names_path)

    # 1. Load and print the entire file (only 36 rows)
    print(df_former.to_string(index=False))

    # 2. Explain
    print("\n[EXPLANATION] This maps old country names to current names (e.g. 'West Germany' -> 'Germany').")
    print("-" * 50)


def clean_data():
    """
    STEP 4: Clean and Standardize Datasets
    Applies the TeamStandardizer to results.csv, fifa-ranking.csv, and wc_2026_groups.json.
    Saves results to backend/data/cleaned/.
    """
    print("\n" + "=" * 80)
    print("STEP 4: Clean and Standardize Datasets")
    print("=" * 80)

    # Initialize standardizer
    standardizer = TeamStandardizer()

    # Create cleaned data directory if it doesn't exist
    cleaned_dir = os.path.join("backend", "data", "cleaned")
    os.makedirs(cleaned_dir, exist_ok=True)

    # --- 1. Clean results.csv ---
    raw_results_path = os.path.join("backend", "data", "raw", "results.csv")
    cleaned_results_path = os.path.join(cleaned_dir, "results.csv")
    print(f"Cleaning {raw_results_path}...")
    df_results = pd.read_csv(raw_results_path)

    # Track normalization counts
    orig_home = df_results["home_team"].copy()
    orig_away = df_results["away_team"].copy()

    df_results["home_team"] = df_results["home_team"].apply(standardizer.standardize)
    df_results["away_team"] = df_results["away_team"].apply(standardizer.standardize)

    home_changes = (orig_home != df_results["home_team"]).sum()
    away_changes = (orig_away != df_results["away_team"]).sum()
    print(f"  Standardized {home_changes} home teams and {away_changes} away teams.")
    df_results.to_csv(cleaned_results_path, index=False)
    print(f"  Saved cleaned results to: {cleaned_results_path}")

    # --- 2. Clean fifa-ranking.csv ---
    raw_fifa_path = os.path.join("backend", "data", "raw", "fifa-ranking.csv")
    cleaned_fifa_path = os.path.join(cleaned_dir, "fifa-ranking.csv")
    print(f"\nCleaning {raw_fifa_path}...")
    df_fifa = pd.read_csv(raw_fifa_path)

    orig_country = df_fifa["country_full"].copy()
    df_fifa["country_full"] = df_fifa["country_full"].apply(standardizer.standardize)

    fifa_changes = (orig_country != df_fifa["country_full"]).sum()
    print(f"  Standardized {fifa_changes} FIFA team names.")
    df_fifa.to_csv(cleaned_fifa_path, index=False)
    print(f"  Saved cleaned FIFA rankings to: {cleaned_fifa_path}")

    # --- 3. Clean wc_2026_groups.json ---
    raw_groups_path = os.path.join("backend", "data", "raw", "wc_2026_groups.json")
    cleaned_groups_path = os.path.join(cleaned_dir, "wc_2026_groups.json")
    print(f"\nCleaning {raw_groups_path}...")

    if os.path.exists(raw_groups_path):
        with open(raw_groups_path, "r", encoding="utf-8") as f:
            groups_data = json.load(f)

        # Clean group stage teams
        groups = groups_data.get("groups", {})
        cleaned_groups = {}
        group_changes = 0
        for grp, teams in groups.items():
            cleaned_teams = []
            for team in teams:
                std_team = standardizer.standardize(team)
                if std_team != team:
                    group_changes += 1
                cleaned_teams.append(std_team)
            cleaned_groups[grp] = cleaned_teams
        groups_data["groups"] = cleaned_groups
        print(f"  Standardized {group_changes} team names in group assignments.")

        with open(cleaned_groups_path, "w", encoding="utf-8") as f:
            json.dump(groups_data, f, indent=2)
        print(f"  Saved cleaned group assignments to: {cleaned_groups_path}")
    else:
        print("  wc_2026_groups.json not found in raw data.")

    print("-" * 50)


if __name__ == "__main__":
    inspect_results()
    inspect_strength_datasets()
    inspect_supporting_datasets()
    clean_data()

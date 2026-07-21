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


def clean_results():
    """
    STEP 5: Clean and Process Match Results for Training and Fixtures
    1. Load backend/data/raw/results.csv
    2. Parse date column to datetime
    3. Apply standardize_name() to both home_team and away_team columns
    4. Remove rows where home_score OR away_score is null
       - EXCEPTION: Keep rows where date >= 2026-06-11 (WC 2026 fixtures)
       - Store WC 2026 fixtures separately as wc2026_fixtures DataFrame
    5. Remove exact duplicate rows (same date + same teams)
    6. Filter to matches on or after 2014-01-01 only (for the training set)
    7. Sort chronologically by date
    8. Add a competition_weight column
    9. Print final stats
    10. Save to backend/data/processed/clean_matches.csv
    11. Save wc2026_fixtures to backend/data/processed/wc2026_fixtures.csv
    """
    print("\n" + "=" * 80)
    print("STEP 5: Clean and Process Match Results")
    print("=" * 80)

    # Initialize standardizer
    standardizer = TeamStandardizer()

    # 1. Load backend/data/raw/results.csv
    csv_path = os.path.join("backend", "data", "raw", "results.csv")
    print(f"Loading raw results from: {csv_path}")
    df = pd.read_csv(csv_path)

    # 2. Parse date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # 3. Apply standardize_name() to both home_team and away_team columns
    def standardize_name(name):
        return standardizer.standardize(name)

    print("Standardizing team names...")
    df["home_team"] = df["home_team"].apply(standardize_name)
    df["away_team"] = df["away_team"].apply(standardize_name)

    # 4. Remove rows where home_score OR away_score is null
    # EXCEPTION: Keep rows where date >= 2026-06-11 (WC 2026 fixtures)
    cutoff_date = pd.to_datetime("2026-06-27")
    is_wc2026 = df["date"] >= cutoff_date
    has_score = df["home_score"].notnull() & df["away_score"].notnull()

    df_filtered = df[has_score | is_wc2026].copy()

    # 5. Remove exact duplicate rows (same date + same teams)
    print("Removing exact duplicates (same date + same teams)...")
    df_filtered = df_filtered.drop_duplicates(subset=["date", "home_team", "away_team"])

    # 6. Filter to matches on or after 2014-01-01 only (for the training set)
    # The WC 2026 fixtures are all in 2026, which is after 2014-01-01.
    start_date = pd.to_datetime("2014-01-01")
    df_filtered = df_filtered[df_filtered["date"] >= start_date]

    # 7. Sort chronologically by date — this is MANDATORY
    print("Sorting chronologically by date...")
    df_filtered = df_filtered.sort_values(by="date").reset_index(drop=True)

    # 8. Add a competition_weight column
    print("Mapping competition weights...")
    weight_map = {
        "FIFA World Cup": 3.0,
        "FIFA World Cup qualification": 2.0,
        "UEFA Euro": 2.5,
        "Copa América": 2.5,
        "Copa Am\uFFFDrica": 2.5,
        "African Cup of Nations": 2.0,
        "AFC Asian Cup": 2.0,
        "Gold Cup": 1.5,
        "CONCACAF Nations League": 1.5,
        "UEFA Nations League": 1.5,
        "UEFA Euro qualification": 1.5,
        "African Cup of Nations qualification": 1.5,
        "Friendly": 0.5
    }
    df_filtered["competition_weight"] = df_filtered["tournament"].map(weight_map).fillna(1.0)

    # Split into training matches and future fixtures
    wc2026_fixtures = df_filtered[df_filtered["date"] >= cutoff_date].copy()
    wc2026_fixtures["home_score"] = float("nan")
    wc2026_fixtures["away_score"] = float("nan")
    clean_matches = df_filtered[df_filtered["date"] < cutoff_date].copy()

    # 9. Print final stats: total rows, date range, null counts, competition weight distribution
    print("\n--- FINAL STATS for clean_matches (Training Set) ---")
    print(f"Total rows: {len(clean_matches)}")
    if not clean_matches.empty:
        print(f"Date range: {clean_matches['date'].min().strftime('%Y-%m-%d')} to {clean_matches['date'].max().strftime('%Y-%m-%d')}")
    else:
        print("Date range: Empty")
    print("\nNull counts:")
    print(clean_matches.isnull().sum())
    print("\nCompetition weight distribution:")
    print(clean_matches["competition_weight"].value_counts())

    print("\n--- FINAL STATS for wc2026_fixtures (Test Set) ---")
    print(f"Total rows: {len(wc2026_fixtures)}")
    if not wc2026_fixtures.empty:
        print(f"Date range: {wc2026_fixtures['date'].min().strftime('%Y-%m-%d')} to {wc2026_fixtures['date'].max().strftime('%Y-%m-%d')}")
    else:
        print("Date range: Empty")
    print("\nNull counts:")
    print(wc2026_fixtures.isnull().sum())

    # Save to directory
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # 10. Save to backend/data/processed/clean_matches.csv
    clean_matches_path = os.path.join(processed_dir, "clean_matches.csv")
    clean_matches.to_csv(clean_matches_path, index=False)
    print(f"\nSaved clean matches to: {clean_matches_path}")

    # 11. Save wc2026_fixtures to backend/data/processed/wc2026_fixtures.csv
    wc2026_fixtures_path = os.path.join(processed_dir, "wc2026_fixtures.csv")
    wc2026_fixtures.to_csv(wc2026_fixtures_path, index=False)
    print(f"Saved WC 2026 fixtures to: {wc2026_fixtures_path}")
    print("-" * 50)


def clean_fifa_rankings():
    """
    STEP 6: Clean and Process FIFA Rankings
    1. Load backend/data/raw/fifa-ranking.csv
    2. Apply standardize_name() to country_full column, rename it to team
    3. Parse rank_date to datetime
    4. Keep only: team, rank, rank_date
    5. Handle nulls in rank (9 null rows) — drop these rows
    6. Sort by rank_date ascending, then team
    7. For each team, ensure rankings are monotonically ordered by date (remove any out-of-order entries)
    8. Save to backend/data/processed/clean_rankings.csv
    """
    print("\n" + "=" * 80)
    print("STEP 6: Clean and Process FIFA Rankings")
    print("=" * 80)

    # Initialize standardizer
    standardizer = TeamStandardizer()

    # 1. Load backend/data/raw/fifa-ranking.csv
    csv_path = os.path.join("backend", "data", "raw", "fifa-ranking.csv")
    print(f"Loading raw FIFA rankings from: {csv_path}")
    df = pd.read_csv(csv_path)

    # 2. Apply standardize_name() to country_full column, rename it to team
    def standardize_name(name):
        return standardizer.standardize(name)

    print("Standardizing team names in FIFA rankings...")
    df["team"] = df["country_full"].apply(standardize_name)

    # 3. Parse rank_date to datetime
    df["rank_date"] = pd.to_datetime(df["rank_date"])

    # 4. Keep only: team, rank, rank_date
    df = df[["team", "rank", "rank_date"]]

    # 5. Handle nulls in rank (9 null rows) — drop these rows
    df = df.dropna(subset=["rank"])

    # 6. Sort by rank_date ascending, then team
    df = df.sort_values(by=["rank_date", "team"]).reset_index(drop=True)

    # 7. For each team, ensure rankings are monotonically ordered by date (remove any out-of-order entries)
    df = df.drop_duplicates(subset=["team", "rank_date"]).reset_index(drop=True)

    # 9. Print final stats
    print("\n--- FINAL STATS for clean_rankings ---")
    print(f"Total rows after cleaning: {len(df)}")
    if not df.empty:
        print(f"Date range: {df['rank_date'].min().strftime('%Y-%m-%d')} to {df['rank_date'].max().strftime('%Y-%m-%d')}")
        unique_teams = df["team"].nunique()
        print(f"Number of unique teams: {unique_teams}")

        # Top 10 teams in the most recent ranking available
        most_recent_date = df["rank_date"].max()
        df_recent = df[df["rank_date"] == most_recent_date]
        print(f"\nTop 10 teams in the most recent ranking ({most_recent_date.strftime('%Y-%m-%d')}):")
        print(df_recent.sort_values("rank")[["rank", "team"]].head(10).to_string(index=False))
    else:
        print("Date range: Empty")

    # 10. Save to backend/data/processed/clean_rankings.csv
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    clean_rankings_path = os.path.join(processed_dir, "clean_rankings.csv")
    df.to_csv(clean_rankings_path, index=False)
    print(f"\nSaved clean FIFA rankings to: {clean_rankings_path}")
    print("-" * 50)


# Cached data dictionary for get_fifa_rank optimization
_fifa_rank_cache = {}

def get_fifa_rank(team: str, match_date) -> float:
    """
    Finds the most recent FIFA ranking for team on or before match_date.
    Returns the ranking value (int), or NaN if no ranking exists before that date.
    This function will be called during feature engineering.
    """
    global _fifa_rank_cache
    
    # Lazy load and build the cache
    if not _fifa_rank_cache:
        path = os.path.join("backend", "data", "processed", "clean_rankings.csv")
        if os.path.exists(path):
            df_temp = pd.read_csv(path)
            df_temp["rank_date"] = pd.to_datetime(df_temp["rank_date"])
            # Ensure sorting
            df_temp = df_temp.sort_values(by="rank_date")
            for t, group in df_temp.groupby("team"):
                _fifa_rank_cache[t] = (group["rank_date"].tolist(), group["rank"].tolist())
                
    if team not in _fifa_rank_cache:
        return float('nan')
        
    dates, ranks = _fifa_rank_cache[team]
    match_dt = pd.to_datetime(match_date)
    
    import bisect
    idx = bisect.bisect_right(dates, match_dt)
    if idx == 0:
        return float('nan')
    return int(ranks[idx - 1])


def compute_penalty_win_rates():
    """
    STEP 7: Compute Penalty Win Rates from Shootouts History
    1. Load backend/data/raw/shootouts.csv
    2. Apply standardize_name() to home_team, away_team, and winner columns
    3. Determine participation and winner for both home and away teams
    4. Aggregate by team (total_shootouts, shootouts_won, penalty_win_rate)
    5. Set penalty_win_rate = 0.5 for teams with < 3 shootouts
    6. Print top 10 and bottom 10 teams by penalty win rate (among those with >=3 shootouts)
    7. Save to backend/data/processed/penalty_win_rates.csv
    """
    print("\n" + "=" * 80)
    print("STEP 7: Compute Penalty Win Rates")
    print("=" * 80)

    # Initialize standardizer
    standardizer = TeamStandardizer()

    # 1. Load backend/data/raw/shootouts.csv
    csv_path = os.path.join("backend", "data", "raw", "shootouts.csv")
    print(f"Loading raw shootouts from: {csv_path}")
    df_shootouts = pd.read_csv(csv_path)

    # 2. Apply standardize_name() to home_team, away_team, and winner columns
    def standardize_name(name):
        return standardizer.standardize(name)

    df_shootouts["home_team"] = df_shootouts["home_team"].apply(standardize_name)
    df_shootouts["away_team"] = df_shootouts["away_team"].apply(standardize_name)
    df_shootouts["winner"] = df_shootouts["winner"].apply(standardize_name)

    # 3. For each match in shootouts.csv, determine participation and outcome
    records = []
    for _, row in df_shootouts.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        winner = row["winner"]

        # Home team record
        records.append({"team": home, "won": 1 if winner == home else 0})
        # Away team record
        records.append({"team": away, "won": 1 if winner == away else 0})

    df_records = pd.DataFrame(records)

    # 4. Aggregate by team
    df_agg = df_records.groupby("team").agg(
        total_shootouts=("won", "count"),
        shootouts_won=("won", "sum")
    ).reset_index()
    
    df_agg["penalty_win_rate"] = df_agg["shootouts_won"] / df_agg["total_shootouts"]

    # 5. For teams with fewer than 3 shootouts, set penalty_win_rate = 0.5 (insufficient data -> default)
    df_agg.loc[df_agg["total_shootouts"] < 3, "penalty_win_rate"] = 0.5

    # 6. Print: top 10 and bottom 10 teams by penalty win rate (among those with >=3 shootouts)
    df_eligible = df_agg[df_agg["total_shootouts"] >= 3]
    
    # Sort top 10 descending
    top_10 = df_eligible.sort_values(
        by=["penalty_win_rate", "total_shootouts", "team"], 
        ascending=[False, False, True]
    ).head(10)
    
    # Sort bottom 10 ascending
    bottom_10 = df_eligible.sort_values(
        by=["penalty_win_rate", "total_shootouts", "team"], 
        ascending=[True, False, True]
    ).head(10)

    print("\nTop 10 teams by penalty win rate (among those with >=3 shootouts):")
    print(top_10.to_string(index=False))
    
    print("\nBottom 10 teams by penalty win rate (among those with >=3 shootouts):")
    print(bottom_10.to_string(index=False))

    # 7. Save to backend/data/processed/penalty_win_rates.csv
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, "penalty_win_rates.csv")
    df_agg.to_csv(out_path, index=False)
    print(f"\nSaved penalty win rates to: {out_path}")
    print("-" * 50)


def validate_clean_data():
    """
    STEP 8: Validate Processed Datasets
    1. Load clean_matches.csv and assert integrity
    2. Load wc2026_fixtures.csv and assert integrity
    3. Load clean_rankings.csv and assert integrity
    4. Load penalty_win_rates.csv and assert integrity
    """
    print("\n" + "=" * 80)
    print("STEP 8: Validate Processed Datasets")
    print("=" * 80)

    try:
        processed_dir = os.path.join("backend", "data", "processed")

        # 1. Load clean_matches.csv and assert
        matches_path = os.path.join(processed_dir, "clean_matches.csv")
        print(f"Validating {matches_path}...")
        df_matches = pd.read_csv(matches_path)
        df_matches["date"] = pd.to_datetime(df_matches["date"])

        # No null values in target columns
        cols_to_check = ["date", "home_team", "away_team", "home_score", "away_score", "competition_weight"]
        for col in cols_to_check:
            null_count = df_matches[col].isnull().sum()
            assert null_count == 0, f"clean_matches.csv: Column '{col}' contains {null_count} null value(s)."

        # Sorted chronologically
        is_sorted = df_matches["date"].is_monotonic_increasing
        assert is_sorted, "clean_matches.csv: Matches are not chronologically sorted."

        # All dates are >= 1990-01-01
        min_match_date = df_matches["date"].min()
        assert min_match_date >= pd.to_datetime("1990-01-01"), f"clean_matches.csv: Found date {min_match_date.strftime('%Y-%m-%d')} before 1990-01-01."

        # competition_weight is between 0.5 and 3.0
        min_weight = df_matches["competition_weight"].min()
        max_weight = df_matches["competition_weight"].max()
        assert 0.5 <= min_weight and max_weight <= 3.0, f"clean_matches.csv: competition_weight range [{min_weight}, {max_weight}] is out of bounds [0.5, 3.0]."

        # home_score and away_score are numeric
        assert pd.api.types.is_numeric_dtype(df_matches["home_score"]), "clean_matches.csv: home_score is not numeric."
        assert pd.api.types.is_numeric_dtype(df_matches["away_score"]), "clean_matches.csv: away_score is not numeric."


        # 2. Load wc2026_fixtures.csv and assert
        fixtures_path = os.path.join(processed_dir, "wc2026_fixtures.csv")
        print(f"Validating {fixtures_path}...")
        df_fixtures = pd.read_csv(fixtures_path)
        df_fixtures["date"] = pd.to_datetime(df_fixtures["date"])

        # Exactly 38 rows (6 group matches + 32 knockout matches)
        row_count = len(df_fixtures)
        assert row_count == 38, f"wc2026_fixtures.csv: Expected 38 rows, got {row_count}."

        # All scores are null
        home_score_nulls = df_fixtures["home_score"].isnull().sum()
        away_score_nulls = df_fixtures["away_score"].isnull().sum()
        assert home_score_nulls == 38, f"wc2026_fixtures.csv: Expected 38 null home_scores, got {home_score_nulls}."
        assert away_score_nulls == 38, f"wc2026_fixtures.csv: Expected 38 null away_scores, got {away_score_nulls}."

        # date range check
        min_fix_date = df_fixtures["date"].min()
        max_fix_date = df_fixtures["date"].max()
        assert min_fix_date == pd.to_datetime("2026-06-27"), f"wc2026_fixtures.csv: Min date is {min_fix_date.strftime('%Y-%m-%d')}, expected 2026-06-27."


        # 3. Load clean_rankings.csv and assert
        rankings_path = os.path.join(processed_dir, "clean_rankings.csv")
        print(f"Validating {rankings_path}...")
        df_rankings = pd.read_csv(rankings_path)
        
        # No nulls
        for col in ["team", "rank", "rank_date"]:
            null_count = df_rankings[col].isnull().sum()
            assert null_count == 0, f"clean_rankings.csv: Column '{col}' contains {null_count} null value(s)."

        # Positive integer ranks
        assert pd.api.types.is_numeric_dtype(df_rankings["rank"]), "clean_rankings.csv: rank is not numeric."
        assert (df_rankings["rank"] > 0).all(), "clean_rankings.csv: Found rank <= 0."
        assert (df_rankings["rank"] == df_rankings["rank"].astype(int)).all(), "clean_rankings.csv: Found non-integer ranks."


        # 4. Load penalty_win_rates.csv and assert
        rates_path = os.path.join(processed_dir, "penalty_win_rates.csv")
        print(f"Validating {rates_path}...")
        df_rates = pd.read_csv(rates_path)

        # penalty_win_rate between 0.0 and 1.0
        min_rate = df_rates["penalty_win_rate"].min()
        max_rate = df_rates["penalty_win_rate"].max()
        assert 0.0 <= min_rate and max_rate <= 1.0, f"penalty_win_rates.csv: penalty_win_rate range [{min_rate}, {max_rate}] is out of bounds [0.0, 1.0]."

        # No null values
        null_total = df_rates.isnull().sum().sum()
        assert null_total == 0, f"penalty_win_rates.csv: Found {null_total} null value(s)."

        print("\nSUCCESS: All data validation checks passed")
        print("-" * 50)

    except AssertionError as e:
        print(f"\nFAILURE: Validation failed: {e}")
        print("-" * 50)
        raise e
    except Exception as e:
        print(f"\nFAILURE: Error during validation: {e}")
        print("-" * 50)
        raise e


if __name__ == "__main__":
    # Temporarily set logging to ERROR to avoid warning spam for historical teams not in the WC mapping
    import logging
    logging.getLogger("backend.utils.team_standardizer").setLevel(logging.ERROR)

    inspect_results()
    inspect_strength_datasets()
    inspect_supporting_datasets()
    clean_data()
    clean_results()
    clean_fifa_rankings()
    compute_penalty_win_rates()
    validate_clean_data()





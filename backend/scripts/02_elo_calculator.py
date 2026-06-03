import os
import sys
import pandas as pd
from collections import defaultdict

# Add project root to python path to import team_standardizer if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


class EloCalculator:
    DEFAULT_ELO = 1500
    K_FACTORS = {
        "FIFA World Cup": 50,
        "UEFA Euro": 30,
        "Copa América": 30,
        "African Cup of Nations": 30,
        "AFC Asian Cup": 30,
        "Gold Cup": 25,
        "FIFA World Cup qualification": 20,
        "UEFA Euro qualification": 20,
        "CONCACAF Nations League": 20,
        "UEFA Nations League": 20,
        "African Cup of Nations qualification": 15,
        "Friendly": 10,
    }
    DEFAULT_K = 15  # for tournaments not in the list above

    def __init__(self):
        self.team_elo = defaultdict(lambda: self.DEFAULT_ELO)

    def get_k_factor(self, tournament: str) -> float:
        """Returns K from K_FACTORS, or DEFAULT_K if not found."""
        return self.K_FACTORS.get(tournament, self.DEFAULT_K)

    def get_expected_score(self, elo_a: float, elo_b: float) -> float:
        """Standard Elo formula: 1 / (1 + 10 ** ((elo_b - elo_a) / 400))"""
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

    def get_margin_multiplier(self, goal_diff: int) -> float:
        """
        goal_diff = abs(score_a - score_b)
        1 goal → multiplier = 1.0
        2 goals → multiplier = 1.5
        3 goals → multiplier = 1.75
        4+ goals → multiplier = 2.0
        """
        if goal_diff <= 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        elif goal_diff == 3:
            return 1.75
        else:
            return 2.0

    def compute_elo_ratings(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        Input: clean_matches.csv loaded as a DataFrame, sorted chronologically
        
        Algorithm:
        1. Initialize team_elo = defaultdict(lambda: DEFAULT_ELO)
        2. Create empty list `elo_records`
        3. For each row in matches_df:
           a. Get current Elo for home_team and away_team BEFORE this match
           b. Append to elo_records: {date, home_team, away_team, home_elo_before, away_elo_before}
           c. Compute expected scores for both teams
           d. Determine actual result: home win=1/draw=0.5/away win=0 for home_team
           e. Compute goal_diff = abs(home_score - away_score)
           f. Get K = get_k_factor(tournament) * competition_weight * get_margin_multiplier(goal_diff)
           g. Update home_team Elo: new_elo = old_elo + K * (actual - expected)
           h. Update away_team Elo: new_elo = old_elo + K * ((1-actual) - (1-expected))
        4. Return elo_records as a DataFrame
        """
        self.team_elo = defaultdict(lambda: self.DEFAULT_ELO)
        elo_records = []

        for idx, row in matches_df.iterrows():
            date = row["date"]
            home_team = row["home_team"]
            away_team = row["away_team"]
            tournament = row["tournament"]
            competition_weight = row["competition_weight"]
            home_score = row["home_score"]
            away_score = row["away_score"]

            # a. Get current Elo for home_team and away_team BEFORE this match
            home_elo_before = self.team_elo[home_team]
            away_elo_before = self.team_elo[away_team]

            # b. Append to elo_records: {date, home_team, away_team, home_elo_before, away_elo_before}
            elo_records.append({
                "date": date,
                "home_team": home_team,
                "away_team": away_team,
                "home_elo_before": home_elo_before,
                "away_elo_before": away_elo_before
            })

            # c. Compute expected scores for both teams
            expected_home = self.get_expected_score(home_elo_before, away_elo_before)
            expected_away = 1.0 - expected_home

            # d. Determine actual result: home win=1/draw=0.5/away win=0 for home_team
            if home_score > away_score:
                actual_home = 1.0
            elif home_score < away_score:
                actual_home = 0.0
            else:
                actual_home = 0.5

            actual_away = 1.0 - actual_home

            # e. Compute goal_diff = abs(home_score - away_score)
            goal_diff = abs(int(home_score) - int(away_score))

            # f. Get K = get_k_factor(tournament) * competition_weight * get_margin_multiplier(goal_diff)
            k_factor = self.get_k_factor(tournament) * competition_weight * self.get_margin_multiplier(goal_diff)

            # g. Update home_team Elo
            self.team_elo[home_team] = home_elo_before + k_factor * (actual_home - expected_home)

            # h. Update away_team Elo
            self.team_elo[away_team] = away_elo_before + k_factor * (actual_away - expected_away)

        return pd.DataFrame(elo_records)

    def get_current_elo(self, team: str) -> float:
        """Returns the final Elo (most recent) for a team after all matches processed."""
        return self.team_elo[team]


def main():
    # 1. Load clean_matches.csv
    clean_matches_path = os.path.join("backend", "data", "processed", "clean_matches.csv")
    print(f"Loading clean matches from: {clean_matches_path}")
    if not os.path.exists(clean_matches_path):
        print(f"Error: {clean_matches_path} does not exist. Please run 01_data_cleaner.py first.")
        return

    matches_df = pd.read_csv(clean_matches_path)
    
    # Ensure they are sorted chronologically
    matches_df["date"] = pd.to_datetime(matches_df["date"])
    matches_df = matches_df.sort_values(by="date").reset_index(drop=True)

    # 2. Initialize EloCalculator
    print("Initializing Elo Calculator...")
    calculator = EloCalculator()

    # 3. Run compute_elo_ratings()
    print("Computing Elo ratings (this may take a few seconds)...")
    elo_records_df = calculator.compute_elo_ratings(matches_df)
    print("Elo calculations completed.")

    # 4. Print top 10 teams by current Elo
    top_10 = sorted(calculator.team_elo.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 teams by computed Elo:")
    for rank, (team, elo) in enumerate(top_10, 1):
        print(f"{rank}. {team}: {elo:.1f}")

    # 5. Compare top 10 against elo-rating.csv reference — they should be roughly similar
    elo_ref_path = os.path.join("backend", "data", "raw", "elo-rating.csv")
    if os.path.exists(elo_ref_path):
        ref_df = pd.read_csv(elo_ref_path)
        standardizer = TeamStandardizer()
        # Standardize team names in reference to match computed names
        ref_df["team"] = ref_df["team"].apply(standardizer.standardize)
        ref_df = ref_df.drop_duplicates(subset=["team"]).reset_index(drop=True)

        print("\n=== ELO COMPARISON (Computed vs. Reference `elo-rating.csv`) ===")
        print(f"{'Computed Rank':<15} {'Team (Computed)':<20} {'Computed Elo':<15} | {'Ref Rank':<10} {'Ref Elo':<10}")
        print("-" * 80)
        for rank_idx, (team, elo_val) in enumerate(top_10, 1):
            ref_match = ref_df[ref_df["team"] == team]
            if not ref_match.empty:
                ref_rank = ref_match.iloc[0]["rank"]
                ref_elo = ref_match.iloc[0]["rating"]
                print(f"{rank_idx:<15} {team:<20} {elo_val:<15.1f} | {ref_rank:<10} {ref_elo:<10.1f}")
            else:
                print(f"{rank_idx:<15} {team:<20} {elo_val:<15.1f} | {'N/A':<10} {'-':<10}")
    else:
        print(f"\nWarning: Reference file {elo_ref_path} not found. Skipping comparison.")

    # Create processed directory if it doesn't exist
    processed_dir = os.path.join("backend", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # 6. Save elo_records DataFrame to backend/data/processed/rolling_elo.csv
    rolling_elo_path = os.path.join(processed_dir, "rolling_elo.csv")
    elo_records_df.to_csv(rolling_elo_path, index=False)
    print(f"\nSaved rolling Elo records to: {rolling_elo_path}")

    # 7. Save final Elo snapshot (one row per team, final Elo only) to backend/data/processed/current_elo.csv
    current_elo_df = pd.DataFrame([
        {"team": team, "elo": elo} for team, elo in calculator.team_elo.items()
    ]).sort_values("elo", ascending=False).reset_index(drop=True)
    
    current_elo_path = os.path.join(processed_dir, "current_elo.csv")
    current_elo_df.to_csv(current_elo_path, index=False)
    print(f"Saved current Elo snapshot to: {current_elo_path}")


if __name__ == "__main__":
    main()

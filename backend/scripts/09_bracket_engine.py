import os
import sys
import json
import random
import pandas as pd
from functools import lru_cache

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


# FIFA 2026 allowed third-place matchups mapping slots to allowed group letters
# Winner of group: allowed third-placed team groups
ALLOWED_SLOTS = {
    'E': {'A', 'B', 'C', 'D', 'F'},
    'I': {'C', 'D', 'F', 'G', 'H'},
    'A': {'C', 'E', 'F', 'H', 'I'},
    'L': {'E', 'H', 'I', 'J', 'K'},
    'G': {'A', 'E', 'H', 'I', 'J'},
    'D': {'B', 'E', 'F', 'I', 'J'},
    'B': {'E', 'F', 'G', 'I', 'J'},
    'K': {'D', 'E', 'I', 'J', 'L'}
}

# Winners list facing third-places in round of 32 (order of matching)
THIRD_PLACE_SLOT_WINNERS = ['E', 'I', 'A', 'L', 'G', 'D', 'B', 'K']


@lru_cache(maxsize=1024)
def get_third_place_allocation(qualified_groups_tuple: tuple) -> dict:
    """
    Computes a deterministic bijection from the 8 group winners to the 8 qualified
    third-placed groups using a backtracking search.
    The LRU cache ensures we only solve the matching problem once per unique group combination.
    """
    assignment = {}
    used = set()
    
    def backtrack(idx):
        if idx == len(THIRD_PLACE_SLOT_WINNERS):
            return True
        winner = THIRD_PLACE_SLOT_WINNERS[idx]
        allowed = ALLOWED_SLOTS[winner]
        
        for g in qualified_groups_tuple:
            if g in allowed and g not in used:
                assignment[winner] = g
                used.add(g)
                if backtrack(idx + 1):
                    return True
                used.remove(g)
                del assignment[winner]
        return False

    if backtrack(0):
        return assignment
    else:
        # Fallback: if no perfect bijection found (should not happen in FIFA design), assign greedily
        assignment = {}
        used = set()
        for w in THIRD_PLACE_SLOT_WINNERS:
            allowed = ALLOWED_SLOTS[w]
            assigned = False
            for g in qualified_groups_tuple:
                if g in allowed and g not in used:
                    assignment[w] = g
                    used.add(g)
                    assigned = True
                    break
            if not assigned:
                for g in qualified_groups_tuple:
                    if g not in used:
                        assignment[w] = g
                        used.add(g)
                        break
        return assignment


def simulate_match_score(outcome: int) -> tuple:
    """
    Generates realistic goals scored by each team conditioned on match outcome.
    outcome: 0 = Team A Win, 1 = Draw, 2 = Team B Win
    Returns: (goals_a, goals_b)
    """
    if outcome == 1:
        # Draw: equal goals
        goals = random.choices([0, 1, 2, 3], weights=[0.25, 0.50, 0.20, 0.05], k=1)[0]
        return goals, goals
    elif outcome == 0:
        # A Win: A has more goals than B
        g_diff = random.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05], k=1)[0]
        g_lose = random.choices([0, 1, 2], weights=[0.50, 0.40, 0.10], k=1)[0]
        return g_lose + g_diff, g_lose
    else:
        # B Win: B has more goals than A
        g_diff = random.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05], k=1)[0]
        g_lose = random.choices([0, 1, 2], weights=[0.50, 0.40, 0.10], k=1)[0]
        return g_lose, g_lose + g_diff


class BracketEngine:
    def __init__(self):
        self.standardizer = TeamStandardizer()
        
        # Load penalty win rates
        penalty_rates_path = os.path.join("backend", "data", "processed", "penalty_win_rates.csv")
        self.penalty_rates = {}
        if os.path.exists(penalty_rates_path):
            df_rates = pd.read_csv(penalty_rates_path)
            for _, row in df_rates.iterrows():
                std_team = self.standardizer.standardize(row["team"])
                self.penalty_rates[std_team] = float(row["penalty_win_rate"])
                
        # Load group assignments
        groups_path = os.path.join("backend", "data", "cleaned", "wc_2026_groups.json")
        if not os.path.exists(groups_path):
            groups_path = os.path.join("backend", "data", "raw", "wc_2026_groups.json")
            
        with open(groups_path, "r", encoding="utf-8") as f:
            self.wc_data = json.load(f)
            
        self.groups = self.wc_data["groups"]
        self.knockout_bracket = self.wc_data["knockout_bracket"]

    def simulate_group_stage(self, predictor_cache: dict, elo_dict: dict) -> tuple:
        """
        Simulates the group stage (12 groups A-L, 4 teams each).
        Returns:
            group_results: dict mapping group letter to sorted team list [1st, 2nd, 3rd, 4th]
            standings_dict: dict mapping team to their standings metrics (points, gd, goals)
        """
        group_results = {}
        standings_dict = {}
        
        for g_letter, team_list in self.groups.items():
            # Initialize standings for this group
            g_standings = {
                team: {"points": 0, "goals_scored": 0, "goals_conceded": 0, "goal_diff": 0, "elo": elo_dict.get(team, 1600.0)}
                for team in team_list
            }
            
            # 6 round-robin matches
            # Matches: (0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)
            matches = [
                (team_list[0], team_list[1]),
                (team_list[0], team_list[2]),
                (team_list[0], team_list[3]),
                (team_list[1], team_list[2]),
                (team_list[1], team_list[3]),
                (team_list[2], team_list[3])
            ]
            
            for ta, tb in matches:
                # Get prediction probabilities from cache
                p_a, p_draw, p_b = predictor_cache[(ta, tb)]
                
                # Draw outcome
                outcome = random.choices([0, 1, 2], weights=[p_a, p_draw, p_b], k=1)[0]
                g_a, g_b = simulate_match_score(outcome)
                
                # Update stats
                g_standings[ta]["goals_scored"] += g_a
                g_standings[ta]["goals_conceded"] += g_b
                g_standings[ta]["goal_diff"] += (g_a - g_b)
                
                g_standings[tb]["goals_scored"] += g_b
                g_standings[tb]["goals_conceded"] += g_a
                g_standings[tb]["goal_diff"] += (g_b - g_a)
                
                if outcome == 0:
                    g_standings[ta]["points"] += 3
                elif outcome == 2:
                    g_standings[tb]["points"] += 3
                else:
                    g_standings[ta]["points"] += 1
                    g_standings[tb]["points"] += 1
            
            # Sort teams within the group
            # Tiebreakers: 1. Points, 2. GD, 3. Goals, 4. Elo (deterministic rating)
            sorted_teams = sorted(
                team_list,
                key=lambda t: (
                    g_standings[t]["points"],
                    g_standings[t]["goal_diff"],
                    g_standings[t]["goals_scored"],
                    g_standings[t]["elo"]
                ),
                reverse=True
            )
            
            group_results[g_letter] = sorted_teams
            for t in team_list:
                standings_dict[t] = g_standings[t]
                
        return group_results, standings_dict

    def rank_third_places(self, group_results: dict, standings_dict: dict) -> tuple:
        """
        Rank the 12 third-placed teams to select the top 8 advancing.
        Returns:
            advancing_teams_dict: dict mapping group letter to third-place team name
            qualified_groups_tuple: sorted tuple of group letters that advanced (e.g. ('A', 'C', ...))
        """
        third_place_candidates = []
        for g_letter, sorted_teams in group_results.items():
            t3 = sorted_teams[2]  # index 2 is third place
            t3_stats = standings_dict[t3]
            third_place_candidates.append({
                "team": t3,
                "group": g_letter,
                "points": t3_stats["points"],
                "goal_diff": t3_stats["goal_diff"],
                "goals_scored": t3_stats["goals_scored"],
                "elo": t3_stats["elo"]
            })
            
        # Sort candidates
        third_place_candidates.sort(
            key=lambda x: (x["points"], x["goal_diff"], x["goals_scored"], x["elo"]),
            reverse=True
        )
        
        # Take top 8
        advancing = third_place_candidates[:8]
        advancing_dict = {item["group"]: item["team"] for item in advancing}
        
        qualified_groups = sorted([item["group"] for item in advancing])
        return advancing_dict, tuple(qualified_groups)

    def simulate_knockout_match(self, team_a: str, team_b: str, predictor_cache: dict) -> str:
        """Simulates a single knockout match, resolving draws via penalty shootouts."""
        p_a, p_draw, p_b = predictor_cache[(team_a, team_b)]
        
        # Draw outcome
        outcome = random.choices([0, 1, 2], weights=[p_a, p_draw, p_b], k=1)[0]
        
        if outcome == 0:
            return team_a
        elif outcome == 2:
            return team_b
        else:
            # Draw -> Penalty Shootout
            pa_rate = self.penalty_rates.get(self.standardizer.standardize(team_a), 0.5)
            pb_rate = self.penalty_rates.get(self.standardizer.standardize(team_b), 0.5)
            
            # Probability of team A winning the shootout
            denom = pa_rate + pb_rate
            p_shootout_a = pa_rate / denom if denom > 0 else 0.5
            
            if random.random() < p_shootout_a:
                return team_a
            else:
                return team_b

    def simulate_tournament(self, predictor_cache: dict, elo_dict: dict) -> dict:
        """
        Simulates the entire World Cup tournament once.
        Returns a dictionary tracking the furthest round achieved by each team.
        """
        # Achievements map
        achievements = {
            team: "group_stage_exit" 
            for group in self.groups.values() 
            for team in group
        }
        
        # 1. Group Stage
        group_results, standings_dict = self.simulate_group_stage(predictor_cache, elo_dict)
        
        # 2. Rank Third Places
        adv_third_places, qual_groups_tuple = self.rank_third_places(group_results, standings_dict)
        
        # Mark top 2 and qualifying third places as reached Round of 32
        for g_letter, sorted_teams in group_results.items():
            achievements[sorted_teams[0]] = "reached_r32"
            achievements[sorted_teams[1]] = "reached_r32"
        for t3 in adv_third_places.values():
            achievements[t3] = "reached_r32"
            
        # Get third place allocation mapping (winner_group -> third_place_group)
        third_place_alloc = get_third_place_allocation(qual_groups_tuple)
        
        # 3. Round of 32
        # We need to map bracket placeholders to actual team names
        r32_winners = {}
        for match in self.knockout_bracket["round_of_32"]:
            m_id = match["match_id"]
            home_placeholder = match["home"]
            away_placeholder = match["away"]
            
            # Resolve home team name
            if home_placeholder.startswith("winner_"):
                g = home_placeholder.split("_")[1]
                home_team = group_results[g][0]
            elif home_placeholder.startswith("runner_up_"):
                g = home_placeholder.split("_")[2]
                home_team = group_results[g][1]
            else:
                # Third place placeholder (e.g. third_place_A_B_C_D_F)
                # It plays against winner of some group. We look up the winner group letter.
                # In the round of 32 match description, the away placeholder is the third-place team
                # and the home placeholder is the group winner, so we find who the home team winner group letter is.
                # E.g. home = "winner_E", away = "third_place_A_B_C_D_F"
                pass
                
            # Resolve away team name
            if away_placeholder.startswith("winner_"):
                g = away_placeholder.split("_")[1]
                away_team = group_results[g][0]
            elif away_placeholder.startswith("runner_up_"):
                g = away_placeholder.split("_")[2]
                away_team = group_results[g][1]
            elif away_placeholder.startswith("third_place_"):
                # We need to find which winner group plays this third-place team.
                # The winner group letter is the home placeholder's letter
                winner_group_letter = home_placeholder.split("_")[1]
                assigned_group_letter = third_place_alloc[winner_group_letter]
                away_team = adv_third_places[assigned_group_letter]
            else:
                # Backup resolve if it's reversed
                winner_group_letter = away_placeholder.split("_")[1]
                assigned_group_letter = third_place_alloc[winner_group_letter]
                home_team = adv_third_places[assigned_group_letter]
                
            # Simulate match
            winner = self.simulate_knockout_match(home_team, away_team, predictor_cache)
            r32_winners[m_id] = winner
            achievements[winner] = "reached_r16"

        # 4. Round of 16
        r16_winners = {}
        for match in self.knockout_bracket["round_of_16"]:
            m_id = match["match_id"]
            home_m_id = int(match["home"].split("_")[1])
            away_m_id = int(match["away"].split("_")[1])
            
            home_team = r32_winners[home_m_id]
            away_team = r32_winners[away_m_id]
            
            winner = self.simulate_knockout_match(home_team, away_team, predictor_cache)
            r16_winners[m_id] = winner
            achievements[winner] = "reached_qf"
            
        # 5. Quarter-finals
        qf_winners = {}
        for match in self.knockout_bracket["quarter_finals"]:
            m_id = match["match_id"]
            home_m_id = int(match["home"].split("_")[1])
            away_m_id = int(match["away"].split("_")[1])
            
            home_team = r16_winners[home_m_id]
            away_team = r16_winners[away_m_id]
            
            winner = self.simulate_knockout_match(home_team, away_team, predictor_cache)
            qf_winners[m_id] = winner
            achievements[winner] = "reached_sf"
            
        # 6. Semi-finals
        sf_winners = {}
        sf_losers = {}
        for match in self.knockout_bracket["semi_finals"]:
            m_id = match["match_id"]
            home_m_id = int(match["home"].split("_")[1])
            away_m_id = int(match["away"].split("_")[1])
            
            home_team = qf_winners[home_m_id]
            away_team = qf_winners[away_m_id]
            
            winner = self.simulate_knockout_match(home_team, away_team, predictor_cache)
            loser = home_team if winner == away_team else away_team
            
            sf_winners[m_id] = winner
            sf_losers[m_id] = loser
            achievements[winner] = "reached_final"
            
        # 7. Third-Place Play-off
        third_place_match = self.knockout_bracket["third_place"]
        t_home = sf_losers[int(third_place_match["home"].split("_")[1])]
        t_away = sf_losers[int(third_place_match["away"].split("_")[1])]
        third_place_winner = self.simulate_knockout_match(t_home, t_away, predictor_cache)
        fourth_place_team = t_home if third_place_winner == t_away else t_away
        
        achievements[third_place_winner] = "third_place"
        achievements[fourth_place_team] = "fourth_place"
        
        # 8. Final
        final_match = self.knockout_bracket["final"]
        f_home = sf_winners[int(final_match["home"].split("_")[1])]
        f_away = sf_winners[int(final_match["away"].split("_")[1])]
        champion = self.simulate_knockout_match(f_home, f_away, predictor_cache)
        runner_up = f_home if champion == f_away else f_away
        
        achievements[champion] = "champion"
        achievements[runner_up] = "runner_up"
        
        return achievements

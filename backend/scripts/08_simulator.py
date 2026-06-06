import os
import sys
import json
import pandas as pd
from tqdm import tqdm

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import importlib.util

# Dynamically import number-prefixed scripts
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

scripts_dir = os.path.dirname(os.path.abspath(__file__))
predictor_mod = import_module_from_path("predictor", os.path.join(scripts_dir, "07_predictor.py"))
MatchPredictor = predictor_mod.MatchPredictor

bracket_mod = import_module_from_path("bracket_engine", os.path.join(scripts_dir, "09_bracket_engine.py"))
BracketEngine = bracket_mod.BracketEngine


def main():
    print("=== 2026 FIFA World Cup Monte Carlo Simulator ===")
    
    # 1. Parse simulation count
    num_simulations = 100000  # Default to 100,000 for standard run
    if len(sys.argv) > 1:
        try:
            num_simulations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid simulation count '{sys.argv[1]}'. Using default of 100,000.")
            
    print(f"Configured to run {num_simulations:,} tournament simulations.")
    
    # 2. Initialize engines
    print("Initializing MatchPredictor and BracketEngine...")
    predictor = MatchPredictor()
    bracket_engine = BracketEngine()
    
    # Get all unique teams in the tournament
    tournament_teams = []
    for g_teams in bracket_engine.groups.values():
        tournament_teams.extend(g_teams)
    tournament_teams = sorted(list(set(tournament_teams)))
    
    print(f"Loaded {len(tournament_teams)} teams from group configurations.")
    
    # Build ELO rating mapping dictionary for tiebreakers
    elo_dict = {}
    for team in tournament_teams:
        try:
            stats = predictor.get_team_features(team)
            elo_dict[team] = float(stats["elo"])
        except ValueError as e:
            print(f"WARNING: ELO mapping error for '{team}': {e}. Defaulting to 1500.0.")
            elo_dict[team] = 1500.0
            
    # 3. Precompute predictions for all 1,128 pairings
    print("Precomputing pairwise match predictions...")
    predictor_cache = {}
    for i in range(len(tournament_teams)):
        for j in range(i + 1, len(tournament_teams)):
            ta = tournament_teams[i]
            tb = tournament_teams[j]
            
            # Predict symmetric probabilities
            pred = predictor.predict_match(ta, tb)
            p_a = pred["team_a_prob"]
            p_draw = pred["draw_prob"]
            p_b = pred["team_b_prob"]
            
            predictor_cache[(ta, tb)] = (p_a, p_draw, p_b)
            predictor_cache[(tb, ta)] = (p_b, p_draw, p_a)
            
    print(f"Successfully cached predictions for {len(predictor_cache)} directed pairings.")
    
    # 4. Initialize progression counters
    prog_counts = {
        team: {
            "champion": 0,
            "runner_up": 0,
            "third_place": 0,
            "fourth_place": 0,
            "reached_sf": 0,
            "reached_qf": 0,
            "reached_r16": 0,
            "reached_r32": 0,
            "group_stage_exit": 0
        }
        for team in tournament_teams
    }
    
    # 5. Run Monte Carlo simulations
    print(f"\nSimulating tournament {num_simulations:,} times...")
    for _ in tqdm(range(num_simulations), desc="Monte Carlo Runs", unit="run"):
        achievements = bracket_engine.simulate_tournament(predictor_cache, elo_dict)
        for team, round_reached in achievements.items():
            if team in prog_counts:
                prog_counts[team][round_reached] += 1
                
    # 6. Aggregate probabilities
    results_list = []
    for team in tournament_teams:
        c = prog_counts[team]
        
        # Calculate individual round probabilities
        champion_prob = c["champion"] / num_simulations
        runner_up_prob = c["runner_up"] / num_simulations
        third_place_prob = c["third_place"] / num_simulations
        fourth_place_prob = c["fourth_place"] / num_simulations
        sf_prob = c["reached_sf"] / num_simulations
        qf_prob = c["reached_qf"] / num_simulations
        r16_prob = c["reached_r16"] / num_simulations
        r32_prob = c["reached_r32"] / num_simulations
        
        # Cumulative progression probabilities
        win_prob = champion_prob
        final_prob = win_prob + runner_up_prob
        semifinal_prob = final_prob + third_place_prob + fourth_place_prob + sf_prob
        quarterfinal_prob = semifinal_prob + qf_prob
        round_16_prob = quarterfinal_prob + r16_prob
        round_32_prob = round_16_prob + r32_prob
        
        results_list.append({
            "team": team,
            "win_prob": round(win_prob, 5),
            "final_prob": round(final_prob, 5),
            "semifinal_prob": round(semifinal_prob, 5),
            "quarterfinal_prob": round(quarterfinal_prob, 5),
            "r16_prob": round(round_16_prob, 5),
            "r32_prob": round(round_32_prob, 5)
        })
        
    # Sort teams by win probability (descending), then final, then semifinal
    results_list.sort(key=lambda x: (x["win_prob"], x["final_prob"], x["semifinal_prob"], x["quarterfinal_prob"]), reverse=True)
    
    # 7. Save to backend/outputs/simulation_results.json
    output_dir = os.path.join("backend", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "simulation_results.json")
    output_data = {
        "total_simulations": num_simulations,
        "teams": results_list
    }
    
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\n[SUCCESS] Saved simulation results to: {output_path}")
    
    # 8. Print formatted standings table (Top 25 teams)
    print("\n" + "=" * 80)
    print(f"   2026 FIFA World Cup Projections (Top 25) — Based on {num_simulations:,} runs")
    print("=" * 80)
    print(f"{'Pos':<3} | {'Team':<20} | {'Win %':<8} | {'Final %':<8} | {'SF %':<8} | {'QF %':<8} | {'R16 %':<8} | {'R32 %':<8}")
    print("-" * 80)
    for idx, r in enumerate(results_list[:25]):
        print(
            f"{idx + 1:<3} | {r['team']:<20} | "
            f"{r['win_prob'] * 100:<8.2f} | "
            f"{r['final_prob'] * 100:<8.2f} | "
            f"{r['semifinal_prob'] * 100:<8.2f} | "
            f"{r['quarterfinal_prob'] * 100:<8.2f} | "
            f"{r['r16_prob'] * 100:<8.2f} | "
            f"{r['r32_prob'] * 100:<8.2f}"
        )
    print("=" * 80)


if __name__ == "__main__":
    main()

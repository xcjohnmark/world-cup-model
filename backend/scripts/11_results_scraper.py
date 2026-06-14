import os
import sys
import json
import requests
import subprocess
import logging
from bs4 import BeautifulSoup

# Resolve project root and add to sys.path to allow imports from root level
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import importlib.util

from backend.utils.team_standardizer import TeamStandardizer

# Dynamically import 09_bracket_engine.py to avoid numeric prefix syntax errors
scripts_dir = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("bracket_engine", os.path.join(scripts_dir, "09_bracket_engine.py"))
bracket_engine_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bracket_engine_mod)
update_with_real_result = bracket_engine_mod.update_with_real_result

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("results_scraper")

ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"


def fetch_espn_results(standardizer: TeamStandardizer) -> list:
    """
    Fetches completed match results from ESPN's scoreboard API.
    Returns: List of dicts: {"home_team": str (std), "away_team": str (std), "home_score": int, "away_score": int}
    """
    logger.info(f"Fetching live results from ESPN API: {ESPN_API_URL}")
    results = []
    try:
        resp = requests.get(ESPN_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        events = data.get("events", [])
        logger.info(f"Retrieved {len(events)} events from ESPN API.")
        
        for event in events:
            # Check if match is completed
            status = event.get("status", {})
            status_type = status.get("type", {})
            completed = status_type.get("completed", False)
            state = status_type.get("state", "pre")
            
            if not (completed or state == "post"):
                continue
                
            competitions = event.get("competitions", [])
            if not competitions:
                continue
                
            competitors = competitions[0].get("competitors", [])
            if len(competitors) < 2:
                continue
                
            # Parse teams and scores
            home_item = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_item = next((c for c in competitors if c.get("homeAway") == "away"), None)
            
            if not home_item or not away_item:
                continue
                
            home_name = home_item.get("team", {}).get("displayName")
            away_name = away_item.get("team", {}).get("displayName")
            
            home_score_str = home_item.get("score")
            away_score_str = away_item.get("score")
            
            if home_score_str is None or away_score_str is None:
                continue
                
            try:
                home_score = int(home_score_str)
                away_score = int(away_score_str)
            except ValueError:
                continue
                
            home_std = standardizer.standardize(home_name)
            away_std = standardizer.standardize(away_name)
            
            results.append({
                "home_team": home_std,
                "away_team": away_std,
                "home_score": home_score,
                "away_score": away_score
            })
            
        logger.info(f"Successfully parsed {len(results)} completed matches from ESPN.")
    except Exception as e:
        logger.error(f"Error fetching from ESPN API: {e}")
        
    return results


def fetch_wikipedia_results(standardizer: TeamStandardizer) -> list:
    """
    Fallback scraper: Fetches match results from the Wikipedia 2026 World Cup page.
    Returns: List of dicts: {"home_team": str (std), "away_team": str (std), "home_score": int, "away_score": int}
    """
    logger.info(f"Fallback: Fetching results from Wikipedia: {WIKIPEDIA_URL}")
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(WIKIPEDIA_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        boxes = soup.find_all(class_="footballbox")
        logger.info(f"Found {len(boxes)} match boxes on Wikipedia page.")
        
        for box in boxes:
            home_tag = box.find(class_="fhome")
            away_tag = box.find(class_="faway")
            score_tag = box.find(class_="fscore")
            
            if not home_tag or not away_tag or not score_tag:
                continue
                
            home_name = home_tag.get_text(strip=True)
            away_name = away_tag.get_text(strip=True)
            score_text = score_tag.get_text(strip=True)
            
            # Parse score (handles en-dash '–', standard hyphen '-', and spaces)
            score_text = score_text.replace("–", "-").replace(" ", "")
            parts = score_text.split("-")
            if len(parts) < 2:
                # Match has not been played yet (e.g. shows time or "v")
                continue
                
            try:
                # Ignore extra time indicators like "a.e.t." or penalty results inside parentheses
                score_a = int(parts[0].split("(")[0])
                score_b = int(parts[1].split("(")[0])
            except ValueError:
                continue
                
            home_std = standardizer.standardize(home_name)
            away_std = standardizer.standardize(away_name)
            
            results.append({
                "home_team": home_std,
                "away_team": away_std,
                "home_score": score_a,
                "away_score": score_b
            })
            
        logger.info(f"Successfully parsed {len(results)} completed matches from Wikipedia.")
    except Exception as e:
        logger.error(f"Error scraping Wikipedia results: {e}")
        
    return results


def run_scraper() -> dict:
    """
    Main function to orchestrate the scraping, database updates, and re-simulation.
    """
    standardizer = TeamStandardizer()
    
    # 1. Fetch completed match scores (ESPN first, then Wikipedia fallback)
    scraped_results = fetch_espn_results(standardizer)
    if not scraped_results:
        logger.warning("No results found from ESPN. Trying Wikipedia fallback...")
        scraped_results = fetch_wikipedia_results(standardizer)
        
    if not scraped_results:
        logger.error("Failed to retrieve any completed match results from ESPN or Wikipedia.")
        return {"updated_matches": [], "status": "no_external_data"}
        
    # 2. Load current bracket_full.json
    bracket_path = os.path.join(project_root, "backend", "outputs", "bracket_full.json")
    if not os.path.exists(bracket_path):
        logger.error(f"bracket_full.json not found at {bracket_path}. Run 09_bracket_engine.py first.")
        return {"updated_matches": [], "status": "no_bracket_file"}
        
    with open(bracket_path, "r", encoding="utf-8") as f:
        bracket = json.load(f)
        
    # 3. Find and update matches that have newly completed scores
    updated_matches_list = []
    
    # Get all matches from bracket_full.json
    all_bracket_matches = []
    # Group stage matches
    for group_data in bracket.get("group_stage", {}).values():
        all_bracket_matches.extend(group_data.get("matches", []))
    # Knockout stage matches
    for stage in ["round_of_32", "round_of_16", "quarterfinals", "semifinals", "final"]:
        all_bracket_matches.extend(bracket.get(stage, {}).get("matches", []))
        
    # Process updates
    for scraped in scraped_results:
        scraped_home = scraped["home_team"]
        scraped_away = scraped["away_team"]
        score_a = scraped["home_score"]
        score_b = scraped["away_score"]
        
        # Look for matching match in local bracket database
        for m in all_bracket_matches:
            # Match is only update-eligible if it doesn't already have an actual result
            if m.get("actual_result") is not None:
                continue
                
            m_home = standardizer.standardize(m["team_a"])
            m_away = standardizer.standardize(m["team_b"])
            
            # Check for direct or reversed team matchups
            if m_home == scraped_home and m_away == scraped_away:
                logger.info(f"New match result detected: {m['team_a']} {score_a} - {score_b} {m['team_b']} (ID: {m['match_id']})")
                update_with_real_result(m["match_id"], score_a, score_b)
                updated_matches_list.append({
                    "match_id": m["match_id"],
                    "team_a": m["team_a"],
                    "team_b": m["team_b"],
                    "score_a": score_a,
                    "score_b": score_b
                })
                break
            elif m_home == scraped_away and m_away == scraped_home:
                # Reversed matchup (scraped home team is local away team)
                logger.info(f"New match result detected (reversed): {m['team_a']} {score_b} - {score_a} {m['team_b']} (ID: {m['match_id']})")
                update_with_real_result(m["match_id"], score_b, score_a)
                updated_matches_list.append({
                    "match_id": m["match_id"],
                    "team_a": m["team_a"],
                    "team_b": m["team_b"],
                    "score_a": score_b,
                    "score_b": score_a
                })
                break

    # 4. If new matches were updated, re-run simulations and rebuild the bracket structure
    if updated_matches_list:
        logger.info(f"Successfully updated {len(updated_matches_list)} new match results. Running simulations...")
        
        # Re-run simulator (08_simulator.py) with 10,000 simulations for fast execution
        scripts_dir = os.path.join(project_root, "backend", "scripts")
        simulator_path = os.path.join(scripts_dir, "08_simulator.py")
        logger.info("Executing 08_simulator.py with 10,000 runs...")
        subprocess.run([sys.executable, simulator_path, "10000"], check=True)
        
        # Re-run bracket engine (09_bracket_engine.py) to rebuild layout files
        bracket_engine_path = os.path.join(scripts_dir, "09_bracket_engine.py")
        logger.info("Executing 09_bracket_engine.py...")
        subprocess.run([sys.executable, bracket_engine_path], check=True)
        
        logger.info("Successfully updated match data, simulations, and tournament bracket layouts.")
    else:
        logger.info("No new match results detected. Database is fully up-to-date.")
        
    # 5. Also scrape and update FIFA standings cache (fifa_standings_scraped.json)
    try:
        logger.info("Scraping Wikipedia group standings...")
        import datetime
        from backend.main import scrape_wikipedia_standings
        scraped_groups = scrape_wikipedia_standings()
        cache_data = {
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "groups": scraped_groups
        }
        cache_path = os.path.join(project_root, "backend", "outputs", "fifa_standings_scraped.json")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
        logger.info("Wikipedia standings cache updated successfully in script run.")
    except Exception as e:
        logger.error(f"Failed to update Wikipedia standings cache: {e}")

    return {
        "status": "success",
        "updated_matches": updated_matches_list
    }


if __name__ == "__main__":
    run_scraper()

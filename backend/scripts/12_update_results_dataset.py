import os
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging

# Resolve project root and add to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("update_results_dataset")

ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719"
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"


def fetch_espn_results(standardizer: TeamStandardizer) -> list:
    logger.info(f"Fetching results from ESPN API: {ESPN_API_URL}")
    results = []
    try:
        resp = requests.get(ESPN_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        events = data.get("events", [])
        for event in events:
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
                
            results.append({
                "home_team": home_name,
                "away_team": away_name,
                "home_score": home_score,
                "away_score": away_score,
                "date": event.get("date", "")[:10]  # YYYY-MM-DD
            })
    except Exception as e:
        logger.error(f"Error fetching from ESPN API: {e}")
    return results


def fetch_wikipedia_results(standardizer: TeamStandardizer) -> list:
    logger.info(f"Fetching results from Wikipedia: {WIKIPEDIA_URL}")
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(WIKIPEDIA_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        boxes = soup.find_all(class_="footballbox")
        
        for box in boxes:
            home_tag = box.find(class_="fhome")
            away_tag = box.find(class_="faway")
            score_tag = box.find(class_="fscore")
            date_tag = box.find(class_="fdate")
            
            if not home_tag or not away_tag or not score_tag:
                continue
                
            home_name = home_tag.get_text(strip=True)
            away_name = away_tag.get_text(strip=True)
            score_text = score_tag.get_text(strip=True)
            
            # Simple date parsing or fallback date
            date_text = "2026-06-28"  # fallback
            if date_tag:
                date_str = date_tag.get_text(strip=True)
                months = {
                    "June": "06",
                    "July": "07"
                }
                for m_name, m_num in months.items():
                    if m_name in date_str:
                        day_str = "".join([c for c in date_str.split(m_name)[0] if c.isdigit()])
                        if day_str:
                            day = int(day_str)
                            date_text = f"2026-{m_num}-{day:02d}"
                        break
            
            score_text = score_text.replace("–", "-").replace(" ", "")
            parts = score_text.split("-")
            if len(parts) < 2:
                continue
                
            try:
                score_a = int(parts[0].split("(")[0])
                score_b = int(parts[1].split("(")[0])
            except ValueError:
                continue
                
            results.append({
                "home_team": home_name,
                "away_team": away_name,
                "home_score": score_a,
                "away_score": score_b,
                "date": date_text
            })
    except Exception as e:
        logger.error(f"Error scraping Wikipedia: {e}")
    return results


def main():
    standardizer = TeamStandardizer()
    
    # 1. Fetch live results from both sources
    espn_res = fetch_espn_results(standardizer)
    wiki_res = fetch_wikipedia_results(standardizer)
    
    # Combine results
    all_scraped = espn_res + wiki_res
    logger.info(f"Retrieved {len(all_scraped)} matches in total from ESPN and Wikipedia.")
    
    # Load raw results.csv
    results_path = os.path.join(project_root, "backend", "data", "raw", "results.csv")
    if not os.path.exists(results_path):
        logger.error(f"results.csv not found at {results_path}")
        return
        
    df = pd.read_csv(results_path)
    logger.info(f"Loaded results.csv with {len(df)} rows.")
    
    # Remove any previously appended knockout matches (date >= 2026-06-28) to start fresh
    original_len = len(df)
    df = df[df["date"] < "2026-06-28"].copy()
    logger.info(f"Removed {original_len - len(df)} previously appended knockout rows.")
    
    # Update the 72 group stage matches (date >= 2026-06-11 and date <= 2026-06-27)
    group_mask = (df["date"] >= "2026-06-11") & (df["date"] <= "2026-06-27")
    logger.info(f"Found {len(df[group_mask])} group stage rows to update in results.csv.")
    
    matched_scraped_indices = set()
    updated_count = 0
    for idx, row in df[group_mask].iterrows():
        home_std = standardizer.standardize(row["home_team"])
        away_std = standardizer.standardize(row["away_team"])
        
        # Look for a match in all_scraped
        match_found = None
        for i, s in enumerate(all_scraped):
            if i in matched_scraped_indices:
                continue
            s_home_std = standardizer.standardize(s["home_team"])
            s_away_std = standardizer.standardize(s["away_team"])
            
            if (home_std == s_home_std and away_std == s_away_std) or (home_std == s_away_std and away_std == s_home_std):
                match_found = s
                matched_scraped_indices.add(i)
                break
                
        if match_found:
            # Set scores. If reversed, swap scores.
            if home_std == standardizer.standardize(match_found["home_team"]):
                df.at[idx, "home_score"] = match_found["home_score"]
                df.at[idx, "away_score"] = match_found["away_score"]
            else:
                df.at[idx, "home_score"] = match_found["away_score"]
                df.at[idx, "away_score"] = match_found["home_score"]
            updated_count += 1
            
    logger.info(f"Updated {updated_count} group stage scores.")
    
    # Any match in all_scraped that was NOT matched to a group stage match is a knockout stage match!
    ko_scraped = [s for i, s in enumerate(all_scraped) if i not in matched_scraped_indices]
    logger.info(f"Found {len(ko_scraped)} unmatched matches, identifying them as knockouts.")
    
    # Deduplicate ko_scraped to avoid duplicates (comparing standardized matchups)
    ko_unique = []
    seen_matchups = set()
    for s in ko_scraped:
        home_std = standardizer.standardize(s["home_team"])
        away_std = standardizer.standardize(s["away_team"])
        matchup_key = tuple(sorted([home_std, away_std]))
        if matchup_key not in seen_matchups:
            seen_matchups.add(matchup_key)
            ko_unique.append(s)
            
    logger.info(f"Found {len(ko_unique)} unique knockout matches to append.")
    
    # Append them
    new_rows = []
    for ko in ko_unique:
        home_name = standardizer.standardize(ko["home_team"])
        away_name = standardizer.standardize(ko["away_team"])
        
        new_rows.append({
            "date": ko["date"],
            "home_team": home_name,
            "away_team": away_name,
            "home_score": ko["home_score"],
            "away_score": ko["away_score"],
            "tournament": "FIFA World Cup",
            "city": "Unknown",
            "country": "United States",
            "neutral": True
        })
        
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df = pd.concat([df, df_new], ignore_index=True)
        
    logger.info(f"Appended {len(new_rows)} new knockout matches to results.csv.")
    
    # Save results.csv back
    df.to_csv(results_path, index=False)
    logger.info(f"Saved updated results.csv with {len(df)} rows to {results_path}.")


if __name__ == "__main__":
    main()

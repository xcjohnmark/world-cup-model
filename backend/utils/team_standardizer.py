import os
import json
import logging
import unicodedata
import re

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class TeamStandardizer:
    def __init__(self, mapping_path=None):
        if mapping_path is None:
            # Default path relative to project structure:
            # backend/utils/team_standardizer.py -> backend/data/team_mapping.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mapping_path = os.path.abspath(os.path.join(current_dir, "..", "data", "team_mapping.json"))
        
        self.mapping_path = mapping_path
        self.canonical_lookup = {}
        self.display_lookup = {}
        self.fifa_code_lookup = {}
        self.load_mapping()

    def _normalize(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        # Lowercase and strip whitespace
        text = text.lower().strip()
        # Remove accents
        text = "".join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c)
        )
        # Strip special characters and punctuation (keep lowercase a-z, 0-9, and spaces)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def load_mapping(self):
        try:
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for team in data.get("teams", []):
                canonical = team["canonical_name"]
                fifa_code = team["fifa_code"]
                display = team["display_name"]
                aliases = team.get("aliases", [])
                
                # Map canonical, FIFA code, and all aliases to canonical name
                keys_to_map = [canonical, fifa_code] + aliases
                
                for key in keys_to_map:
                    norm_key = self._normalize(key)
                    if norm_key:
                        self.canonical_lookup[norm_key] = canonical
                        
                # Register displays and FIFA codes by canonical name
                self.display_lookup[canonical] = display
                self.fifa_code_lookup[canonical] = fifa_code
                
        except Exception as e:
            logger.error(f"Error loading team mapping from {self.mapping_path}: {e}")
            raise e

    def standardize(self, team_name: str) -> str:
        """
        Takes a raw team name and returns the official canonical name.
        Returns the original input if no match is found, logging a warning.
        """
        if not team_name or not isinstance(team_name, str):
            return team_name
        
        norm_name = self._normalize(team_name)
        if norm_name in self.canonical_lookup:
            return self.canonical_lookup[norm_name]
        
        # Log warning and return name as-is
        logger.warning(f"Team name '{team_name}' not found in mapping dictionary.")
        return team_name

    def get_display_name(self, team_name: str) -> str:
        """
        Returns the friendly display name for UI rendering.
        If the team is not in the mapping, returns the standardized name.
        """
        canonical = self.standardize(team_name)
        return self.display_lookup.get(canonical, canonical)

    def get_fifa_code(self, team_name: str) -> str:
        """
        Returns the 3-letter FIFA code for the team.
        If the team is not in the mapping, returns None.
        """
        canonical = self.standardize(team_name)
        return self.fifa_code_lookup.get(canonical, None)

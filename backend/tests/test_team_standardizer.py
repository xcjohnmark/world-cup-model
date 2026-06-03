import os
import sys
import unittest

# Add project root to python path to import team_standardizer
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.team_standardizer import TeamStandardizer


class TestTeamStandardizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.standardizer = TeamStandardizer()

    def test_canonicalization(self):
        # Test basic standardization
        self.assertEqual(self.standardizer.standardize("South Korea"), "Korea Republic")
        self.assertEqual(self.standardizer.standardize("KOR"), "Korea Republic")
        self.assertEqual(self.standardizer.standardize("Republic of Korea"), "Korea Republic")
        
        self.assertEqual(self.standardizer.standardize("USA"), "United States")
        self.assertEqual(self.standardizer.standardize("United States of America"), "United States")
        
        self.assertEqual(self.standardizer.standardize("Ivory Coast"), "Côte d'Ivoire")
        self.assertEqual(self.standardizer.standardize("Cote d'Ivoire"), "Côte d'Ivoire")
        
        self.assertEqual(self.standardizer.standardize("Curaþao"), "Curaçao")
        self.assertEqual(self.standardizer.standardize("Curacao"), "Curaçao")
        
        self.assertEqual(self.standardizer.standardize("Holland"), "Netherlands")
        self.assertEqual(self.standardizer.standardize("Great Britain"), "England")

    def test_display_names(self):
        # Test friendly display name rendering
        self.assertEqual(self.standardizer.get_display_name("Korea Republic"), "South Korea")
        self.assertEqual(self.standardizer.get_display_name("South Korea"), "South Korea")
        self.assertEqual(self.standardizer.get_display_name("USA"), "United States")
        self.assertEqual(self.standardizer.get_display_name("Côte d'Ivoire"), "Ivory Coast")

    def test_fifa_codes(self):
        # Test retrieving FIFA codes
        self.assertEqual(self.standardizer.get_fifa_code("South Korea"), "KOR")
        self.assertEqual(self.standardizer.get_fifa_code("USA"), "USA")
        self.assertEqual(self.standardizer.get_fifa_code("Ivory Coast"), "CIV")
        self.assertEqual(self.standardizer.get_fifa_code("Curaçao"), "CUW")

    def test_unmapped_teams(self):
        # Test unmapped names return as-is
        self.assertEqual(self.standardizer.standardize("Wakanda"), "Wakanda")
        self.assertEqual(self.standardizer.get_display_name("Wakanda"), "Wakanda")
        self.assertIsNone(self.standardizer.get_fifa_code("Wakanda"))


if __name__ == "__main__":
    unittest.main()

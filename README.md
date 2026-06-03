# WC2026 Predictor

An ML-powered prediction platform for the **2026 FIFA World Cup**. This system uses historical match results, FIFA rankings, and ELO calculations to train an **XGBoost** model to simulate the entire World Cup tournament 1,000,000 times, computing progression probabilities for all 48 participating countries.

---

## Project Structure

```text
wc-pred-model/
├── backend/
│   ├── data/
│   │   ├── raw/
│   │   │   ├── results.csv             # Historical match results since 1872
│   │   │   ├── fifa-ranking.csv        # Historical FIFA rankings
│   │   │   ├── elo-rating.csv          # Snapshot ELO values (for validation)
│   │   │   ├── goalscorers.csv         # Supplementary context on goal scorers
│   │   │   ├── shootouts.csv           # Historical penalty shootouts
│   │   │   ├── former-names.csv        # Maps historical country name transitions
│   │   │   └── wc_2026_groups.json     # 48-team groups & bracket path mappings
│   │   ├── cleaned/
│   │   │   ├── results.csv             # Standardized match results
│   │   │   ├── fifa-ranking.csv        # Standardized FIFA rankings
│   │   │   └── wc_2026_groups.json     # Standardized WC groups
│   │   └── team_mapping.json           # Naming translations & FIFA codes
│   ├── scripts/
│   │   ├── 01_data_cleaner.py          # Load, inspect, and normalize raw datasets
│   │   ├── 02_elo_calculator.py        # Compute dynamic historical ELO ratings
│   │   ├── 03_feature_builder.py       # Feature engineering for match prediction
│   │   ├── 04_dataset_builder.py       # Combine features into training datasets
│   │   ├── 05_model_trainer.py         # XGBoost model training and evaluation
│   │   ├── 06_calibrator.py            # Probability calibration of match outcomes
│   │   ├── 07_predictor.py             # Match winner predictor module
│   │   ├── 08_simulator.py             # Monte Carlo tournament simulator
│   │   ├── 09_bracket_engine.py        # Group stage tables and knockout logic
│   │   └── 10_leaderboard.py           # Benchmark models leaderboard
│   ├── utils/
│   │   └── team_standardizer.py        # Team name translation and normalization
│   └── tests/
│       └── test_team_standardizer.py   # Unit test suite for standardizer
├── docs/
│   └── schemas.md                      # JSON output schemas & conventions
├── frontend/                           # Vercel Next.js web application
├── requirements.txt                    # Python dependencies
└── venv/                               # Python virtual environment
```

---

## Getting Started

### 1. Installation
Clone the repository and set up the Python virtual environment:

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (cmd):
venv\Scripts\activate.bat
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run Data Cleaning & Inspection
The initial cleaning script performs comprehensive data validation and normalizes all raw datasets to a standardized team naming convention:

```cmd
python backend/scripts/01_data_cleaner.py
```

Output datasets are written to `backend/data/cleaned/` with standardized canonical team names.

---

## Team Name Standardization

To prevent discrepancies between datasets (e.g. matching `"South Korea"` in the groups with `"Korea Republic"` in the rankings), we use a JSON translation map:

*   **Mapping File**: `backend/data/team_mapping.json` maintains the single source of truth linking canonical names, FIFA 3-letter codes, friendly display names, and lists of known aliases for all 48 World Cup teams.
*   **Standardizer Helper**: `backend/utils/team_standardizer.py` converts strings to lowercase, removes accents/diacritics, strips punctuation, and maps matches to canonical forms. If a team is not mapped, it safely logs a warning and returns it as-is.

### Running Unit Tests
You can verify the team name standardization logic by running the test suite:

```cmd
python -m unittest backend/tests/test_team_standardizer.py
```

---

## JSON Schemas

Official JSON output schemas for match predictions, tournament simulation runs, and leaderboard models are documented in [schemas.md](file:///c:/Users/ADMIN/Documents/wc-pred-model/docs/schemas.md).

# Output Schemas and Team Naming Conventions

This document defines the JSON schemas for internal/external outputs and details the team naming conventions to ensure consistency across all data cleaning, training, and simulation steps.

---

## 1. JSON Output Schemas

### A. Match Prediction Output
This schema represents the predicted outcome of a single match between two teams (e.g. produced by the predictor module).

```json
{
  "team_a": "Spain",
  "team_b": "Argentina",
  "team_a_prob": 0.56,
  "draw_prob": 0.14,
  "team_b_prob": 0.30
}
```

* **`team_a` / `team_b`** (string): Standard canonical team names.
* **`team_a_prob` / `draw_prob` / `team_b_prob`** (float): Probability values in the range `[0, 1]` summing to `1.0`.

### B. Simulation Results (`outputs/simulation_results.json`)
This schema aggregates results from simulating the entire tournament (e.g., 1,000,000 runs) to predict progression probabilities.

```json
{
  "total_simulations": 1000000,
  "teams": [
    {
      "team": "Brazil",
      "win_prob": 0.173,
      "final_prob": 0.284,
      "semifinal_prob": 0.412,
      "quarterfinal_prob": 0.587
    }
  ]
}
```

* **`total_simulations`** (int): Number of simulated tournaments run.
* **`teams`** (array): List of participating teams with their probabilities of reaching specific rounds.
* **`win_prob` / `final_prob` / `semifinal_prob` / `quarterfinal_prob`** (float): Progression probabilities in the range `[0, 1]`.

### C. Leaderboard (`outputs/leaderboard.json`)
This schema catalogs internal and external prediction models for comparative benchmarking.

```json
[
  {
    "model_name": "XGBoost (Ours)",
    "accuracy": 0.52,
    "log_loss": 0.98,
    "type": "internal"
  },
  {
    "model_name": "IBM Watson",
    "accuracy": null,
    "log_loss": null,
    "source_url": "https://...",
    "type": "external"
  }
]
```

* **`model_name`** (string): The name of the model.
* **`accuracy`** (float or null): Proportion of correctly predicted match outcomes.
* **`log_loss`** (float or null): Evaluation metric (lower is better) for predicted probability distributions.
* **`type`** (string): `"internal"` (trained locally) or `"external"` (external sources/benchmarks).
* **`source_url`** (string, optional): URL reference for external models.

---

## 2. Team Naming Convention

To prevent discrepancies between datasets (e.g., `results.csv` using different spellings than `fifa-ranking.csv`), all code must adhere to the following naming conventions:

1. **Canonical Names (UTF-8)**:
   * Keep standard English names matching the main dataset, using proper accents (e.g., `"Curaçao"` instead of `"Curaþao"`, `"Côte d'Ivoire"` or `"Ivory Coast"`).
   * Canonicalize spelling variations to a single format (e.g., standardizing `"Cape Verde"` vs `"Cabo Verde"`).

2. **Standardization Mapping (FIFA Trigrams)**:
   * Maintain a mapping dictionary linking canonical names to official 3-letter FIFA trigrams (e.g., `ARG` for Argentina, `BRA` for Brazil, `USA` for United States).
   * This is used to join different datasets safely (e.g., merging FIFA rankings, historical results, and current Elo ratings).

3. **Data Cleaning Rule**:
   * Any data ingestion function in `01_data_cleaner.py` and downstream feature pipelines must apply a cleaning/mapping utility to convert raw text names to their canonical forms before computing statistics or feeding features to the model.

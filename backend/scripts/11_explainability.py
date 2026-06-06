import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Dynamically import MatchPredictor from 07_predictor.py
scripts_dir = os.path.dirname(os.path.abspath(__file__))
spec = importlib = __import__("importlib.util").util.spec_from_file_location(
    "predictor", os.path.join(scripts_dir, "07_predictor.py")
)
predictor_mod = __import__("importlib.util").util.module_from_spec(spec)
spec.loader.exec_module(predictor_mod)
MatchPredictor = predictor_mod.MatchPredictor


def explain_match_difference(team_a: str, team_b: str, predictor: MatchPredictor) -> str:
    """
    Generates a human-readable explanation of the key driver differences (Elo, Form, Attack)
    between two teams.
    """
    stats_a = predictor.get_team_features(team_a)
    stats_b = predictor.get_team_features(team_b)
    
    display_a = predictor.standardizer.get_display_name(stats_a["team"])
    display_b = predictor.standardizer.get_display_name(stats_b["team"])
    
    elo_a, elo_b = float(stats_a["elo"]), float(stats_b["elo"])
    form_a, form_b = float(stats_a["form_last_5"]), float(stats_b["form_last_5"])
    goals_a, goals_b = float(stats_a["goals_scored_10"]), float(stats_b["goals_scored_10"])
    
    # Determine who has the ELO advantage
    if elo_a >= elo_b:
        favored, underdog = display_a, display_b
        elo_adv = elo_a - elo_b
        form_diff = form_a - form_b
        attack_diff = goals_a - goals_b
    else:
        favored, underdog = display_b, display_a
        elo_adv = elo_b - elo_a
        form_diff = form_b - form_a
        attack_diff = goals_b - goals_a
        
    form_sign = "+" if form_diff >= 0 else ""
    attack_sign = "+" if attack_diff >= 0 else ""
    
    return (
        f"Why is {favored} favored against {underdog}?\n"
        f"-> Elo advantage: +{elo_adv:.1f} points\n"
        f"-> Recent form (win rate diff): {form_sign}{form_diff:.2f}\n"
        f"-> Goals scored (attack diff): {attack_sign}{attack_diff:.2f} goals/match"
    )


def main():
    print("=== Phase 11: SHAP Model Explainability Pipeline ===")
    
    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    outputs_dir = os.path.join("backend", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # 1. Load xgboost_best.pkl (raw XGBClassifier, natively supported by SHAP TreeExplainer)
    model_path = os.path.join(models_dir, "xgboost_best.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Best XGBoost model not found at {model_path}")
        
    print(f"Loading raw XGBoost model from: {model_path}...")
    model = joblib.load(model_path)
    
    # Load test set features
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    if not os.path.exists(X_test_path):
        raise FileNotFoundError(f"Test features not found at {X_test_path}")
        
    print(f"Loading test features from: {X_test_path}...")
    X_test = pd.read_csv(X_test_path)
    
    # 2. Compute SHAP values using TreeExplainer
    print("Computing SHAP values on the test set using TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Extract SHAP values for Class 0 (Home Win / Team A Win)
    # TreeExplainer on multi-class output returns a list of length 3 (one array per class)
    # or an array of shape (samples, features, classes)
    if isinstance(shap_values, list):
        shap_class_0 = shap_values[0]
    elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
        shap_class_0 = shap_values[:, :, 0]
    else:
        shap_class_0 = shap_values
        
    # 3. Generate SHAP summary plot and save to backend/outputs/shap_summary.png
    print("Generating SHAP summary plot...")
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_class_0, X_test, show=False)
    plt.title("SHAP Feature Importance (Class 0: Team A Win)", fontsize=14, pad=15)
    plt.tight_layout()
    
    plot_path = os.path.join(outputs_dir, "shap_summary.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"[SUCCESS] Saved SHAP summary plot to: {plot_path}")
    
    # 4. Save global feature importances to backend/outputs/shap_importance.json
    print("Calculating global feature importances...")
    # Calculate the mean absolute SHAP value for each feature
    mean_abs_shap = np.abs(shap_class_0).mean(axis=0)
    
    # Create sorted dict mapping feature name to importance
    importance_dict = {
        col: float(importance)
        for col, importance in zip(X_test.columns, mean_abs_shap)
    }
    # Sort by value descending
    sorted_importance = dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))
    
    importance_path = os.path.join(outputs_dir, "shap_importance.json")
    with open(importance_path, "w") as f:
        json.dump(sorted_importance, f, indent=4)
        
    print(f"[SUCCESS] Saved SHAP feature importances to: {importance_path}")
    print("\nGlobal Feature Importance Ranking (Class 0: Team A Win):")
    print("-" * 50)
    for idx, (feat, val) in enumerate(sorted_importance.items()):
        print(f"  {idx + 1:<2} | {feat:<25} | SHAP Importance: {val:.4f}")
    print("-" * 50)
    
    # 5. Initialize predictor and print human-readable explanations for test matches
    print("\nInitializing MatchPredictor for explanation test cases...")
    predictor = MatchPredictor()
    
    explanation_cases = [
        ("Brazil", "Argentina"),
        ("Spain", "Germany"),
        ("France", "Senegal")
    ]
    
    print("\nSample Match Explanations:")
    print("=" * 60)
    for team_a, team_b in explanation_cases:
        explanation = explain_match_difference(team_a, team_b, predictor)
        print(explanation)
        print("-" * 60)


if __name__ == "__main__":
    main()

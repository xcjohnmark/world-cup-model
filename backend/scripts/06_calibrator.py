import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.calibration import calibration_curve

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def compute_ece(y_true_binary: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) for a binary class indicator and its predicted probabilities.
    ECE = sum(|count_in_bin / N| * |mean_predicted - fraction_positive|) across bins
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_ids = np.digitize(y_prob, bin_edges) - 1
    # Clip indices to range [0, n_bins - 1]
    bin_ids = np.clip(bin_ids, 0, n_bins - 1)
    
    ece = 0.0
    N = len(y_true_binary)
    
    for i in range(n_bins):
        mask = bin_ids == i
        count = np.sum(mask)
        if count > 0:
            fraction_positive = np.mean(y_true_binary[mask])
            mean_predicted = np.mean(y_prob[mask])
            ece += (count / N) * abs(mean_predicted - fraction_positive)
            
    return ece


def assess_calibration() -> dict:
    """
    Assess calibration quality of the best XGBoost model on the test dataset.
    Computes calibration curve for home win class and Expected Calibration Error (ECE) for all classes.
    """
    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    
    model_path = os.path.join(models_dir, "xgboost_best.pkl")
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Best XGBoost model not found at {model_path}")
    if not os.path.exists(X_test_path) or not os.path.exists(y_test_path):
        raise FileNotFoundError("Test datasets not found.")
        
    # 1. Load best model and X_test, y_test
    print(f"Loading model from: {model_path}...")
    model = joblib.load(model_path)
    X_test = pd.read_csv(X_test_path)
    y_test = pd.read_csv(y_test_path).values.ravel().astype(int)
    
    # 2. Get predicted probabilities on test set
    proba = model.predict_proba(X_test)
    
    # 3. For the "home team wins" class (label 0):
    # — Use sklearn.calibration.calibration_curve(y_binary, proba[:, 0], n_bins=10)
    print("\n=== Calibration Curve (Class 0: Home Wins) ===")
    y_binary_0 = (y_test == 0).astype(int)
    fraction_positives, mean_predicted_values = calibration_curve(y_binary_0, proba[:, 0], n_bins=10)
    
    overconfident_bins = 0
    total_nonempty_bins = len(mean_predicted_values)
    
    for idx, (fp, mpv) in enumerate(zip(fraction_positives, mean_predicted_values)):
        print(f"  Bin {idx + 1}: Mean Predicted = {mpv:.4f}, Actual Fraction = {fp:.4f}")
        if mpv > fp:
            overconfident_bins += 1
            
    # Assess overall confidence behavior for Class 0
    # If mean_predicted_value > fraction_of_positives for most bins -> overconfident
    # If mean_predicted_value < fraction_of_positives -> underconfident
    if overconfident_bins > total_nonempty_bins / 2:
        class_0_assessment = "overconfident"
    elif overconfident_bins < total_nonempty_bins / 2:
        class_0_assessment = "underconfident"
    else:
        class_0_assessment = "well-calibrated"
        
    print(f"Class 0 (Home Wins) Assessment: {class_0_assessment} ({overconfident_bins}/{total_nonempty_bins} bins have predicted > actual)")
    
    # 4. Compute Expected Calibration Error (ECE) for each class
    ece_class_0 = compute_ece(y_binary_0, proba[:, 0], n_bins=10)
    
    y_binary_1 = (y_test == 1).astype(int)
    ece_class_1 = compute_ece(y_binary_1, proba[:, 1], n_bins=10)
    
    y_binary_2 = (y_test == 2).astype(int)
    ece_class_2 = compute_ece(y_binary_2, proba[:, 2], n_bins=10)
    
    # Average ECE across all 3 classes
    mean_ece = (ece_class_0 + ece_class_1 + ece_class_2) / 3.0
    
    print("\nExpected Calibration Error (ECE):")
    print(f"  Class 0 (Home Win): {ece_class_0:.4f}")
    print(f"  Class 1 (Draw):     {ece_class_1:.4f}")
    print(f"  Class 2 (Away Win): {ece_class_2:.4f}")
    print(f"  Mean ECE:           {mean_ece:.4f}")
    
    # 5. Print a calibration assessment: ECE threshold check
    overall_assessment = class_0_assessment
    if mean_ece < 0.015:
        overall_assessment = "well-calibrated"
        
    print(f"\nCalibration Assessment:")
    print(f"  XGBoost ECE: {mean_ece:.4f} — {overall_assessment}")
    
    return {
        "ece_class_0": ece_class_0,
        "ece_class_1": ece_class_1,
        "ece_class_2": ece_class_2,
        "mean_ece": mean_ece,
        "assessment": overall_assessment
    }


def main():
    assess_calibration()


if __name__ == "__main__":
    main()

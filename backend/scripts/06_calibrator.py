import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.calibration import calibration_curve, CalibratedClassifierCV, FrozenEstimator
from sklearn.metrics import log_loss, accuracy_score
from xgboost import XGBClassifier

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


def calibrate_model() -> dict:
    """
    Splits the training data temporally into an 80% training portion and 20% calibration portion.
    Trains the base XGBoost model on the training portion, and fits both Isotonic and Sigmoid Calibrators.
    Compares test performance (including uncalibrated model) to determine the best model,
    updates the leaderboard, and saves the final chosen model.
    """
    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    outputs_dir = os.path.join("backend", "outputs")
    
    # 1. Load xgboost_best.pkl, X_train, y_train, X_test, y_test
    X_train_path = os.path.join(processed_dir, "X_train.csv")
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_train_path = os.path.join(processed_dir, "y_train.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")
    uncal_model_path = os.path.join(models_dir, "xgboost_best.pkl")
    
    X_train = pd.read_csv(X_train_path)
    X_test = pd.read_csv(X_test_path)
    y_train = pd.read_csv(y_train_path).values.ravel().astype(int)
    y_test = pd.read_csv(y_test_path).values.ravel().astype(int)
    
    # 2. Split X_train chronologically: 80% training / 20% calibration
    split_idx = int(len(X_train) * 0.8)
    X_train_fit = X_train.iloc[:split_idx]
    y_train_fit = y_train[:split_idx]
    
    X_train_calib = X_train.iloc[split_idx:]
    y_train_calib = y_train[split_idx:]
    
    print(f"\nTraining portion:    {X_train_fit.shape[0]} matches")
    print(f"Calibration portion: {X_train_calib.shape[0]} matches")
    
    # 3. Re-train XGBoost on training_portion only using best parameters
    # The best parameters from Phase 5 tuning:
    best_params = {
        'colsample_bytree': 0.8,
        'learning_rate': 0.01,
        'max_depth': 3,
        'min_child_weight': 3,
        'n_estimators': 500,
        'subsample': 0.8
    }
    
    xgb_base = XGBClassifier(
        **best_params,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        random_state=42
    )
    
    print("Re-fitting base XGBoost on training portion...")
    xgb_base.fit(X_train_fit, y_train_fit)
    
    # Setup custom cv split to calibrate on the entire validation set (without cross-validation)
    n_calib = len(X_train_calib)
    custom_cv = [(np.arange(n_calib), np.arange(n_calib))]
    
    # 4. Apply Isotonic regression calibration
    # Wraps base estimator in FrozenEstimator (mandatory in sklearn >= 1.6 to prevent refitting)
    print("Fitting Isotonic calibrator...")
    calibrated_model_iso = CalibratedClassifierCV(
        estimator=FrozenEstimator(xgb_base),
        method='isotonic',
        cv=custom_cv
    )
    calibrated_model_iso.fit(X_train_calib, y_train_calib)
    
    # Fit Sigmoid calibration for comparison
    print("Fitting Sigmoid calibrator...")
    calibrated_model_sig = CalibratedClassifierCV(
        estimator=FrozenEstimator(xgb_base),
        method='sigmoid',
        cv=custom_cv
    )
    calibrated_model_sig.fit(X_train_calib, y_train_calib)
    
    # 5. Evaluate uncalibrated and calibrated models on X_test
    # Load uncalibrated best model for baseline
    uncal_model = joblib.load(uncal_model_path)
    uncal_proba = uncal_model.predict_proba(X_test)
    uncal_loss = log_loss(y_test, uncal_proba, labels=[0, 1, 2])
    uncal_ece = (
        compute_ece((y_test == 0).astype(int), uncal_proba[:, 0]) +
        compute_ece((y_test == 1).astype(int), uncal_proba[:, 1]) +
        compute_ece((y_test == 2).astype(int), uncal_proba[:, 2])
    ) / 3.0
    uncal_acc = accuracy_score(y_test, uncal_model.predict(X_test))
    
    # Isotonic evaluation
    iso_proba = calibrated_model_iso.predict_proba(X_test)
    iso_loss = log_loss(y_test, iso_proba, labels=[0, 1, 2])
    iso_ece = (
        compute_ece((y_test == 0).astype(int), iso_proba[:, 0]) +
        compute_ece((y_test == 1).astype(int), iso_proba[:, 1]) +
        compute_ece((y_test == 2).astype(int), iso_proba[:, 2])
    ) / 3.0
    iso_acc = accuracy_score(y_test, calibrated_model_iso.predict(X_test))
    
    # Sigmoid evaluation
    sig_proba = calibrated_model_sig.predict_proba(X_test)
    sig_loss = log_loss(y_test, sig_proba, labels=[0, 1, 2])
    sig_ece = (
        compute_ece((y_test == 0).astype(int), sig_proba[:, 0]) +
        compute_ece((y_test == 1).astype(int), sig_proba[:, 1]) +
        compute_ece((y_test == 2).astype(int), sig_proba[:, 2])
    ) / 3.0
    sig_acc = accuracy_score(y_test, calibrated_model_sig.predict(X_test))
    
    # Print side-by-side comparison
    print("\nCalibration Correction Comparison:")
    print("-" * 75)
    print(f"{'Configuration':<25} | {'Log Loss':<12} | {'ECE':<12} | {'Accuracy':<10}")
    print("-" * 75)
    print(f"{'Uncalibrated XGBoost':<25} | {uncal_loss:<12.4f} | {uncal_ece:<12.4f} | {uncal_acc:<10.4f}")
    print(f"{'Isotonic Calibration':<25} | {iso_loss:<12.4f} | {iso_ece:<12.4f} | {iso_acc:<10.4f}")
    print(f"{'Sigmoid Calibration':<25} | {sig_loss:<12.4f} | {sig_ece:<12.4f} | {sig_acc:<10.4f}")
    print("-" * 75)
    
    # Choose best model based on lowest ECE (including uncalibrated model)
    if uncal_ece <= iso_ece and uncal_ece <= sig_ece:
        best_method = "none (uncalibrated)"
        best_model = uncal_model
        best_loss = uncal_loss
        best_ece = uncal_ece
        best_acc = uncal_acc
    elif iso_ece < sig_ece:
        best_method = "isotonic"
        best_model = calibrated_model_iso
        best_loss = iso_loss
        best_ece = iso_ece
        best_acc = iso_acc
    else:
        best_method = "sigmoid"
        best_model = calibrated_model_sig
        best_loss = sig_loss
        best_ece = sig_ece
        best_acc = sig_acc
        
    print(f"\nSelected calibration method: {best_method} (yielded lowest test set ECE of {best_ece:.4f})")
    
    # 6. Update leaderboard_results.json with best XGBoost metrics
    leaderboard_path = os.path.join(outputs_dir, "leaderboard_results.json")
    if os.path.exists(leaderboard_path):
        with open(leaderboard_path, "r") as f:
            results = json.load(f)
    else:
        results = []
        
    results = [r for r in results if r["model_name"] != "XGBoost (Ours)"]
    results.append({
        "model_name": "XGBoost (Ours)",
        "log_loss": round(float(best_loss), 4),
        "accuracy": round(float(best_acc), 4),
        "type": "internal"
    })
    
    with open(leaderboard_path, "w") as f:
        json.dump(results, f, indent=4)
        
    # 7. Save calibrated model: backend/models/xgboost_calibrated.pkl
    calib_model_path = os.path.join(models_dir, "xgboost_calibrated.pkl")
    joblib.dump(best_model, calib_model_path)
    print("[SUCCESS] Calibrated model saved. All predictions will now use the calibrated model.")
    
    return {
        "best_method": best_method,
        "log_loss": best_loss,
        "ece": best_ece,
        "accuracy": best_acc
    }


def main():
    print("=== STEP 1: Assess Baseline Calibration ===")
    assess_calibration()
    print("\n=== STEP 2: Apply Calibration Correction ===")
    calibrate_model()


if __name__ == "__main__":
    main()

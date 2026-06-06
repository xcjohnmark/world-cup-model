import os
import sys
import pickle
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss, accuracy_score

# Add project root to python path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def train_baselines() -> list:
    """
    Trains and evaluates baseline and classic machine learning models:
      1. Random Baseline
      2. Elo-Only Logistic Regression (OVR)
      3. Full-Feature Logistic Regression (Multinomial)
      4. Random Forest Classifier
    Saves trained model files and initializes leaderboard results.
    """
    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    outputs_dir = os.path.join("backend", "outputs")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    
    # 1. Load splits
    X_train_path = os.path.join(processed_dir, "X_train.csv")
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_train_path = os.path.join(processed_dir, "y_train.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")
    
    for path in [X_train_path, X_test_path, y_train_path, y_test_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required split file not found at {path}")
            
    X_train = pd.read_csv(X_train_path)
    X_test = pd.read_csv(X_test_path)
    
    # Convert targets to 1D integer arrays
    y_train = pd.read_csv(y_train_path).values.ravel().astype(int)
    y_test = pd.read_csv(y_test_path).values.ravel().astype(int)
    
    results = []
    
    # 2. RANDOM BASELINE
    # Predict uniform probabilities [0.333, 0.334, 0.333] for every match
    rand_pred_proba = np.tile([0.333, 0.334, 0.333], (len(y_test), 1))
    rand_loss = log_loss(y_test, rand_pred_proba, labels=[0, 1, 2])
    # Predict argmax (class 1 for all rows, since 0.334 is the max)
    rand_pred = np.argmax(rand_pred_proba, axis=1)
    rand_acc = accuracy_score(y_test, rand_pred)
    
    results.append({
        "model_name": "Random Baseline",
        "log_loss": round(float(rand_loss), 4),
        "accuracy": round(float(rand_acc), 4),
        "type": "internal"
    })
    
    # 3. ELO-ONLY BASELINE
    # Wrap in OneVsRestClassifier to enforce OVR behavior in sklearn >= 1.5 where multi_class argument is removed
    elo_model = OneVsRestClassifier(LogisticRegression(max_iter=1000))
    elo_model.fit(X_train[["elo_diff"]], y_train)
    elo_pred_proba = elo_model.predict_proba(X_test[["elo_diff"]])
    elo_loss = log_loss(y_test, elo_pred_proba, labels=[0, 1, 2])
    elo_pred = elo_model.predict(X_test[["elo_diff"]])
    elo_acc = accuracy_score(y_test, elo_pred)
    
    results.append({
        "model_name": "Elo-Only Baseline",
        "log_loss": round(float(elo_loss), 4),
        "accuracy": round(float(elo_acc), 4),
        "type": "internal"
    })
    
    # 4. LOGISTIC REGRESSION (full features)
    # Multinomial is automatically selected for multiclass targets with solver='lbfgs' in sklearn >= 1.5
    lr_model = LogisticRegression(C=1.0, max_iter=1000, solver='lbfgs')
    lr_model.fit(X_train, y_train)
    lr_pred_proba = lr_model.predict_proba(X_test)
    lr_loss = log_loss(y_test, lr_pred_proba, labels=[0, 1, 2])
    lr_pred = lr_model.predict(X_test)
    lr_acc = accuracy_score(y_test, lr_pred)
    
    # Save model
    lr_path = os.path.join(models_dir, "logistic_regression.pkl")
    with open(lr_path, "wb") as f:
        pickle.dump(lr_model, f)
        
    results.append({
        "model_name": "Logistic Regression",
        "log_loss": round(float(lr_loss), 4),
        "accuracy": round(float(lr_acc), 4),
        "type": "internal"
    })
    
    # 5. RANDOM FOREST
    rf_model = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_pred_proba = rf_model.predict_proba(X_test)
    rf_loss = log_loss(y_test, rf_pred_proba, labels=[0, 1, 2])
    rf_pred = rf_model.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)
    
    # Save model
    rf_path = os.path.join(models_dir, "random_forest.pkl")
    with open(rf_path, "wb") as f:
        pickle.dump(rf_model, f)
        
    results.append({
        "model_name": "Random Forest",
        "log_loss": round(float(rf_loss), 4),
        "accuracy": round(float(rf_acc), 4),
        "type": "internal"
    })
    
    # 6. Print comparison table
    print("\nModel Evaluation Comparison:")
    print("-" * 55)
    print(f"{'Model':<25} | {'Log Loss':<10} | {'Accuracy':<10}")
    print("-" * 55)
    for res in results:
        print(f"{res['model_name']:<25} | {res['log_loss']:<10.4f} | {res['accuracy']:<10.4f}")
    print("-" * 55)
    
    # 7. Save to backend/outputs/leaderboard_results.json
    leaderboard_path = os.path.join(outputs_dir, "leaderboard_results.json")
    with open(leaderboard_path, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nSaved leaderboard results to: {leaderboard_path}")
    
    return results


def main():
    train_baselines()


if __name__ == "__main__":
    main()

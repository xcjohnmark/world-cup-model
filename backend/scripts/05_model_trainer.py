import os
import sys
import pickle
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import log_loss, accuracy_score
from xgboost import XGBClassifier

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
    
    # Save to backend/outputs/leaderboard_results.json
    leaderboard_path = os.path.join(outputs_dir, "leaderboard_results.json")
    with open(leaderboard_path, "w") as f:
        json.dump(results, f, indent=4)
    
    return results


def train_xgboost() -> XGBClassifier:
    """
    Trains and tunes an XGBoost model using GridSearchCV with TimeSeriesSplit.
    Retrains with early stopping and updates the leaderboard.
    """
    processed_dir = os.path.join("backend", "data", "processed")
    models_dir = os.path.join("backend", "models")
    outputs_dir = os.path.join("backend", "outputs")
    
    X_train_path = os.path.join(processed_dir, "X_train.csv")
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_train_path = os.path.join(processed_dir, "y_train.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")
    
    X_train = pd.read_csv(X_train_path)
    X_test = pd.read_csv(X_test_path)
    y_train = pd.read_csv(y_train_path).values.ravel().astype(int)
    y_test = pd.read_csv(y_test_path).values.ravel().astype(int)
    
    # 2. Define the hyperparameter search grid
    param_grid = {
        'max_depth': [3, 4, 5],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [300, 500],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0],
        'min_child_weight': [1, 3]
    }
    
    # 3. Setup GridSearchCV
    print("\nRunning hyperparameter tuning for XGBoost via GridSearchCV...")
    tscv = TimeSeriesSplit(n_splits=5)
    xgb_base = XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        random_state=42
    )
    
    grid_search = GridSearchCV(
        estimator=xgb_base,
        param_grid=param_grid,
        scoring='neg_log_loss',
        cv=tscv,
        n_jobs=-1,
        verbose=1
    )
    
    # 4. Fit GridSearchCV on X_train, y_train
    grid_search.fit(X_train, y_train)
    
    # 5. Print best parameters and cross-validation log loss
    best_params = grid_search.best_params_
    best_cv_loss = -grid_search.best_score_
    print(f"\nBest XGBoost Hyperparameters: {best_params}")
    print(f"Best CV Log Loss: {best_cv_loss:.4f}")
    
    # 6. Retrain XGBoost with best parameters on ALL of X_train (with early stopping)
    print("\nRetraining XGBoost with best parameters and early stopping...")
    best_model = XGBClassifier(
        **best_params,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        early_stopping_rounds=30,
        random_state=42
    )
    
    best_model.fit(
        X_train, 
        y_train, 
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # 7. Predict probabilities on X_test
    y_pred_proba = best_model.predict_proba(X_test)
    
    # 8. Compute final log_loss and accuracy
    xgb_loss = log_loss(y_test, y_pred_proba, labels=[0, 1, 2])
    xgb_pred = best_model.predict(X_test)
    xgb_acc = accuracy_score(y_test, xgb_pred)
    
    print(f"Final XGBoost Test Log Loss: {xgb_loss:.4f}")
    print(f"Final XGBoost Test Accuracy: {xgb_acc:.4f}")
    
    # 10. Save model using joblib.dump()
    xgboost_path = os.path.join(models_dir, "xgboost_best.pkl")
    joblib.dump(best_model, xgboost_path)
    print(f"Saved best XGBoost model to: {xgboost_path}")
    
    # 11. Add XGBoost results to leaderboard_results.json
    leaderboard_path = os.path.join(outputs_dir, "leaderboard_results.json")
    if os.path.exists(leaderboard_path):
        with open(leaderboard_path, "r") as f:
            results = json.load(f)
    else:
        results = []
        
    # Remove existing XGBoost (Ours) row to prevent duplicates
    results = [r for r in results if r["model_name"] != "XGBoost (Ours)"]
    results.append({
        "model_name": "XGBoost (Ours)",
        "log_loss": round(float(xgb_loss), 4),
        "accuracy": round(float(xgb_acc), 4),
        "type": "internal"
    })
    
    # Save updated leaderboard
    with open(leaderboard_path, "w") as f:
        json.dump(results, f, indent=4)
        
    # 9. Print comparison table
    print("\nModel Evaluation Comparison (Including XGBoost):")
    print("-" * 55)
    print(f"{'Model':<25} | {'Log Loss':<10} | {'Accuracy':<10}")
    print("-" * 55)
    for res in results:
        print(f"{res['model_name']:<25} | {res['log_loss']:<10.4f} | {res['accuracy']:<10.4f}")
    print("-" * 55)
    
    return best_model


def main():
    train_baselines()
    train_xgboost()


if __name__ == "__main__":
    main()

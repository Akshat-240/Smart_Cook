"""
SmartCook - Model Training
Trains a Linear Regression model to predict daily meal headcount.
Saves trained model as model/smartcook_model.pkl
"""

import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader.load_kaggle import load_mess_data
from analytics.features import build_features, get_feature_stats

MODEL_DIR   = Path(__file__).parent
MODEL_PATH  = MODEL_DIR / "smartcook_model.pkl"
SCALER_PATH = MODEL_DIR / "smartcook_scaler.pkl"
EVAL_PATH   = MODEL_DIR / "evaluation.txt"


def train():
    print("=" * 50)
    print("SmartCook - Model Training")
    print("=" * 50)

    # 1. Load data
    df = load_mess_data()
    print("\n[1] Loaded {} rows".format(len(df)))

    # 2. Feature stats
    stats = get_feature_stats(df)
    print("\n[2] Per-meal baseline headcounts:")
    for meal, s in stats.items():
        print("    {}: mean={}, std={}".format(meal, s["mean"], s["std"]))

    # 3. Build features
    X, y, feature_names = build_features(df)

    # 4. Train/test split 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print("\n[3] Train: {} rows | Test: {} rows".format(len(X_train), len(X_test)))

    # 5. Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # 6. Train model
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    print("\n[4] Model trained")

    # 7. Evaluate
    y_pred = model.predict(X_test_scaled)
    r2   = round(r2_score(y_test, y_pred), 4)
    rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2)
    mae  = round(float(np.mean(np.abs(y_pred - y_test))), 2)

    print("\n[5] Evaluation Results:")
    print("    R2 Score : {}  (1.0 = perfect)".format(r2))
    print("    RMSE     : {} students".format(rmse))
    print("    MAE      : {} students".format(mae))

    # 8. Feature coefficients
    print("\n[6] Feature Coefficients:")
    for name, coef in zip(feature_names, model.coef_):
        print("    {:<20} {:>10}".format(name, round(coef, 4)))
    print("    {:<20} {:>10}".format("intercept", round(float(model.intercept_), 4)))

    # 9. Save model + scaler
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("\n[7] Model saved  -> {}".format(MODEL_PATH))
    print("    Scaler saved -> {}".format(SCALER_PATH))

    # 10. Save evaluation report
    report = "SmartCook - Model Evaluation Report\n"
    report += "=====================================\n"
    report += "Training rows : {}\n".format(len(X_train))
    report += "Test rows     : {}\n".format(len(X_test))
    report += "Features      : {}\n\n".format(feature_names)
    report += "Results\n-------\n"
    report += "R2 Score : {}\n".format(r2)
    report += "RMSE     : {} students\n".format(rmse)
    report += "MAE      : {} students\n\n".format(mae)
    report += "Feature Coefficients\n--------------------\n"
    for name, coef in zip(feature_names, model.coef_):
        report += "  {:<20} {}\n".format(name, round(coef, 4))
    report += "  {:<20} {}\n".format("intercept", round(float(model.intercept_), 4))

    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print("    Evaluation  -> {}".format(EVAL_PATH))
    print("\nTraining complete!")
    return model, scaler


if __name__ == "__main__":
    train()

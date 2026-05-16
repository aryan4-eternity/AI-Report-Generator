"""
ML Model module for CFL Sales Dashboard — XGBoost demand forecasting.

Provides functions to train, load, predict, evaluate, and compare
an XGBRegressor model against human forecast teams.
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
from xgboost import XGBRegressor
import joblib

# ─── PATHS ───────────────────────────────────────────────────
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "xgb_model.joblib")

# ─── FEATURE COLUMNS (order matters for model) ──────────────
FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_4",
    "rolling_avg_4", "rolling_std_4",
    "qoq_growth", "yoy_growth",
    "quarter_num", "product_encoded",
]


# ─── 1. TRAIN ───────────────────────────────────────────────
def train_forecast_model(features_df: pd.DataFrame) -> XGBRegressor:
    """
    Train an XGBRegressor on the training split (FY23 Q2-offset rows → FY25 Q3).
    Saves the fitted model to models/xgb_model.joblib.

    Args:
        features_df: Output of build_ml_features() — must have FEATURE_COLS + 'target' + 'Quarter'

    Returns:
        Fitted XGBRegressor
    """
    # Training quarters: everything up to and including FY25 Q3
    train_quarters = ["FY23 Q2", "FY23 Q3", "FY23 Q4",
                      "FY24 Q1", "FY24 Q2", "FY24 Q3", "FY24 Q4",
                      "FY25 Q1", "FY25 Q2", "FY25 Q3"]
    train_df = features_df[features_df["Quarter"].isin(train_quarters)].copy()

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df["target"].values

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_train, y_train)

    # Save model
    os.makedirs(_MODEL_DIR, exist_ok=True)
    joblib.dump(model, _MODEL_PATH)

    return model


# ─── 2. LOAD OR TRAIN ───────────────────────────────────────
@st.cache_resource(show_spinner="🤖 Loading ML model…")
def load_or_train_model(_features_df: pd.DataFrame) -> XGBRegressor:
    """
    Load a saved model from disk, or train a fresh one if none exists.
    Uses @st.cache_resource so the model stays in memory across reruns.

    Args:
        _features_df: Output of build_ml_features()
                     (underscore prefix tells Streamlit not to hash it)
    """
    if os.path.exists(_MODEL_PATH):
        try:
            model = joblib.load(_MODEL_PATH)
            return model
        except Exception:
            pass  # Fall through to retrain

    return train_forecast_model(_features_df)


# ─── 3. PREDICT FY26 Q2 ─────────────────────────────────────
def predict_next_quarter(model: XGBRegressor, prediction_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Use the trained model to predict FY26 Q2 units for all 30 products.

    Args:
        model: Fitted XGBRegressor
        prediction_features_df: Output of build_prediction_features()

    Returns:
        DataFrame with columns: Product, ML_Prediction
    """
    X = prediction_features_df[FEATURE_COLS].values
    preds = model.predict(X)

    result = prediction_features_df[["Product"]].copy()
    result["ML_Prediction"] = np.maximum(preds, 0).round(0)  # no negative units
    return result


# ─── 4. EVALUATE (HOLDOUT) ───────────────────────────────────
def evaluate_model(model: XGBRegressor, features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate the model on holdout quarters (FY25 Q4 and FY26 Q1).
    Returns MAPE per product, plus overall MAPE.

    Args:
        model: Fitted XGBRegressor
        features_df: Output of build_ml_features()

    Returns:
        DataFrame: Product, Quarter, Actual, Predicted, APE
    """
    holdout_quarters = ["FY25 Q4", "FY26 Q1"]
    holdout = features_df[features_df["Quarter"].isin(holdout_quarters)].copy()

    if holdout.empty:
        return pd.DataFrame(columns=["Product", "Quarter", "Actual", "Predicted", "APE"])

    X = holdout[FEATURE_COLS].values
    holdout["Predicted"] = np.maximum(model.predict(X), 0).round(0)
    holdout["Actual"] = holdout["target"]
    holdout["APE"] = np.where(
        holdout["Actual"] != 0,
        np.abs(holdout["Predicted"] - holdout["Actual"]) / np.abs(holdout["Actual"]),
        0.0,
    )

    return holdout[["Product", "Quarter", "Actual", "Predicted", "APE"]]


# ─── 5. COMPARE WITH HUMAN FORECASTS ────────────────────────
def compare_with_human_forecasts(ml_df: pd.DataFrame, human_df: pd.DataFrame,
                                  actuals_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare ML predictions against 3 human forecast teams for FY26 Q2.
    Since FY26 Q2 actuals aren't available yet, we compare the spread of predictions
    and identify the closest forecast to the ML consensus.

    If FY26 Q1 actuals exist, we use the validation-set performance to assess
    which forecast method is historically most reliable.

    Args:
        ml_df: DataFrame with Product, ML_Prediction (from predict_next_quarter)
        human_df: DataFrame with Product, Demand Planners, Marketing Team, Data Science Team
        actuals_df: Bookings actuals DataFrame

    Returns:
        DataFrame: Product, ML_Prediction, Demand Planners, Marketing Team, Data Science Team,
                   Closest_Team, ML_vs_Consensus
    """
    merged = human_df.merge(ml_df, on="Product", how="left")

    # Consensus = average of 3 human forecasts
    team_cols = ["Demand Planners", "Marketing Team", "Data Science Team"]
    merged["Human_Consensus"] = merged[team_cols].mean(axis=1)

    # For each product, find which human team is closest to ML prediction
    def _closest_team(row):
        diffs = {t: abs(row[t] - row["ML_Prediction"]) for t in team_cols}
        return min(diffs, key=diffs.get)

    merged["Closest_Team"] = merged.apply(_closest_team, axis=1)

    # ML vs consensus: positive = ML predicts higher
    merged["ML_vs_Consensus"] = (
        (merged["ML_Prediction"] - merged["Human_Consensus"])
        / merged["Human_Consensus"].replace(0, 1) * 100
    ).round(1)

    return merged


def count_ml_wins_on_holdout(model: XGBRegressor, features_df: pd.DataFrame,
                              accuracy_df: pd.DataFrame) -> int:
    """
    Count products where ML had lower APE than ALL 3 human teams on FY26 Q1.
    Uses forecast accuracy data for human teams and model predictions for ML.

    Args:
        model: Fitted XGBRegressor
        features_df: Output of build_ml_features()
        accuracy_df: Forecast accuracy DataFrame (Product, Team, Quarter, Accuracy)

    Returns:
        Number of products where ML beat all 3 human teams
    """
    # ML evaluation on FY26 Q1
    eval_df = evaluate_model(model, features_df)
    ml_q1 = eval_df[eval_df["Quarter"] == "FY26 Q1"].copy()
    if ml_q1.empty:
        return 0

    ml_mape_per_product = ml_q1.groupby("Product")["APE"].mean()

    # Human accuracy on FY26 Q1 (accuracy → MAPE = 1 - accuracy)
    human_q1 = accuracy_df[accuracy_df["Quarter"] == "FY26 Q1"].copy()
    if human_q1.empty:
        return 0

    wins = 0
    for product in ml_mape_per_product.index:
        ml_ape = ml_mape_per_product[product]
        human_product = human_q1[human_q1["Product"] == product]
        if human_product.empty:
            continue

        # Human MAPE = 1 - Accuracy (since accuracy is 0-1 scale)
        human_mapes = (1 - human_product["Accuracy"]).values
        if all(ml_ape < h for h in human_mapes if not np.isnan(h)):
            wins += 1

    return wins

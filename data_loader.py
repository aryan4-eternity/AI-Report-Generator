"""
Data loader module for CFL Sales Dashboard.
Parses the multi-sheet Excel file with merged headers into clean DataFrames.
All functions use @st.cache_data for efficient caching.

Excel structure (verified against actual file):
- Data Pack - Actual Bookings:
    Row 0: header labels (Cost Rank, Product Name, Product Life Cycle, ACTUAL UNITS, ..., Forecasted Units)
    Row 1: blank
    Row 2: quarter labels (FY23 Q2 ... FY26 Q1, FY26 Q2)
    Rows 3-32: 30 products
      Col 0 = Cost Rank, Col 1 = Product Name, Col 2 = Lifecycle
      Cols 3-14 = 12 actual quarters (FY23 Q2 to FY26 Q1)
      Col 15 = FY26 Q2 actual (blank/nan)
      Cols 16-18 = 3 forecast team targets for FY26 Q2
    Rows 35-37: accuracy section headers
      Row 35: team names in cols 2, 9, 16
      Row 36: quarter labels (FY2026 Q1, FY2025 Q4, FY2025 Q3) per team
      Row 37: Accuracy/BIAS labels
    Rows 38-67: 30 products accuracy data
      Col 0 = Rank, Col 1 = Product Name
      Per team block (Demand=cols 2-8, Marketing=cols 9-15, DataSci=cols 16-21):
        Each quarter = 2 cols: [Accuracy, BIAS], with blank separator cols

- Big Deal:
    Row 0-1: headers
    Rows 2-31: 30 products
    Col 0 = Rank, Col 1 = Product
    Cols 2-9 = MFG Book Units (8 quarters: 2024Q2 to 2026Q1)
    Cols 10-17 = Big Deals
    Cols 18-25 = Avg Deals

- SCMS:
    Row 0-2: headers
    Rows 3+: data (each product has 6 rows, one per segment)
    Col 0 = Rank, Col 1 = Product, Col 2 = Segment
    Cols 3-15 = 13 quarters (2023Q1 to 2026Q1)

- VMS:
    Row 0-2: headers
    Rows 3+: data (each product has ~15 rows, one per vertical)
    Col 0 = Rank, Col 1 = Product, Col 2 = Vertical
    Cols 3-15 = 13 quarters (2023Q1 to 2026Q1)
"""

import pandas as pd
import numpy as np
import streamlit as st
from config import (
    FILE_PATH,
    QUARTER_LABELS,
    ACCURACY_QUARTERS,
    FORECAST_TEAMS,
    BIG_DEAL_QUARTERS,
    SCMS_QUARTERS,
    SEGMENTS,
)


def _read_sheet_raw(sheet_name: str) -> pd.DataFrame:
    """Read a sheet with no header inference (header=None) to handle merged cells."""
    return pd.read_excel(FILE_PATH, sheet_name=sheet_name, header=None)


# ─── 1. ACTUAL BOOKINGS ─────────────────────────────────────
@st.cache_data(show_spinner="Loading bookings data…")
def load_bookings_actuals() -> pd.DataFrame:
    """
    Returns DataFrame with columns: Product, FY23 Q2, …, FY26 Q1
    30 products × 12 quarters of actual booking units.
    """
    raw = _read_sheet_raw("Data Pack - Actual Bookings")

    products = []
    actuals = []

    # Data rows are 3 to 32 (30 products)
    for i in range(3, 33):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not product_name:
            continue

        # Cols 3-14 = 12 actual quarters
        quarter_vals = []
        for j in range(3, 15):
            v = row.iloc[j]
            quarter_vals.append(float(v) if pd.notna(v) else 0.0)

        products.append(product_name)
        actuals.append(quarter_vals)

    df = pd.DataFrame(actuals, columns=QUARTER_LABELS)
    df.insert(0, "Product", products)
    return df


# ─── 2. FORECAST TARGETS ────────────────────────────────────
@st.cache_data(show_spinner="Loading forecast targets…")
def load_forecast_targets() -> pd.DataFrame:
    """
    Returns DataFrame with columns: Product, Demand Planners, Marketing Team, Data Science Team
    FY26 Q2 forecast values from each team.
    """
    raw = _read_sheet_raw("Data Pack - Actual Bookings")

    products = []
    forecasts = []

    for i in range(3, 33):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not product_name:
            continue

        # Cols 16, 17, 18 = 3 forecast team targets for FY26 Q2
        team_vals = []
        for j in [16, 17, 18]:
            v = row.iloc[j] if j < len(row) else np.nan
            team_vals.append(float(v) if pd.notna(v) else 0.0)

        products.append(product_name)
        forecasts.append(team_vals)

    df = pd.DataFrame(forecasts, columns=FORECAST_TEAMS)
    df.insert(0, "Product", products)
    return df


# ─── 3. FORECAST ACCURACY & BIAS ────────────────────────────
@st.cache_data(show_spinner="Loading forecast accuracy…")
def load_forecast_accuracy() -> pd.DataFrame:
    """
    Returns long-format DataFrame: Product, Team, Quarter, Accuracy, Bias
    3 teams × 3 quarters × 30 products.

    Column layout per team (verified):
    Demand Planning Team: cols 2-7 → [FY26Q1 Acc, FY26Q1 Bias, FY25Q4 Acc, FY25Q4 Bias, FY25Q3 Acc, FY25Q3 Bias]
    (col 8 = blank separator)
    Marketing Team: cols 9-14 → same pattern
    (col 15 = blank separator)
    Data Science Team: cols 16-21 → same pattern

    Quarters order in sheet: FY2026 Q1, FY2025 Q4, FY2025 Q3
    Mapped to: FY26 Q1, FY25 Q4, FY25 Q3
    """
    raw = _read_sheet_raw("Data Pack - Actual Bookings")

    # Team column offsets: each team has 6 data columns (3 quarters × [Accuracy, Bias])
    team_col_starts = {
        "Demand Planners": 2,
        "Marketing Team": 9,
        "Data Science Team": 16,
    }

    # Quarter order in the sheet (matches ACCURACY_QUARTERS reversed)
    quarter_order = ["FY26 Q1", "FY25 Q4", "FY25 Q3"]

    records = []

    # Accuracy data rows: 38 to 67 (30 products)
    for i in range(38, 68):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not product_name:
            continue

        for team, start_col in team_col_starts.items():
            for q_idx, quarter in enumerate(quarter_order):
                acc_col = start_col + (q_idx * 2)
                bias_col = start_col + (q_idx * 2) + 1

                acc_val = row.iloc[acc_col] if acc_col < len(row) and pd.notna(row.iloc[acc_col]) else np.nan
                bias_val = row.iloc[bias_col] if bias_col < len(row) and pd.notna(row.iloc[bias_col]) else np.nan

                try:
                    acc_val = float(acc_val)
                except (ValueError, TypeError):
                    acc_val = np.nan

                try:
                    bias_val = float(bias_val)
                except (ValueError, TypeError):
                    bias_val = np.nan

                records.append({
                    "Product": product_name,
                    "Team": team,
                    "Quarter": quarter,
                    "Accuracy": acc_val,
                    "Bias": bias_val,
                })

    return pd.DataFrame(records)


# ─── 4. SCMS (Segment Data) ─────────────────────────────────
@st.cache_data(show_spinner="Loading segment data…")
def load_scms() -> pd.DataFrame:
    """
    Returns long-format DataFrame: Product, Segment, Quarter, Units
    Each product has 6 segment rows × 13 quarters.

    Col 0 = Cost Rank, Col 1 = Product (masked name), Col 2 = Segment,
    Cols 3-15 = 13 quarters (2023Q1 to 2026Q1)
    Data starts at row 3.
    """
    raw = _read_sheet_raw("SCMS")

    records = []

    for i in range(3, len(raw)):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        segment = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""

        if not product_name or not segment:
            continue

        for q_idx, quarter in enumerate(SCMS_QUARTERS):
            col = 3 + q_idx
            v = row.iloc[col] if col < len(row) else 0.0
            try:
                units = float(v) if pd.notna(v) else 0.0
            except (ValueError, TypeError):
                units = 0.0

            records.append({
                "Product": product_name,
                "Segment": segment.upper(),
                "Quarter": quarter,
                "Units": units,
            })

    return pd.DataFrame(records)


# ─── 5. VMS (Vertical / Industry Data) ──────────────────────
@st.cache_data(show_spinner="Loading vertical data…")
def load_vms() -> pd.DataFrame:
    """
    Returns long-format DataFrame: Product, Vertical, Quarter, Units
    Each product has ~15 vertical rows × 13 quarters.

    Col 0 = Cost Rank, Col 1 = Product, Col 2 = Vertical,
    Cols 3-15 = 13 quarters (2023Q1 to 2026Q1)
    Data starts at row 3.
    """
    raw = _read_sheet_raw("VMS")

    records = []

    for i in range(3, len(raw)):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        vertical = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""

        if not product_name or not vertical:
            continue

        for q_idx, quarter in enumerate(SCMS_QUARTERS):
            col = 3 + q_idx
            v = row.iloc[col] if col < len(row) else 0.0
            try:
                units = float(v) if pd.notna(v) else 0.0
            except (ValueError, TypeError):
                units = 0.0

            records.append({
                "Product": product_name,
                "Vertical": vertical,
                "Quarter": quarter,
                "Units": units,
            })

    return pd.DataFrame(records)


# ─── 6. BIG DEALS ───────────────────────────────────────────
@st.cache_data(show_spinner="Loading big deal data…")
def load_big_deals() -> pd.DataFrame:
    """
    Returns long-format DataFrame: Product, Quarter, MFG_Units, Big_Deals, Avg_Deals
    30 products × 8 quarters.

    Col 0 = Rank, Col 1 = Product
    Cols 2-9 = MFG Book Units (8 quarters: 2024Q2 to 2026Q1)
    Cols 10-17 = Big Deals
    Cols 18-25 = Avg Deals
    Data starts at row 2.
    """
    raw = _read_sheet_raw("Big Deal")

    records = []

    for i in range(2, len(raw)):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not product_name or product_name.lower() in ("nan", ""):
            continue

        for q_idx, quarter in enumerate(BIG_DEAL_QUARTERS):
            mfg_col = 2 + q_idx
            big_col = 10 + q_idx
            avg_col = 18 + q_idx

            def safe_float(c):
                v = row.iloc[c] if c < len(row) else 0.0
                try:
                    return float(v) if pd.notna(v) else 0.0
                except (ValueError, TypeError):
                    return 0.0

            records.append({
                "Product": product_name,
                "Quarter": quarter,
                "MFG_Units": safe_float(mfg_col),
                "Big_Deals": safe_float(big_col),
                "Avg_Deals": safe_float(avg_col),
            })

    return pd.DataFrame(records)


# ─── 7. PRODUCT METADATA ────────────────────────────────────
@st.cache_data(show_spinner="Loading product metadata…")
def load_product_metadata() -> pd.DataFrame:
    """
    Returns DataFrame: Product, Lifecycle, Cost_Rank, Description
    Col 0 = Cost Rank, Col 1 = Product Name, Col 2 = Lifecycle
    """
    raw = _read_sheet_raw("Data Pack - Actual Bookings")

    products = []
    lifecycles = []
    ranks = []

    for i in range(3, 33):
        row = raw.iloc[i]
        product_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        lifecycle = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "Unknown"
        rank = int(row.iloc[0]) if pd.notna(row.iloc[0]) else i - 2

        if product_name:
            products.append(product_name)
            lifecycles.append(lifecycle)
            ranks.append(rank)

    df = pd.DataFrame({
        "Product": products,
        "Lifecycle": lifecycles,
        "Cost_Rank": ranks,
    })

    # Enrich with descriptions from Masked Product Insights
    try:
        insights = pd.read_excel(FILE_PATH, sheet_name="Masked Product Insights ")
        if not insights.empty:
            cols = insights.columns.tolist()
            insights_map = dict(
                zip(
                    insights.iloc[:, 0].astype(str).str.strip(),
                    insights.iloc[:, 1].astype(str),
                )
            )
            df["Description"] = df["Product"].map(insights_map).fillna("")
    except Exception:
        df["Description"] = ""

    return df


# ─── 8. ML FEATURE ENGINEERING ───────────────────────────────
@st.cache_data(show_spinner="Building ML features…")
def build_ml_features() -> pd.DataFrame:
    """
    Build a feature DataFrame from historical bookings for ML model training.

    For each product-quarter combination (where enough history exists), creates:
        lag_1 .. lag_4   — units from the prior 1–4 quarters
        rolling_avg_4    — mean of last 4 quarters
        rolling_std_4    — std  of last 4 quarters
        qoq_growth       — quarter-over-quarter growth rate
        yoy_growth        — year-over-year growth rate (lag_4 → current)
        quarter_num      — 1-4 for seasonality encoding
        product_encoded  — label-encoded product name
        target           — actual units for the row's quarter

    Returns:
        pd.DataFrame with columns:
            Product, Quarter, lag_1..lag_4, rolling_avg_4, rolling_std_4,
            qoq_growth, yoy_growth, quarter_num, product_encoded, target
    """
    bookings = load_bookings_actuals()          # Product × 12 quarter columns
    quarter_cols = [c for c in bookings.columns if c != "Product"]
    products = bookings["Product"].tolist()

    # Label-encode products (stable alphabetical order)
    sorted_products = sorted(products)
    product_label_map = {p: idx for idx, p in enumerate(sorted_products)}

    # Quarter number extraction helper  (e.g. "FY25 Q3" → 3)
    def _quarter_num(q: str) -> int:
        try:
            return int(q.strip()[-1])
        except (ValueError, IndexError):
            return 0

    records = []
    for _, row in bookings.iterrows():
        product = row["Product"]
        vals = [row[q] for q in quarter_cols]          # ordered time-series

        for i in range(4, len(vals)):                   # need 4 lags minimum
            target = vals[i]
            lag_1 = vals[i - 1]
            lag_2 = vals[i - 2]
            lag_3 = vals[i - 3]
            lag_4 = vals[i - 4]

            window = vals[i - 4 : i]
            rolling_avg = np.mean(window)
            rolling_std = np.std(window, ddof=0)        # population std

            qoq = (lag_1 - lag_2) / lag_2 if lag_2 != 0 else 0.0
            yoy = (lag_1 - lag_4) / lag_4 if lag_4 != 0 else 0.0

            records.append({
                "Product":        product,
                "Quarter":        quarter_cols[i],
                "lag_1":          lag_1,
                "lag_2":          lag_2,
                "lag_3":          lag_3,
                "lag_4":          lag_4,
                "rolling_avg_4":  rolling_avg,
                "rolling_std_4":  rolling_std,
                "qoq_growth":     qoq,
                "yoy_growth":     yoy,
                "quarter_num":    _quarter_num(quarter_cols[i]),
                "product_encoded": product_label_map[product],
                "target":         target,
            })

    return pd.DataFrame(records)


@st.cache_data(show_spinner="Building FY26 Q2 prediction features…")
def build_prediction_features() -> pd.DataFrame:
    """
    Build the feature row for each product to predict FY26 Q2.
    Uses FY25 Q2 .. FY26 Q1 (the last 4 known quarters) as lags.
    """
    bookings = load_bookings_actuals()
    quarter_cols = [c for c in bookings.columns if c != "Product"]
    products = bookings["Product"].tolist()
    sorted_products = sorted(products)
    product_label_map = {p: idx for idx, p in enumerate(sorted_products)}

    records = []
    for _, row in bookings.iterrows():
        product = row["Product"]
        vals = [row[q] for q in quarter_cols]

        # Last 4 quarters are lags for predicting the next one (FY26 Q2)
        lag_1 = vals[-1]   # FY26 Q1
        lag_2 = vals[-2]   # FY25 Q4
        lag_3 = vals[-3]   # FY25 Q3
        lag_4 = vals[-4]   # FY25 Q2

        window = vals[-4:]
        rolling_avg = np.mean(window)
        rolling_std = np.std(window, ddof=0)
        qoq = (lag_1 - lag_2) / lag_2 if lag_2 != 0 else 0.0
        yoy = (lag_1 - lag_4) / lag_4 if lag_4 != 0 else 0.0

        records.append({
            "Product":         product,
            "Quarter":         "FY26 Q2",
            "lag_1":           lag_1,
            "lag_2":           lag_2,
            "lag_3":           lag_3,
            "lag_4":           lag_4,
            "rolling_avg_4":   rolling_avg,
            "rolling_std_4":   rolling_std,
            "qoq_growth":      qoq,
            "yoy_growth":      yoy,
            "quarter_num":     2,                      # Q2
            "product_encoded": product_label_map[product],
        })

    return pd.DataFrame(records)


# ─── CONVENIENCE: Load all data at once ─────────────────────
@st.cache_data(show_spinner="Loading all dashboard data…")
def load_all_data() -> dict:
    """Load all datasets and return as a dictionary."""
    return {
        "bookings": load_bookings_actuals(),
        "forecast_targets": load_forecast_targets(),
        "forecast_accuracy": load_forecast_accuracy(),
        "scms": load_scms(),
        "vms": load_vms(),
        "big_deals": load_big_deals(),
        "metadata": load_product_metadata(),
    }

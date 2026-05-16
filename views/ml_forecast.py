"""
Page 7 — ML Forecasting
XGBoost demand forecasting: train on historical actuals, validate on holdout,
predict FY26 Q2, and compare against 3 human forecast teams.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from components.kpi_cards import render_kpi_row, render_section_header
from components.ai_engine import get_ml_forecast_analysis
from config import PLOTLY_TEMPLATE, PLOTLY_FONT, PLOTLY_MARGIN
from data_loader import build_ml_features, build_prediction_features
from ml_model import (
    load_or_train_model,
    predict_next_quarter,
    evaluate_model,
    compare_with_human_forecasts,
    count_ml_wins_on_holdout,
    FEATURE_COLS,
)


def _base_layout(fig, title: str = "", height: int = 450):
    """Apply consistent layout to charts."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        font=PLOTLY_FONT,
        title=dict(text=title, font=dict(size=16, color="#1a1a2e")),
        margin=PLOTLY_MARGIN,
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
    )
    return fig


# ─── COLOR CONSTANTS ─────────────────────────────────────────
ML_PURPLE = "#9B59B6"
DEMAND_BLUE = "#378ADD"
MARKETING_AMBER = "#EF9F27"
DS_TEAL = "#1D9E75"


def render(data: dict):
    """Render the ML Forecasting page."""

    render_section_header(
        "🤖 ML Forecasting",
        "XGBoost demand predictions vs. human forecast teams"
    )

    # ─── LOAD / TRAIN MODEL ──────────────────────────────────
    with st.spinner("Building features & training model…"):
        features_df = build_ml_features()
        pred_features = build_prediction_features()
        model = load_or_train_model(features_df)

    # ─── PREDICTIONS & EVALUATION ────────────────────────────
    ml_predictions = predict_next_quarter(model, pred_features)
    eval_df = evaluate_model(model, features_df)
    forecast_targets = data["forecast_targets"]
    accuracy_df = data["forecast_accuracy"]

    comparison_df = compare_with_human_forecasts(
        ml_predictions, forecast_targets, data["bookings"]
    )

    # ─── KPI CALCULATIONS ────────────────────────────────────
    overall_mape = eval_df["APE"].mean() * 100 if not eval_df.empty else 0.0

    # Best predicted product (lowest APE on holdout)
    if not eval_df.empty:
        product_mape = eval_df.groupby("Product")["APE"].mean()
        best_product = product_mape.idxmin()
        best_mape = product_mape.min() * 100
    else:
        best_product = "N/A"
        best_mape = 0.0

    # Count where ML beats all 3 human teams on holdout
    ml_wins = count_ml_wins_on_holdout(model, features_df, accuracy_df)

    # ─── KPI ROW ─────────────────────────────────────────────
    render_kpi_row([
        {
            "label": "ML Model MAPE",
            "value": f"{overall_mape:.1f}%",
            "icon": "📉",
            "delta": "On validation set",
            "delta_color": ML_PURPLE,
        },
        {
            "label": "Best Predicted Product",
            "value": best_product[:22] + "…" if len(best_product) > 22 else best_product,
            "icon": "🏆",
            "delta": f"MAPE: {best_mape:.1f}%",
            "delta_color": DS_TEAL,
        },
        {
            "label": "ML Beats All Teams",
            "value": f"{ml_wins} / 30",
            "icon": "🥇",
            "delta": "Products on FY26 Q1",
            "delta_color": DEMAND_BLUE,
        },
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════
    # CHART 1: Grouped Bar — FY26 Q2 Predictions (4 bars/product)
    # ═════════════════════════════════════════════════════════
    st.subheader("FY26 Q2 Forecast Comparison")
    st.caption("XGBoost prediction vs. 3 human forecast teams for every product")

    # Build chart data
    chart1_df = comparison_df[["Product", "ML_Prediction",
                                "Demand Planners", "Marketing Team",
                                "Data Science Team"]].copy()
    chart1_df["Product_Short"] = chart1_df["Product"].apply(
        lambda x: x[:18] + "…" if len(x) > 18 else x
    )

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=chart1_df["Product_Short"], y=chart1_df["ML_Prediction"],
        name="XGBoost ML", marker_color=ML_PURPLE,
    ))
    fig1.add_trace(go.Bar(
        x=chart1_df["Product_Short"], y=chart1_df["Demand Planners"],
        name="Demand Planners", marker_color=DEMAND_BLUE,
    ))
    fig1.add_trace(go.Bar(
        x=chart1_df["Product_Short"], y=chart1_df["Marketing Team"],
        name="Marketing Team", marker_color=MARKETING_AMBER,
    ))
    fig1.add_trace(go.Bar(
        x=chart1_df["Product_Short"], y=chart1_df["Data Science Team"],
        name="Data Science Team", marker_color=DS_TEAL,
    ))
    fig1.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
        yaxis_title="Predicted Units",
    )
    _base_layout(fig1, "FY26 Q2 Predictions — ML vs. Human Teams", height=520)
    st.plotly_chart(fig1, width='stretch', key="ml_grouped_bar")

    # ═════════════════════════════════════════════════════════
    # CHART 2: Line — Actual vs Predicted on Holdout
    # ═════════════════════════════════════════════════════════
    st.subheader("Holdout Validation — Actual vs. Predicted")

    if not eval_df.empty:
        # Product selector in sidebar
        with st.sidebar:
            st.markdown("### 🔍 ML Product Selector")
            products_list = sorted(eval_df["Product"].unique().tolist())
            selected_product = st.selectbox(
                "Select product for validation chart",
                products_list,
                index=0,
                key="ml_product_selector",
            )

        product_eval = eval_df[eval_df["Product"] == selected_product]
        product_mape_val = product_eval["APE"].mean() * 100

        # Show MAPE above chart
        st.markdown(
            f'<div style="background: linear-gradient(135deg, rgba(155,89,182,0.08) 0%, rgba(55,138,221,0.08) 100%); '
            f'border: 1px solid rgba(155,89,182,0.25); border-radius: 12px; padding: 0.8rem 1.2rem; '
            f'margin-bottom: 0.8rem; display: inline-block;">'
            f'<span style="font-size: 0.8rem; color: #6b7689; text-transform: uppercase; letter-spacing: 1px;">'
            f'Model MAPE for {selected_product}</span><br>'
            f'<span style="font-size: 1.4rem; font-weight: 700; color: {ML_PURPLE};">{product_mape_val:.1f}%</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=product_eval["Quarter"], y=product_eval["Actual"],
            mode="lines+markers", name="Actual",
            line=dict(color="#1e1e1e", width=3),
            marker=dict(size=9, symbol="circle"),
        ))
        fig2.add_trace(go.Scatter(
            x=product_eval["Quarter"], y=product_eval["Predicted"],
            mode="lines+markers", name="XGBoost Predicted",
            line=dict(color=ML_PURPLE, width=3, dash="dash"),
            marker=dict(size=9, symbol="diamond"),
        ))
        fig2.update_layout(yaxis_title="Units")
        _base_layout(fig2, f"Holdout Validation — {selected_product}", height=420)
        st.plotly_chart(fig2, width='stretch', key="ml_validation_line")
    else:
        st.info("No holdout evaluation data available.")

    # ═════════════════════════════════════════════════════════
    # CHART 3: Horizontal Bar — Feature Importances
    # ═════════════════════════════════════════════════════════
    st.subheader("XGBoost Feature Importances")
    st.caption("Which features drive the model's predictions most?")

    importances = model.feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": FEATURE_COLS,
        "Importance": importances,
    }).sort_values("Importance", ascending=True)

    fig3 = go.Figure(go.Bar(
        x=feat_imp_df["Importance"],
        y=feat_imp_df["Feature"],
        orientation="h",
        marker=dict(
            color=feat_imp_df["Importance"],
            colorscale=[
                [0.0, "#D2B4DE"],
                [0.5, "#9B59B6"],
                [1.0, "#6C3483"],
            ],
            showscale=False,
        ),
        text=feat_imp_df["Importance"].apply(lambda x: f"{x:.3f}"),
        textposition="outside",
    ))
    fig3.update_layout(
        xaxis_title="Importance Score",
        yaxis=dict(tickfont=dict(size=11)),
    )
    _base_layout(fig3, "XGBoost Feature Importances", height=420)
    st.plotly_chart(fig3, width='stretch', key="ml_feature_importance")

    # ═════════════════════════════════════════════════════════
    # AI PANEL
    # ═════════════════════════════════════════════════════════
    st.markdown("---")
    if st.button("🤖 Explain ML Results", key="ml_ai_btn", type="primary"):
        # Build context for AI
        context_parts = []

        # Overall MAPE comparison
        context_parts.append(f"Overall ML Model MAPE on holdout: {overall_mape:.1f}%")

        # Human team MAPEs on FY26 Q1
        for team in ["Demand Planners", "Marketing Team", "Data Science Team"]:
            mask = (accuracy_df["Team"] == team) & (accuracy_df["Quarter"] == "FY26 Q1")
            human_mape = (1 - accuracy_df.loc[mask, "Accuracy"]).mean() * 100
            context_parts.append(f"{team} avg MAPE on FY26 Q1: {human_mape:.1f}%")

        context_parts.append(f"\nML beats all 3 human teams on {ml_wins} out of 30 products")

        # Top 5 where ML won (lowest APE)
        if not eval_df.empty:
            product_mape = eval_df.groupby("Product")["APE"].mean().sort_values()
            top5_wins = product_mape.head(5)
            context_parts.append("\nTop 5 products where ML performed best:")
            for p, ape in top5_wins.items():
                context_parts.append(f"  {p}: {ape*100:.1f}% MAPE")

            # Top 5 where ML lost (highest APE)
            top5_losses = product_mape.tail(5)
            context_parts.append("\nTop 5 products where ML performed worst:")
            for p, ape in top5_losses.items():
                context_parts.append(f"  {p}: {ape*100:.1f}% MAPE")

        # Feature importances
        feat_sorted = feat_imp_df.sort_values("Importance", ascending=False)
        context_parts.append("\nTop feature importances:")
        for _, row in feat_sorted.iterrows():
            context_parts.append(f"  {row['Feature']}: {row['Importance']:.3f}")

        context_str = "\n".join(context_parts)

        with st.container():
            st.markdown(
                '<div class="ai-box"><div class="ai-box-header">'
                '<span class="ai-badge">✨ AI</span>'
                '<span class="ai-title">ML Forecasting Analysis</span>'
                '</div><div class="ai-box-content">',
                unsafe_allow_html=True,
            )
            st.write_stream(get_ml_forecast_analysis(context_str))
            st.markdown('</div></div>', unsafe_allow_html=True)

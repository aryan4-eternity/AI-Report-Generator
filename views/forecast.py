"""
Page 2 — Forecast Accuracy Analysis
Team comparison, bias heatmap, accuracy vs volume scatter, AI analysis.
"""

import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_row, render_section_header
from components.charts import (
    grouped_bar_accuracy,
    bias_heatmap,
    scatter_accuracy_volume,
)
from components.ai_engine import get_forecast_analysis
from config import TEAM_COLORS, FORECAST_TEAMS, ACCURACY_QUARTERS


def render(data: dict):
    """Render the Forecast Accuracy page."""
    accuracy_df = data["forecast_accuracy"]
    bookings = data["bookings"]

    if accuracy_df.empty:
        st.warning("Forecast accuracy data is not available.")
        return

    render_section_header("🎯 Forecast Accuracy Analysis", "Compare prediction performance across teams")

    # ─── TOP KPI CARDS: Accuracy per team for FY26 Q1 ────────
    latest_q = "FY26 Q1"
    team_kpis = []
    team_icons = {"Demand Planners": "📋", "Marketing Team": "📣", "Data Science Team": "🔬"}

    for team in FORECAST_TEAMS:
        mask = (accuracy_df["Team"] == team) & (accuracy_df["Quarter"] == latest_q)
        avg_acc = accuracy_df.loc[mask, "Accuracy"].mean() if mask.any() else 0
        team_kpis.append({
            "label": team,
            "value": f"{avg_acc:.1%}",
            "icon": team_icons.get(team, "📊"),
            "delta": f"{latest_q} Avg",
            "delta_color": TEAM_COLORS.get(team, "#888"),
        })

    render_kpi_row(team_kpis)
    st.markdown("<br>", unsafe_allow_html=True)

    # ─── CHART 1: Grouped Bar — Accuracy by Product & Team ──
    st.subheader("Accuracy by Product")
    quarter_select = st.selectbox(
        "Select Quarter", ACCURACY_QUARTERS, index=len(ACCURACY_QUARTERS) - 1,
        key="forecast_quarter"
    )

    fig_bar = grouped_bar_accuracy(accuracy_df, quarter=quarter_select,
                                   title=f"Forecast Accuracy — {quarter_select}")
    st.plotly_chart(fig_bar, width='stretch', key="forecast_bar")

    # ─── CHART 2: Bias Heatmap ──────────────────────────────
    st.subheader("Bias Heatmap")
    st.caption("🔴 Red = Under-forecast (negative bias) · 🟢 Green = Over-forecast (positive bias)")

    fig_heat = bias_heatmap(accuracy_df, title="Forecast Bias: Teams × Quarters")
    st.plotly_chart(fig_heat, width='stretch', key="forecast_heatmap")

    # ─── CHART 3: Scatter — Accuracy vs Volume ──────────────
    st.subheader("Accuracy vs Volume")
    st.caption("Bubble size = |bias|. Are high-volume products harder to forecast?")

    fig_scatter = scatter_accuracy_volume(
        accuracy_df, bookings,
        quarter=quarter_select,
        title=f"Forecast Accuracy vs Actual Volume — {quarter_select}",
    )
    st.plotly_chart(fig_scatter, width='stretch', key="forecast_scatter")

    # ─── AI INSIGHT ─────────────────────────────────────────
    st.markdown("---")
    if st.button("🤖 Explain Forecast Patterns", key="forecast_ai_btn"):
        with st.spinner("Analyzing forecast patterns…"):
            # Build accuracy summary string
            acc_summary_lines = []
            for team in FORECAST_TEAMS:
                for q in ACCURACY_QUARTERS:
                    mask = (accuracy_df["Team"] == team) & (accuracy_df["Quarter"] == q)
                    avg = accuracy_df.loc[mask, "Accuracy"].mean()
                    acc_summary_lines.append(f"{team} | {q} | Avg Accuracy: {avg:.3f}")

            # Build bias summary string
            bias_summary_lines = []
            for team in FORECAST_TEAMS:
                for q in ACCURACY_QUARTERS:
                    mask = (accuracy_df["Team"] == team) & (accuracy_df["Quarter"] == q)
                    avg_bias = accuracy_df.loc[mask, "Bias"].mean()
                    bias_summary_lines.append(f"{team} | {q} | Avg Bias: {avg_bias:.4f}")

            # Product-level worst accuracy
            worst = accuracy_df.groupby("Product")["Accuracy"].mean().nsmallest(5)
            acc_summary_lines.append("\nHardest to Forecast (lowest avg accuracy):")
            for prod, acc in worst.items():
                acc_summary_lines.append(f"  {prod}: {acc:.3f}")

            result = get_forecast_analysis(
                "\n".join(acc_summary_lines),
                "\n".join(bias_summary_lines),
            )
            if result:
                st.markdown(result)

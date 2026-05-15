"""
Page 3 — Segment Analysis (SCMS)
Stacked bars, segment trend lines, share chart, data table, AI insight.
"""

import streamlit as st
import pandas as pd
from components.kpi_cards import render_section_header
from components.charts import (
    stacked_bar_segments,
    stacked_bar_100_pct,
    line_chart_segments,
)
from components.ai_engine import get_segment_insight
from config import SEGMENT_COLORS, SCMS_QUARTERS


def render(data: dict):
    """Render the Segment Analysis page."""
    scms = data["scms"]

    if scms.empty:
        st.warning("Segment (SCMS) data is not available.")
        return

    render_section_header("🏢 Segment Analysis", "Sales distribution across market segments")

    # ─── SIDEBAR FILTERS ────────────────────────────────────
    st.sidebar.markdown("### 🔍 Segment Filters")

    products = sorted(scms["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox(
        "Select Product", products, key="seg_product"
    )

    available_quarters = sorted(scms["Quarter"].unique().tolist())
    if len(available_quarters) >= 2:
        q_range = st.sidebar.select_slider(
            "Quarter Range",
            options=available_quarters,
            value=(available_quarters[0], available_quarters[-1]),
            key="seg_q_range",
        )
        filtered = scms[
            (scms["Product"] == selected_product) &
            (scms["Quarter"] >= q_range[0]) &
            (scms["Quarter"] <= q_range[1])
        ]
    else:
        filtered = scms[scms["Product"] == selected_product]

    st.markdown(f"#### 📦 Product: **{selected_product}**")
    st.markdown("<br>", unsafe_allow_html=True)

    # ─── CHART 1: Stacked Bar — Units by Segment ────────────
    col1, col2 = st.columns(2)

    with col1:
        fig_stacked = stacked_bar_segments(
            filtered, selected_product,
            title=f"Units by Segment — {selected_product}",
        )
        st.plotly_chart(fig_stacked, width='stretch', key="seg_stacked")

    # ─── CHART 2: Line — Segment Trends ─────────────────────
    with col2:
        fig_line = line_chart_segments(
            filtered, selected_product,
            title=f"Segment Trends — {selected_product}",
        )
        st.plotly_chart(fig_line, width='stretch', key="seg_line")

    # ─── CHART 3: 100% Stacked Bar — Share % ────────────────
    fig_share = stacked_bar_100_pct(
        filtered, selected_product,
        title=f"Segment Share % — {selected_product}",
    )
    st.plotly_chart(fig_share, width='stretch', key="seg_share")

    # ─── DATA TABLE ─────────────────────────────────────────
    st.subheader("📋 Raw Segment Data")
    pivot = filtered.pivot_table(
        index="Segment", columns="Quarter", values="Units", aggfunc="sum"
    ).fillna(0)

    # Style the table with conditional coloring
    if not pivot.empty:
        styled = pivot.style.background_gradient(cmap="YlGnBu", axis=None).format("{:,.0f}")
        st.dataframe(styled, width='stretch', height=280)

    # ─── AI INSIGHT ─────────────────────────────────────────
    st.markdown("---")
    if st.button("🤖 What's Driving Segment Shifts?", key="seg_ai_btn"):
        with st.spinner("Analyzing segment trends…"):
            # Build segment summary
            summary_lines = [f"Product: {selected_product}\n"]
            for seg in filtered["Segment"].unique():
                seg_data = filtered[filtered["Segment"] == seg]
                if not seg_data.empty:
                    first_val = seg_data["Units"].iloc[0]
                    last_val = seg_data["Units"].iloc[-1]
                    change = ((last_val - first_val) / max(first_val, 1)) * 100
                    total = seg_data["Units"].sum()
                    summary_lines.append(
                        f"  {seg}: Total={total:,.0f}, "
                        f"First Q={first_val:,.0f}, Latest Q={last_val:,.0f}, "
                        f"Change={change:+.1f}%"
                    )

            # Add share data
            latest_q = filtered["Quarter"].max()
            latest_data = filtered[filtered["Quarter"] == latest_q]
            total_latest = latest_data["Units"].sum()
            if total_latest > 0:
                summary_lines.append(f"\nLatest Quarter ({latest_q}) Share:")
                for _, row in latest_data.iterrows():
                    share = row["Units"] / total_latest * 100
                    summary_lines.append(f"  {row['Segment']}: {share:.1f}%")

            result = get_segment_insight("\n".join(summary_lines), selected_product)
            if result:
                st.markdown(result)

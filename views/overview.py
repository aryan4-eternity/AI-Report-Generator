"""
Page 1 — Overview Dashboard
Top KPIs, trend lines, lifecycle bar chart, segment donut, AI executive summary.
"""

import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_row, render_ai_insight_box, render_section_header
from components.charts import (
    line_chart_multi_product,
    horizontal_bar_lifecycle,
    donut_chart,
)
from components.ai_engine import get_executive_summary
from config import LIFECYCLE_COLORS, SEGMENT_COLORS, QUARTER_LABELS


def render(data: dict):
    """Render the Overview page."""
    bookings = data["bookings"]
    metadata = data["metadata"]
    accuracy = data["forecast_accuracy"]
    scms = data["scms"]

    if bookings.empty:
        st.error("Bookings data could not be loaded. Please check your Excel file.")
        return

    # ─── SIDEBAR FILTERS ────────────────────────────────────
    st.sidebar.markdown("### 🔍 Overview Filters")

    all_products = bookings["Product"].tolist()
    lifecycles = metadata["Lifecycle"].unique().tolist() if not metadata.empty else []

    selected_lifecycle = st.sidebar.selectbox(
        "Lifecycle Filter", ["All"] + lifecycles, key="overview_lifecycle"
    )
    if selected_lifecycle != "All" and not metadata.empty:
        lifecycle_products = metadata[metadata["Lifecycle"] == selected_lifecycle]["Product"].tolist()
        filtered_products = [p for p in all_products if p in lifecycle_products]
    else:
        filtered_products = all_products

    selected_products = st.sidebar.multiselect(
        "Select Products", filtered_products, default=filtered_products[:5], key="overview_products"
    )

    fy_options = ["All", "FY23", "FY24", "FY25", "FY26"]
    selected_fy = st.sidebar.selectbox("Fiscal Year", fy_options, key="overview_fy")

    # Filter quarters by fiscal year
    if selected_fy != "All":
        active_quarters = [q for q in QUARTER_LABELS if q.startswith(selected_fy)]
    else:
        active_quarters = QUARTER_LABELS

    # Apply product filter
    bk = bookings[bookings["Product"].isin(selected_products)] if selected_products else bookings

    # ─── KPI CALCULATIONS ───────────────────────────────────
    latest_q = active_quarters[-1] if active_quarters else QUARTER_LABELS[-1]
    total_units = int(bk[latest_q].sum()) if latest_q in bk.columns else 0

    top_product = bk.set_index("Product")[latest_q].idxmax() if latest_q in bk.columns and not bk.empty else "N/A"

    avg_accuracy = accuracy["Accuracy"].mean() if "Accuracy" in accuracy.columns else 0
    avg_accuracy_str = f"{avg_accuracy:.1%}"

    declining_count = 0
    if not metadata.empty:
        declining_count = len(metadata[metadata["Lifecycle"] == "Decline"])

    # ─── ROW 1: KPI CARDS ───────────────────────────────────
    render_section_header("📊 Portfolio Overview", f"Latest Quarter: {latest_q}")

    render_kpi_row([
        {"label": "Total Units Booked", "value": f"{total_units:,}", "icon": "📦",
         "delta": f"{latest_q}", "delta_color": "#378ADD"},
        {"label": "Top Product", "value": top_product[:25], "icon": "🏆"},
        {"label": "Avg Forecast Accuracy", "value": avg_accuracy_str, "icon": "🎯",
         "delta": "All Teams", "delta_color": "#1D9E75"},
        {"label": "Declining Products", "value": str(declining_count), "icon": "📉",
         "delta": f"of {len(bookings)} total", "delta_color": "#E24B4A"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── ROW 2: TOP 5 PRODUCT TREND ─────────────────────────
    # Get top 5 by total volume
    quarter_cols = [q for q in active_quarters if q in bookings.columns]
    if quarter_cols:
        bk_totals = bk.copy()
        bk_totals["Total"] = bk_totals[quarter_cols].sum(axis=1)
        top5 = bk_totals.nlargest(5, "Total")["Product"].tolist()

        # Melt to long format for plotting
        melt_cols = ["Product"] + quarter_cols
        long_df = bk[bk["Product"].isin(top5)][melt_cols].melt(
            id_vars="Product", var_name="Quarter", value_name="Units"
        )

        fig_trend = line_chart_multi_product(
            long_df, top5,
            title=f"Top {len(top5)} Products — Quarterly Booking Trend",
            height=400,
        )
        st.plotly_chart(fig_trend, width='stretch', key="overview_trend")

        # Lifecycle badges below chart
        if not metadata.empty:
            badge_parts = []
            for p in top5:
                match = metadata[metadata["Product"] == p]
                lc = match["Lifecycle"].values[0] if len(match) > 0 else "Unknown"
                color = LIFECYCLE_COLORS.get(lc, "#888")
                short_name = p[:22] + "…" if len(p) > 22 else p
                badge_parts.append(
                    f'<span style="display:inline-block; background:rgba(0,0,0,0.03); '
                    f'border:1px solid rgba(0,0,0,0.08); border-radius:8px; '
                    f'padding:4px 10px; margin:3px; font-size:0.78rem; white-space:nowrap;">'
                    f'<b>{short_name}</b>: '
                    f'<span style="color:{color}; font-weight:600;">{lc}</span></span>'
                )
            badge_html = "".join(badge_parts)
            st.markdown(
                f'<div style="text-align:center; margin-bottom:1rem; display:flex; '
                f'flex-wrap:wrap; justify-content:center; gap:4px;">{badge_html}</div>',
                unsafe_allow_html=True,
            )

    # ─── ROW 3: BAR CHART + DONUT ───────────────────────────
    col_bar, col_donut = st.columns([3, 2])

    with col_bar:
        if latest_q in bk.columns and not metadata.empty:
            bar_df = bk[["Product", latest_q]].merge(metadata[["Product", "Lifecycle"]], on="Product", how="left")
            bar_df["Lifecycle"] = bar_df["Lifecycle"].fillna("Unknown")
            fig_bar = horizontal_bar_lifecycle(
                bar_df, latest_q,
                title=f"Top 10 Products by {latest_q} Units",
                top_n=10,
            )
            st.plotly_chart(fig_bar, width='stretch', key="overview_bar")

    with col_donut:
        if not scms.empty:
            latest_scms_q = scms["Quarter"].unique()[-1]
            seg_totals = scms[scms["Quarter"] == latest_scms_q].groupby("Segment")["Units"].sum()
            if not seg_totals.empty:
                fig_donut = donut_chart(
                    labels=seg_totals.index.tolist(),
                    values=seg_totals.values.tolist(),
                    colors=SEGMENT_COLORS,
                    title=f"Segment Split — {latest_scms_q}",
                )
                st.plotly_chart(fig_donut, width='stretch', key="overview_donut")

    # ─── ROW 4: AI EXECUTIVE SUMMARY ────────────────────────
    st.markdown("---")

    # Calculate QoQ growth
    qoq_growth = "N/A"
    if len(quarter_cols) >= 2:
        q_curr = bookings[quarter_cols[-1]].sum()
        q_prev = bookings[quarter_cols[-2]].sum()
        if q_prev > 0:
            qoq_growth = f"{((q_curr - q_prev) / q_prev * 100):.1f}%"

    kpi_dict = {
        "latest_quarter": latest_q,
        "total_units": total_units,
        "top_product": top_product,
        "avg_accuracy": avg_accuracy_str,
        "declining_count": declining_count,
        "top_5_products": ", ".join(top5) if quarter_cols else "N/A",
        "qoq_growth": qoq_growth,
    }

    # Auto-generate on first load, or use cached
    if "overview_ai_summary" not in st.session_state:
        with st.spinner("🤖 Generating AI executive summary…"):
            summary = get_executive_summary(kpi_dict)
            st.session_state["overview_ai_summary"] = summary

    if st.session_state["overview_ai_summary"]:
        render_ai_insight_box(st.session_state["overview_ai_summary"], "Executive Summary")

    if st.button("🔄 Regenerate Summary", key="overview_regen"):
        with st.spinner("🤖 Regenerating…"):
            summary = get_executive_summary(kpi_dict)
            st.session_state["overview_ai_summary"] = summary
            st.rerun()

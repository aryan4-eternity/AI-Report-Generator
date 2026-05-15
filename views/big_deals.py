"""
Page 5 — Big Deal Intelligence
Big vs avg deal comparison, dependency analysis, risk assessment.
"""

import streamlit as st
import pandas as pd
from components.kpi_cards import render_kpi_row, render_section_header
from components.charts import (
    grouped_bar_big_deals,
    big_deal_pct_line,
    big_deal_dependency_bar,
)
from components.ai_engine import get_big_deal_risk
from config import BIG_DEAL_QUARTERS


def render(data: dict):
    """Render the Big Deal Intelligence page."""
    big_deals = data["big_deals"]

    if big_deals.empty:
        st.warning("Big deal data is not available.")
        return

    render_section_header("💼 Big Deal Intelligence", "Analyze deal concentration and risk")

    # ─── KPI CARDS ──────────────────────────────────────────
    # Most big-deal-dependent product
    agg = big_deals.groupby("Product")[["Big_Deals", "Avg_Deals", "MFG_Units"]].sum().reset_index()
    agg["Total_Deals"] = agg["Big_Deals"] + agg["Avg_Deals"]
    agg["Big_Pct"] = (agg["Big_Deals"] / agg["Total_Deals"].replace(0, 1) * 100).round(1)

    most_dependent = agg.loc[agg["Big_Pct"].idxmax()]
    most_dependent_name = most_dependent["Product"] if not agg.empty else "N/A"
    most_dependent_pct = f"{most_dependent['Big_Pct']:.1f}%" if not agg.empty else "N/A"

    # Biggest single-quarter big deal spike
    biggest_spike = big_deals.loc[big_deals["Big_Deals"].idxmax()] if not big_deals.empty else None
    spike_product = biggest_spike["Product"] if biggest_spike is not None else "N/A"
    spike_quarter = biggest_spike["Quarter"] if biggest_spike is not None else "N/A"
    spike_value = f"{int(biggest_spike['Big_Deals']):,}" if biggest_spike is not None else "N/A"

    # Count of high-dependency products (>15%)
    high_dep_count = len(agg[agg["Big_Pct"] > 15])

    render_kpi_row([
        {
            "label": "Most Big-Deal Dependent",
            "value": most_dependent_name[:22],
            "icon": "🎯",
            "delta": f"{most_dependent_pct} of volume",
            "delta_color": "#E24B4A",
        },
        {
            "label": "Biggest Deal Spike",
            "value": spike_value,
            "icon": "📈",
            "delta": f"{spike_product[:15]} — {spike_quarter}",
            "delta_color": "#D85A30",
        },
        {
            "label": "High-Dependency Products",
            "value": str(high_dep_count),
            "icon": "⚠️",
            "delta": ">15% from big deals",
            "delta_color": "#EF9F27",
        },
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── SIDEBAR FILTERS ────────────────────────────────────
    st.sidebar.markdown("### 🔍 Big Deal Filters")
    products = sorted(big_deals["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox(
        "Select Product (for detail view)", products, key="bd_product"
    )

    # ─── CHART 1: Grouped Bar — Big vs Avg for selected product ─
    st.subheader(f"Big Deals vs Avg Deals — {selected_product}")

    fig_grouped = grouped_bar_big_deals(
        big_deals, selected_product, n_quarters=4,
        title=f"Recent 4 Quarters — {selected_product}",
    )
    st.plotly_chart(fig_grouped, width='stretch', key="bd_grouped")

    # ─── CHART 2: Line — Big deal % over time ──────────────
    st.subheader("Big Deal % of Total Bookings")

    top_products = agg.nlargest(8, "Big_Pct")["Product"].tolist()
    fig_pct = big_deal_pct_line(
        big_deals, products=top_products,
        title="Big Deal % — Top 8 Most Dependent Products",
    )
    st.plotly_chart(fig_pct, width='stretch', key="bd_pct_line")

    # ─── CHART 3: Stacked — Dependency bar ──────────────────
    st.subheader("Deal Composition — Big vs Avg")
    st.caption("⚠️ Products with >15% big deal dependency are flagged")

    fig_dep = big_deal_dependency_bar(
        big_deals,
        title="Big Deal Dependency Across Products",
    )
    st.plotly_chart(fig_dep, width='stretch', key="bd_dependency")

    # ─── AI INSIGHT ─────────────────────────────────────────
    st.markdown("---")
    if st.button("🤖 Analyze Big Deal Risk", key="bd_ai_btn"):
        with st.spinner("Assessing big deal risk…"):
            summary_lines = ["Product | Big Deal % | Total Big Deals | Total Avg Deals | Trend\n"]

            for _, row in agg.iterrows():
                # Calculate trend (latest vs first quarter)
                prod_data = big_deals[big_deals["Product"] == row["Product"]].sort_values("Quarter")
                if len(prod_data) >= 2:
                    first_pct = prod_data.iloc[0]["Big_Deals"] / max(prod_data.iloc[0]["MFG_Units"], 1) * 100
                    last_pct = prod_data.iloc[-1]["Big_Deals"] / max(prod_data.iloc[-1]["MFG_Units"], 1) * 100
                    trend = "↑ Increasing" if last_pct > first_pct else "↓ Decreasing"
                else:
                    trend = "—"

                summary_lines.append(
                    f"{row['Product']} | {row['Big_Pct']:.1f}% | "
                    f"{int(row['Big_Deals']):,} | {int(row['Avg_Deals']):,} | {trend}"
                )

            summary_lines.append(f"\nProducts with >15% big deal dependency: {high_dep_count}")
            summary_lines.append(f"Most dependent: {most_dependent_name} at {most_dependent_pct}")

            result = get_big_deal_risk("\n".join(summary_lines))
            if result:
                st.markdown(result)

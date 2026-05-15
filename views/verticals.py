"""
Page 4 — Vertical / Industry Analysis (VMS)
Treemap, horizontal stacked bars, trend lines, AI recommendation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from components.kpi_cards import render_section_header
from components.charts import treemap_verticals, _base_layout
from components.ai_engine import get_vertical_recommendation
from config import SCMS_QUARTERS


def render(data: dict):
    """Render the Vertical Analysis page."""
    vms = data["vms"]
    bookings = data["bookings"]

    if vms.empty:
        st.warning("Vertical (VMS) data is not available.")
        return

    render_section_header("🏭 Vertical / Industry Analysis", "Sales by industry vertical")

    # ─── SIDEBAR FILTERS ────────────────────────────────────
    st.sidebar.markdown("### 🔍 Vertical Filters")

    products = sorted(vms["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox(
        "Select Product", products, key="vert_product"
    )

    available_quarters = sorted(vms["Quarter"].unique().tolist())
    selected_quarter = st.sidebar.selectbox(
        "Select Quarter (for Treemap)", available_quarters,
        index=len(available_quarters) - 1, key="vert_quarter"
    )

    st.markdown(f"#### 📦 Product: **{selected_product}**")
    st.markdown("<br>", unsafe_allow_html=True)

    # ─── CHART 1: Treemap — Vertical distribution ───────────
    fig_tree = treemap_verticals(
        vms, selected_product, selected_quarter,
        title=f"Vertical Distribution — {selected_product} ({selected_quarter})",
    )
    st.plotly_chart(fig_tree, width='stretch', key="vert_treemap")

    # ─── CHART 2: Horizontal Stacked Bar — Top Verticals ────
    st.subheader("Top Verticals × Top Products")

    # Top 8 verticals by total units
    vert_totals = vms.groupby("Vertical")["Units"].sum().nlargest(8)
    top_verts = vert_totals.index.tolist()

    # Top 5 products by total units
    if not bookings.empty:
        q_cols = [c for c in bookings.columns if c != "Product"]
        prod_totals = bookings.set_index("Product")[q_cols].sum(axis=1).nlargest(5)
        top_prods = prod_totals.index.tolist()
    else:
        prod_totals_vms = vms.groupby("Product")["Units"].sum().nlargest(5)
        top_prods = prod_totals_vms.index.tolist()

    cross = vms[vms["Vertical"].isin(top_verts) & vms["Product"].isin(top_prods)]
    cross_agg = cross.groupby(["Vertical", "Product"])["Units"].sum().reset_index()

    if not cross_agg.empty:
        fig_hbar = px.bar(
            cross_agg.sort_values("Units"),
            x="Units",
            y="Vertical",
            color="Product",
            orientation="h",
            barmode="stack",
            title="Top 8 Verticals by Top 5 Products (Total Units)",
        )
        fig_hbar = _base_layout(fig_hbar, "Top 8 Verticals by Top 5 Products", 450)
        st.plotly_chart(fig_hbar, width='stretch', key="vert_hbar")

    # ─── CHART 3: Line — Selected Vertical Trends ───────────
    st.subheader("Vertical Trend Comparison")

    all_verts = sorted(vms[vms["Product"] == selected_product]["Vertical"].unique().tolist())
    selected_verts = st.multiselect(
        "Select up to 3 verticals to compare",
        all_verts,
        default=all_verts[:3] if len(all_verts) >= 3 else all_verts,
        max_selections=3,
        key="vert_multi",
    )

    if selected_verts:
        vert_trend = vms[
            (vms["Product"] == selected_product) &
            (vms["Vertical"].isin(selected_verts))
        ]
        fig_line = px.line(
            vert_trend,
            x="Quarter",
            y="Units",
            color="Vertical",
            markers=True,
            title=f"Quarterly Trend — {selected_product}",
        )
        fig_line.update_traces(line=dict(width=2.5), marker=dict(size=6))
        fig_line = _base_layout(fig_line, f"Quarterly Trend — {selected_product}", 400)
        st.plotly_chart(fig_line, width='stretch', key="vert_line")

    # ─── AI INSIGHT ─────────────────────────────────────────
    st.markdown("---")
    if st.button("🤖 Which Verticals Should We Focus On?", key="vert_ai_btn"):
        with st.spinner("Generating vertical recommendations…"):
            prod_vms = vms[vms["Product"] == selected_product]
            summary_lines = [f"Product: {selected_product}\n"]

            for vert in prod_vms["Vertical"].unique():
                v_data = prod_vms[prod_vms["Vertical"] == vert]
                total = v_data["Units"].sum()
                if total <= 0:
                    continue
                first_val = v_data["Units"].iloc[0]
                last_val = v_data["Units"].iloc[-1]
                growth = ((last_val - first_val) / max(first_val, 1)) * 100
                summary_lines.append(
                    f"  {vert}: Total={total:,.0f}, Latest Q={last_val:,.0f}, Growth={growth:+.1f}%"
                )

            result = get_vertical_recommendation("\n".join(summary_lines), selected_product)
            if result:
                st.markdown(result)

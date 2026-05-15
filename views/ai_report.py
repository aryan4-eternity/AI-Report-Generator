"""
Page 6 — AI Report Generator
Quick reports, natural language Q&A, full dashboard report.
"""

import streamlit as st
import pandas as pd
import io
from markdown_pdf import MarkdownPdf, Section
from components.kpi_cards import render_section_header
from components.ai_engine import (
    generate_product_report,
    chat_with_data,
    generate_full_report,
)
from config import QUARTER_LABELS, FORECAST_TEAMS


def _build_product_context(product: str, data: dict) -> str:
    """Build a comprehensive data context string for a specific product."""
    lines = [f"=== PRODUCT: {product} ===\n"]

    # Bookings
    bookings = data["bookings"]
    if not bookings.empty and product in bookings["Product"].values:
        row = bookings[bookings["Product"] == product].iloc[0]
        lines.append("QUARTERLY BOOKINGS (Actual Units):")
        for q in QUARTER_LABELS:
            if q in row.index:
                lines.append(f"  {q}: {row[q]:,.0f}")

    # Forecast targets
    targets = data["forecast_targets"]
    if not targets.empty and product in targets["Product"].values:
        row = targets[targets["Product"] == product].iloc[0]
        lines.append("\nFY26 Q2 FORECAST TARGETS:")
        for team in FORECAST_TEAMS:
            if team in row.index:
                lines.append(f"  {team}: {row[team]:,.0f}")

    # Forecast accuracy
    accuracy = data["forecast_accuracy"]
    if not accuracy.empty:
        prod_acc = accuracy[accuracy["Product"] == product]
        if not prod_acc.empty:
            lines.append("\nFORECAST ACCURACY & BIAS:")
            for _, r in prod_acc.iterrows():
                lines.append(f"  {r['Team']} | {r['Quarter']} | Accuracy: {r['Accuracy']:.3f} | Bias: {r['Bias']:.4f}")

    # Lifecycle
    meta = data["metadata"]
    if not meta.empty and product in meta["Product"].values:
        lifecycle = meta[meta["Product"] == product]["Lifecycle"].values[0]
        lines.append(f"\nLIFECYCLE: {lifecycle}")

    # Segment data
    scms = data["scms"]
    if not scms.empty:
        prod_scms = scms[scms["Product"] == product]
        if not prod_scms.empty:
            lines.append("\nSEGMENT BREAKDOWN (latest quarter):")
            latest_q = prod_scms["Quarter"].max()
            latest = prod_scms[prod_scms["Quarter"] == latest_q]
            total = latest["Units"].sum()
            for _, r in latest.iterrows():
                share = r["Units"] / max(total, 1) * 100
                lines.append(f"  {r['Segment']}: {r['Units']:,.0f} ({share:.1f}%)")

    # Vertical data
    vms = data["vms"]
    if not vms.empty:
        prod_vms = vms[vms["Product"] == product]
        if not prod_vms.empty:
            lines.append("\nTOP VERTICALS (latest quarter):")
            latest_q = prod_vms["Quarter"].max()
            latest = prod_vms[prod_vms["Quarter"] == latest_q].nlargest(5, "Units")
            for _, r in latest.iterrows():
                lines.append(f"  {r['Vertical']}: {r['Units']:,.0f}")

    # Big deals
    bd = data["big_deals"]
    if not bd.empty:
        prod_bd = bd[bd["Product"] == product]
        if not prod_bd.empty:
            lines.append("\nBIG DEAL DATA (latest 4 quarters):")
            for _, r in prod_bd.tail(4).iterrows():
                total = r["Big_Deals"] + r["Avg_Deals"]
                big_pct = r["Big_Deals"] / max(total, 1) * 100
                lines.append(
                    f"  {r['Quarter']}: MFG={r['MFG_Units']:,.0f}, "
                    f"Big={r['Big_Deals']:,.0f}, Avg={r['Avg_Deals']:,.0f}, "
                    f"Big%={big_pct:.1f}%"
                )

    return "\n".join(lines)


def _build_full_context(data: dict) -> str:
    """Build a comprehensive data context for the full dashboard report."""
    lines = ["=== CFL PORTFOLIO DASHBOARD REPORT DATA ===\n"]

    bookings = data["bookings"]
    if not bookings.empty:
        q_cols = [c for c in bookings.columns if c != "Product"]
        last_q = q_cols[-1] if q_cols else ""

        lines.append(f"PORTFOLIO OVERVIEW ({last_q}):")
        lines.append(f"  Total Products: {len(bookings)}")
        if last_q:
            lines.append(f"  Total Units ({last_q}): {bookings[last_q].sum():,.0f}")
            top5 = bookings.nlargest(5, last_q)[["Product", last_q]]
            lines.append("  Top 5 Products:")
            for _, r in top5.iterrows():
                lines.append(f"    {r['Product']}: {r[last_q]:,.0f}")

        # QoQ growth
        if len(q_cols) >= 2:
            curr = bookings[q_cols[-1]].sum()
            prev = bookings[q_cols[-2]].sum()
            growth = (curr - prev) / max(prev, 1) * 100
            lines.append(f"  QoQ Growth: {growth:+.1f}%")

    # Lifecycle distribution
    meta = data["metadata"]
    if not meta.empty:
        lines.append("\nLIFECYCLE DISTRIBUTION:")
        for lc, count in meta["Lifecycle"].value_counts().items():
            lines.append(f"  {lc}: {count} products")

    # Forecast accuracy summary
    accuracy = data["forecast_accuracy"]
    if not accuracy.empty:
        lines.append("\nFORECAST ACCURACY SUMMARY (FY26 Q1):")
        for team in FORECAST_TEAMS:
            mask = (accuracy["Team"] == team) & (accuracy["Quarter"] == "FY26 Q1")
            avg = accuracy.loc[mask, "Accuracy"].mean()
            lines.append(f"  {team}: {avg:.1%}")

    # Segment summary
    scms = data["scms"]
    if not scms.empty:
        latest_q = scms["Quarter"].max()
        seg_totals = scms[scms["Quarter"] == latest_q].groupby("Segment")["Units"].sum()
        lines.append(f"\nSEGMENT DISTRIBUTION ({latest_q}):")
        total = seg_totals.sum()
        for seg, units in seg_totals.items():
            lines.append(f"  {seg}: {units:,.0f} ({units/max(total,1)*100:.1f}%)")

    # Big deal summary
    bd = data["big_deals"]
    if not bd.empty:
        agg = bd.groupby("Product")[["Big_Deals", "Avg_Deals"]].sum().reset_index()
        agg["Total"] = agg["Big_Deals"] + agg["Avg_Deals"]
        agg["Big_Pct"] = agg["Big_Deals"] / agg["Total"].replace(0, 1) * 100
        high_dep = agg[agg["Big_Pct"] > 15]
        lines.append(f"\nBIG DEAL RISK: {len(high_dep)} products with >15% big deal dependency")
        if not high_dep.empty:
            for _, r in high_dep.nlargest(3, "Big_Pct").iterrows():
                lines.append(f"  {r['Product']}: {r['Big_Pct']:.1f}%")

    return "\n".join(lines)


def render(data: dict):
    """Render the AI Report Generator page."""
    render_section_header("🤖 AI Report Generator", "Generate intelligent reports and ask questions")

    products = sorted(data["bookings"]["Product"].unique().tolist()) if not data["bookings"].empty else []

    # ─── SECTION A: Quick Report ────────────────────────────
    st.markdown("### 📄 Quick Product Report")

    col_prod, col_type = st.columns(2)
    with col_prod:
        report_product = st.selectbox("Select Product", products, key="report_product")
    with col_type:
        report_type = st.selectbox(
            "Report Type",
            ["Executive Summary", "Forecast Analysis", "Segment Deep Dive", "Risk Report"],
            key="report_type",
        )

    if st.button("📝 Generate Report", key="gen_report_btn", type="primary"):
        if report_product:
            context = _build_product_context(report_product, data)
            st.markdown(f"---")
            st.markdown(f"## 📋 {report_type} — {report_product}")

            with st.container():
                st.write_stream(generate_product_report(report_product, report_type, context))

    st.markdown("---")

    # ─── SECTION B: Natural Language Q&A ────────────────────
    st.markdown("### 💬 Ask Anything About the Data")

    # Example chips
    examples = [
        "Which product had the highest growth?",
        "Compare forecast team performance",
        "What's the outlook for the top product?",
        "Which segments are growing fastest?",
    ]
    chip_cols = st.columns(len(examples))
    for i, (col, example) in enumerate(zip(chip_cols, examples)):
        with col:
            if st.button(f"💡 {example}", key=f"chip_{i}", width='stretch'):
                st.session_state["chat_input_prefill"] = example

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask anything about the sales data…")

    # Check for prefilled input from chip buttons
    if "chat_input_prefill" in st.session_state:
        user_input = st.session_state.pop("chat_input_prefill")

    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build data context
        context = _build_full_context(data)

        # Generate response
        with st.chat_message("assistant"):
            response_chunks = []
            stream = chat_with_data(
                user_input,
                st.session_state.messages[:-1],  # Don't include the current message twice
                context,
            )
            response = st.write_stream(stream)

        # Save assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown("---")

    # ─── SECTION C: Full Dashboard Report ───────────────────
    st.markdown("### 📊 Full Dashboard Report")
    st.caption("Generate a comprehensive multi-section report covering the entire portfolio.")

    if st.button("📑 Generate Full Dashboard Report", key="full_report_btn", type="primary"):
        context = _build_full_context(data)

        st.markdown("---")
        st.markdown("## 📊 CFL Sales Intelligence — Full Report")

        # Stream the report
        full_report_text = ""
        report_container = st.empty()
        for chunk in generate_full_report(context):
            full_report_text += chunk
            report_container.markdown(full_report_text)

        # Download button
        if full_report_text:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download Report (.md)",
                    data=full_report_text,
                    file_name="cfl_sales_intelligence_report.md",
                    mime="text/markdown",
                    key="download_report",
                )
            with col2:
                try:
                    pdf = MarkdownPdf(toc_level=2)
                    pdf.add_section(Section(full_report_text))
                    pdf_buffer = io.BytesIO()
                    pdf.save(pdf_buffer)
                    
                    st.download_button(
                        label="📄 Download Report (.pdf)",
                        data=pdf_buffer.getvalue(),
                        file_name="cfl_sales_intelligence_report.pdf",
                        mime="application/pdf",
                        key="download_report_pdf",
                    )
                except Exception as e:
                    st.error(f"Could not generate PDF: {e}")

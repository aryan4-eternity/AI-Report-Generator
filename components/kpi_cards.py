"""
Reusable KPI card components for the CFL Sales Dashboard.
"""

import streamlit as st


def render_kpi_row(kpis: list[dict]):
    """
    Render a row of KPI metric cards.

    Args:
        kpis: List of dicts with keys: label, value, delta (optional), delta_color (optional), icon (optional)
              Example: {"label": "Total Units", "value": "125,430", "delta": "+5.2%", "icon": "📦"}
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{kpi.get('icon', '📊')}</div>
                    <div class="kpi-label">{kpi['label']}</div>
                    <div class="kpi-value">{kpi['value']}</div>
                    {f'<div class="kpi-delta" style="color: {kpi.get("delta_color", "#1D9E75")}">{kpi.get("delta", "")}</div>' if kpi.get("delta") else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_ai_insight_box(text: str, title: str = "AI-Generated Insight"):
    """
    Render an AI insight in a styled container.

    Args:
        text: The AI-generated text (markdown supported)
        title: Title for the insight box
    """
    st.markdown(
        f"""
        <div class="ai-box">
            <div class="ai-box-header">
                <span class="ai-badge">✨ AI</span>
                <span class="ai-title">{title}</span>
            </div>
            <div class="ai-box-content">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = ""):
    """Render a styled section header."""
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{title}</h2>
            {f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_lifecycle_badge(lifecycle: str) -> str:
    """Return HTML for a lifecycle badge."""
    colors = {
        "Sustaining": ("#1D9E75", "#E8F8F0"),
        "Decline": ("#E24B4A", "#FDE8E8"),
        "NPI-Ramp": ("#EF9F27", "#FEF3E2"),
    }
    fg, bg = colors.get(lifecycle, ("#888780", "#F0F0F0"))
    return f'<span style="background:{bg}; color:{fg}; padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600;">{lifecycle}</span>'

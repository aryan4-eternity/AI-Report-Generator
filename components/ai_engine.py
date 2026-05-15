"""
AI Engine — All Groq API interaction functions for the CFL Sales Dashboard.
Uses the groq Python SDK with streaming support.
"""

import streamlit as st
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, AI_SYSTEM_PROMPT


def _get_client() -> Groq:
    """Get a Groq client instance."""
    api_key = GROQ_API_KEY or st.session_state.get("groq_api_key", "")
    if not api_key:
        raise ValueError("Groq API key not found. Set `GROQ_API_KEY` in your `.env` file or enter it in the sidebar.")
    return Groq(api_key=api_key)


def _call_llm(prompt: str, system: str = AI_SYSTEM_PROMPT, max_tokens: int = 1500) -> str:
    """
    Non-streaming call to Groq. Returns the response text.
    Handles errors gracefully.
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ AI Engine Error: {str(e)}")
        return ""


def _stream_llm(prompt: str, system: str = AI_SYSTEM_PROMPT, max_tokens: int = 2000):
    """
    Streaming generator for Groq responses.
    Yields text chunks for use with st.write_stream().
    """
    try:
        client = _get_client()
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"❌ AI Engine Error: {str(e)}"


# ─── 1. EXECUTIVE SUMMARY ───────────────────────────────────
def get_executive_summary(kpi_dict: dict) -> str:
    """
    Generate a 4–5 sentence executive summary from top-level KPIs.

    Args:
        kpi_dict: dict with keys like 'total_units', 'top_product', 'avg_accuracy',
                  'declining_count', 'top_5_products', 'latest_quarter', etc.
    """
    prompt = f"""Based on the following sales dashboard KPIs, write a concise 4-5 sentence executive summary 
for a networking hardware product portfolio. Focus on key trends, standout performers, and areas of concern.

**Key Metrics:**
- Latest Quarter: {kpi_dict.get('latest_quarter', 'FY26 Q1')}
- Total Units Booked (latest quarter): {kpi_dict.get('total_units', 'N/A'):,}
- Top Product by Volume: {kpi_dict.get('top_product', 'N/A')}
- Average Forecast Accuracy (all teams): {kpi_dict.get('avg_accuracy', 'N/A')}
- Number of Declining Products: {kpi_dict.get('declining_count', 'N/A')} out of 30
- Top 5 Products by Total Volume: {kpi_dict.get('top_5_products', 'N/A')}
- Quarter-over-Quarter Growth: {kpi_dict.get('qoq_growth', 'N/A')}

Write the summary in a professional tone suitable for a C-level audience."""
    return _call_llm(prompt, max_tokens=500)


# ─── 2. FORECAST ANALYSIS ───────────────────────────────────
def get_forecast_analysis(accuracy_summary: str, bias_summary: str) -> str:
    """
    Analyze forecast accuracy and bias patterns.

    Args:
        accuracy_summary: Pre-formatted string of accuracy data by team and product
        bias_summary: Pre-formatted string of bias data by team and product
    """
    prompt = f"""Analyze the following forecast accuracy and bias data for a networking hardware product portfolio.
Provide a structured analysis covering:
1. **Best Performing Team** — which forecast team is most accurate overall and why
2. **Hardest to Forecast Products** — identify products with consistently low accuracy
3. **Bias Patterns** — which teams tend to over-forecast vs under-forecast
4. **Recommendations** — actionable suggestions to improve forecast quality

**Forecast Accuracy Data (0-1 scale, 1 = perfect):**
{accuracy_summary}

**Forecast Bias Data (negative = under-forecast, positive = over-forecast):**
{bias_summary}

Use bullet points and be specific with product names and numbers."""
    return _call_llm(prompt, max_tokens=1200)


# ─── 3. SEGMENT INSIGHT ─────────────────────────────────────
def get_segment_insight(segment_summary: str, product_name: str) -> str:
    """
    Interpret segment trend shifts for a specific product.

    Args:
        segment_summary: Formatted string of segment data over time
        product_name: Name of the selected product
    """
    prompt = f"""Analyze the segment distribution trends for the product "{product_name}" in a networking hardware portfolio.
Based on the data below, provide a 3-4 sentence interpretation of:
- Which segments are growing or shrinking
- What might be driving the shifts
- Strategic implications for sales team allocation

**Segment Sales Data:**
{segment_summary}

Be specific with segment names and percentages where possible."""
    return _call_llm(prompt, max_tokens=600)


# ─── 4. VERTICAL RECOMMENDATION ─────────────────────────────
def get_vertical_recommendation(vertical_summary: str, product_name: str) -> str:
    """
    Strategic recommendation on which verticals to focus on.

    Args:
        vertical_summary: Formatted string of vertical/industry data
        product_name: Name of the selected product
    """
    prompt = f"""You are advising the sales leadership for the product "{product_name}" in a networking hardware company.
Based on the vertical/industry sales data below, provide strategic recommendations:
1. **Top Growth Verticals** — which industries are showing the strongest growth trajectory
2. **Declining Verticals** — which industries are shrinking and should be deprioritized
3. **Untapped Opportunities** — verticals with low current volume but growth potential
4. **Resource Allocation** — where should sales resources be focused

**Vertical Sales Data:**
{vertical_summary}

Be data-driven and specific with vertical names and growth rates."""
    return _call_llm(prompt, max_tokens=800)


# ─── 5. BIG DEAL RISK ───────────────────────────────────────
def get_big_deal_risk(big_deal_summary: str) -> str:
    """
    Analyze big deal concentration risk across products.

    Args:
        big_deal_summary: Formatted string of big deal vs avg deal data
    """
    prompt = f"""Analyze the big deal dependency and concentration risk for a networking hardware product portfolio.
Focus on:
1. **High-Risk Products** — products where >15% of volume comes from big deals
2. **Forecast Impact** — how big deal dependency affects forecast reliability
3. **Trend Analysis** — is big deal dependency increasing or decreasing
4. **Mitigation Strategies** — recommendations to reduce concentration risk

**Big Deal Data (MFG Units, Big Deals, Avg Deals by product and quarter):**
{big_deal_summary}

Highlight specific products and percentages. Use a risk-assessment tone."""
    return _call_llm(prompt, max_tokens=1000)


# ─── 6. PRODUCT REPORT ──────────────────────────────────────
def generate_product_report(product_name: str, report_type: str, data_context: str):
    """
    Generate a structured report for a specific product. Returns a streaming generator.

    Args:
        product_name: Name of the product
        report_type: One of "Executive Summary", "Forecast Analysis", "Segment Deep Dive", "Risk Report"
        data_context: Comprehensive data context string for the product
    """
    report_instructions = {
        "Executive Summary": """Write a comprehensive executive summary covering:
- Sales trajectory and recent performance
- Forecast outlook and team predictions
- Key segment and vertical highlights
- Strategic recommendations
Format with clear headers and bullet points.""",

        "Forecast Analysis": """Write a detailed forecast analysis covering:
- Historical accuracy by forecast team
- Bias trends and patterns
- FY26 Q2 forecast comparison across teams
- Confidence assessment and recommended forecast
Format with clear headers, numbers, and comparison tables.""",

        "Segment Deep Dive": """Write a deep-dive segment analysis covering:
- Current segment distribution and share
- Quarter-over-quarter segment trends
- Emerging segment opportunities
- Sales channel optimization recommendations
Format with clear headers and segment-specific insights.""",

        "Risk Report": """Write a comprehensive risk assessment covering:
- Product lifecycle risk (sustaining, decline, or ramp)
- Forecast accuracy risk
- Big deal concentration risk
- Segment/vertical concentration risk
- Mitigation recommendations
Format with risk levels (High/Medium/Low) and action items.""",
    }

    instruction = report_instructions.get(report_type, report_instructions["Executive Summary"])

    prompt = f"""Generate a {report_type} for the product "{product_name}" in a networking hardware portfolio.

{instruction}

**Product Data Context:**
{data_context}

Write a professional, data-driven report suitable for executive review."""

    return _stream_llm(prompt, max_tokens=2500)


# ─── 7. CHAT WITH DATA ──────────────────────────────────────
def chat_with_data(user_message: str, conversation_history: list, data_context: str):
    """
    Natural language Q&A about the data. Returns a streaming generator.

    Args:
        user_message: User's question
        conversation_history: List of {role, content} dicts
        data_context: Summary of all available data
    """
    system = f"""{AI_SYSTEM_PROMPT}

You have access to the following data context about the product portfolio:
{data_context}

Answer questions accurately based on this data. If you can't find specific information,
say so rather than making up numbers. Use markdown formatting for readability."""

    messages = [{"role": "system", "content": system}] + conversation_history + [{"role": "user", "content": user_message}]

    try:
        client = _get_client()
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1500,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"❌ Error: {str(e)}"


# ─── 8. FULL DASHBOARD REPORT ───────────────────────────────
def generate_full_report(data_context: str):
    """
    Generate a comprehensive multi-section dashboard report. Returns a streaming generator.

    Args:
        data_context: Comprehensive summary of all KPIs, trends, and data points
    """
    prompt = f"""Generate a comprehensive Sales Intelligence Report for a networking hardware product portfolio.

Structure the report with these sections:
1. **Executive Summary** — 4-5 sentences on overall portfolio health
2. **Top Products Performance** — highlight top 5 and bottom 5 products
3. **Forecast Accuracy Assessment** — compare team performance, identify improvement areas
4. **Segment Analysis** — key segment trends and channel insights
5. **Vertical Market Outlook** — growth industries and strategic opportunities
6. **Big Deal Risk Analysis** — concentration risk and forecast stability
7. **Strategic Recommendations** — top 5 actionable recommendations for leadership

**Dashboard Data:**
{data_context}

Write in professional report format with markdown headers, bullet points, and bold emphasis on key numbers.
Make it comprehensive but scannable — suitable for a 5-minute executive read."""

    return _stream_llm(prompt, max_tokens=4000)

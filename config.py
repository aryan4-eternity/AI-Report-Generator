"""
Configuration constants for the CFL Sales Dashboard.
All color palettes, quarter labels, file paths, and model settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── FILE PATH ───────────────────────────────────────────────
FILE_PATH = os.path.join(os.path.dirname(__file__), "CFL_External Data Pack_Phase1.xlsx")

# ─── GROQ CONFIG ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ─── COLOR PALETTES ──────────────────────────────────────────
LIFECYCLE_COLORS = {
    "Sustaining": "#1D9E75",
    "Decline": "#E24B4A",
    "NPI-Ramp": "#EF9F27",
}

SEGMENT_COLORS = {
    "COMMERCIAL": "#378ADD",
    "ENTERPRISE": "#7F77DD",
    "PUBLIC SECTOR": "#1D9E75",
    "SMB": "#EF9F27",
    "SERVICE PROVIDER": "#D85A30",
    "OTHER": "#888780",
}

TEAM_COLORS = {
    "Demand Planners": "#378ADD",
    "Marketing Team": "#EF9F27",
    "Data Science Team": "#1D9E75",
}

# ─── QUARTER LABELS ──────────────────────────────────────────
# Actual bookings quarters: FY23 Q2 through FY26 Q1 (12 quarters)
QUARTER_LABELS = [
    "FY23 Q2", "FY23 Q3", "FY23 Q4",
    "FY24 Q1", "FY24 Q2", "FY24 Q3", "FY24 Q4",
    "FY25 Q1", "FY25 Q2", "FY25 Q3", "FY25 Q4",
    "FY26 Q1",
]

# Forecast accuracy quarters (most recent 3)
ACCURACY_QUARTERS = ["FY25 Q3", "FY25 Q4", "FY26 Q1"]

# Forecast target quarter
FORECAST_TARGET_QUARTER = "FY26 Q2"

# Forecast teams
FORECAST_TEAMS = ["Demand Planners", "Marketing Team", "Data Science Team"]

# Big deal quarters (2024Q2 – 2026Q1 = 8 quarters)
BIG_DEAL_QUARTERS = [
    "2024Q2", "2024Q3", "2024Q4",
    "2025Q1", "2025Q2", "2025Q3", "2025Q4",
    "2026Q1",
]

# SCMS quarters (2023Q1 – 2026Q1 = 13 quarters)
SCMS_QUARTERS = [
    "2023Q1", "2023Q2", "2023Q3", "2023Q4",
    "2024Q1", "2024Q2", "2024Q3", "2024Q4",
    "2025Q1", "2025Q2", "2025Q3", "2025Q4",
    "2026Q1",
]

# Segment names
SEGMENTS = [
    "COMMERCIAL", "ENTERPRISE", "OTHER",
    "PUBLIC SECTOR", "SERVICE PROVIDER", "SMB",
]

# ─── DASHBOARD SETTINGS ──────────────────────────────────────
APP_TITLE = "CFL Sales Intelligence Dashboard"
APP_ICON = "📊"
APP_LAYOUT = "wide"

# Plotly global layout defaults
PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_FONT = dict(family="Inter, sans-serif", size=12, color="#2C2C2C")
PLOTLY_MARGIN = dict(l=40, r=40, t=50, b=40)

# AI system prompt
AI_SYSTEM_PROMPT = (
    "You are a senior sales analytics assistant for a networking hardware company (Cisco). "
    "You analyze product demand data, forecast accuracy, segment trends, vertical markets, "
    "and big deal patterns. Always provide data-backed, actionable insights. "
    "Use markdown formatting with headers, bullet points, and bold text for readability. "
    "Be concise but thorough. Refer to products, quarters, and metrics by their exact names."
)

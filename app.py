"""
CFL Sales Intelligence Dashboard — Main Entry Point
Multi-page Streamlit + Plotly dashboard
"""

import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from streamlit_option_menu import option_menu
from config import APP_TITLE, APP_ICON, APP_LAYOUT, GROQ_API_KEY
from data_loader import load_all_data

# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    layout=APP_LAYOUT,
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    initial_sidebar_state="expanded",
)

# ─── COOKIE MANAGER ──────────────────────────────────────────
cookies = EncryptedCookieManager(
    prefix="cfl_dash_",
    password=os.environ.get("COOKIES_PASSWORD", "default-dev-password-for-cookies-1234")
)

if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.stop()

# ─── CUSTOM CSS ──────────────────────────────────────────────
st.markdown("""
<style>
/* ─── Google Fonts ─────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─── Global ───────────────────────────────── */
html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #ffffff;
    color: #1e1e1e;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

/* ─── Sidebar ──────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    border-right: 1px solid rgba(0,0,0,0.06);
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #6b7689;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 1.2rem;
}

/* ─── KPI Cards ────────────────────────────── */
.kpi-card {
    background: linear-gradient(135deg, rgba(255,255,255,1) 0%, rgba(248,249,250,1) 100%);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}
.kpi-card:hover {
    border-color: rgba(42, 123, 202, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(42, 123, 202, 0.12);
}
.kpi-icon {
    font-size: 1.6rem;
    margin-bottom: 0.3rem;
}
.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #5a6270;
    margin-bottom: 0.3rem;
    font-weight: 500;
}
.kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e1e1e;
    line-height: 1.2;
}
.kpi-delta {
    font-size: 0.78rem;
    margin-top: 0.3rem;
    font-weight: 500;
}

/* ─── AI Insight Box ───────────────────────── */
.ai-box {
    background: linear-gradient(135deg, rgba(29, 158, 117, 0.05) 0%, rgba(42, 123, 202, 0.05) 100%);
    border: 1px solid rgba(29, 158, 117, 0.2);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 1rem 0;
}
.ai-box-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.8rem;
}
.ai-badge {
    background: linear-gradient(135deg, #1D9E75 0%, #2A7BCA 100%);
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}
.ai-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #2c3e50;
}
.ai-box-content {
    font-size: 0.88rem;
    line-height: 1.7;
    color: #4a5568;
}

/* ─── Section Header ───────────────────────── */
.section-header h2 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1e1e1e;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}
.section-subtitle {
    font-size: 0.85rem;
    color: #5a6270;
    margin-top: 0;
}

/* ─── Plotly Charts ────────────────────────── */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
}

/* ─── Buttons ──────────────────────────────── */
.stButton > button {
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    border: 1px solid rgba(0,0,0,0.1);
    color: #1e1e1e;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(42, 123, 202, 0.15);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2A7BCA 0%, #1D9E75 100%);
    border: none;
    color: white;
}

/* ─── Chat Messages ────────────────────────── */
.stChatMessage {
    background: rgba(0,0,0,0.03);
    border-radius: 12px;
    border: 1px solid rgba(0,0,0,0.05);
}

/* ─── Metrics ──────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(0,0,0,0.02);
    border-radius: 12px;
    padding: 0.8rem;
    border: 1px solid rgba(0,0,0,0.06);
}

/* ─── DataFrames ───────────────────────────── */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* ─── Sidebar Nav ──────────────────────────── */
.nav-link {
    display: block;
    padding: 0.65rem 1rem;
    margin: 0.2rem 0;
    border-radius: 10px;
    color: #5a6270;
    text-decoration: none;
    font-size: 0.88rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

/* ─── Dividers ─────────────────────────────── */
hr {
    border-color: rgba(0,0,0,0.08);
    margin: 1.5rem 0;
}

/* ─── Scrollbar ────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.15);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0,0,0,0.25);
}
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
            <div style="font-size: 2rem; margin-bottom: 0.3rem;">📊</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e1e1e; letter-spacing: -0.02em;">
                CFL Sales Intelligence
            </div>
            <div style="font-size: 0.72rem; color: #6b7689; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 0.2rem;">
                AI-Powered Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = option_menu(
        menu_title=None,
        options=["Overview", "Forecast Accuracy", "Segment Analysis", "Vertical Analysis", "Big Deal Intelligence", "AI Report Generator", "ML Forecasting"],
        icons=["bar-chart-fill", "bullseye", "buildings", "industry", "briefcase", "robot", "cpu"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#5a6270", "font-size": "1rem"}, 
            "nav-link": {
                "font-size": "0.9rem", 
                "text-align": "left", 
                "margin": "0.2rem 0", 
                "--hover-color": "rgba(0,0,0,0.05)",
                "color": "#5a6270",
                "font-weight": "500",
                "border-radius": "10px"
            },
            "nav-link-selected": {
                "background-color": "rgba(42, 123, 202, 0.1)", 
                "color": "#2A7BCA", 
                "border-left": "3px solid #2A7BCA",
                "font-weight": "600"
            },
        }
    )

    st.markdown("---")

    # API key input if not in env
    if not GROQ_API_KEY:
        st.markdown("### 🔑 API Configuration")
        
        # Load from cookies if available
        if "groq_api_key" not in st.session_state and cookies.get("groq_api_key"):
            st.session_state["groq_api_key"] = cookies["groq_api_key"]
            
        if "groq_api_key" not in st.session_state or not st.session_state["groq_api_key"]:
            api_key_input = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                key="api_key_input",
            )
            if api_key_input:
                st.session_state["groq_api_key"] = api_key_input
                cookies["groq_api_key"] = api_key_input
                cookies.save()
                st.success("✅ API key set and saved in cookies!")
                st.rerun()
        else:
            st.success("✅ API key active (loaded from cookies/session)")
            if st.button("Clear Saved API Key"):
                st.session_state.pop("groq_api_key", None)
                if "groq_api_key" in cookies:
                    cookies["groq_api_key"] = ""
                    cookies.save()
                st.rerun()




# ─── LOAD DATA ───────────────────────────────────────────────
@st.cache_data(show_spinner="🔄 Loading dashboard data…")
def _load():
    from data_loader import load_all_data
    return load_all_data()


try:
    data = _load()
except Exception as e:
    st.error(f"❌ Failed to load data: {str(e)}")
    st.info("💡 Make sure `CFL_External_Data_Pack_Phase1.xlsx` is in the `sales_dashboard/` directory.")
    st.stop()


# ─── PAGE ROUTING ────────────────────────────────────────────
if page == "Overview":
    from views.overview import render
    render(data)

elif page == "Forecast Accuracy":
    from views.forecast import render
    render(data)

elif page == "Segment Analysis":
    from views.segments import render
    render(data)

elif page == "Vertical Analysis":
    from views.verticals import render
    render(data)

elif page == "Big Deal Intelligence":
    from views.big_deals import render
    render(data)

elif page == "AI Report Generator":
    from views.ai_report import render
    render(data)

elif page == "ML Forecasting":
    from views.ml_forecast import render
    render(data)

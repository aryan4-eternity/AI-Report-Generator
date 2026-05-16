# CFL Sales Intelligence Dashboard

A full-stack **GenAI + ML-powered** sales intelligence dashboard built with Python, Streamlit, XGBoost, and Llama 3 (via Groq). Designed to ingest Cisco CFL product demand data, surface actionable insights through interactive Plotly visualisations, and generate AI-driven analysis — including a purpose-built XGBoost forecasting model that competes directly against human forecast teams.

---

## 🚀 Features

| Page | Description |
|------|-------------|
| 📊 **Portfolio Overview** | Top-level KPIs, quarterly booking trends, lifecycle breakdown, segment donut, AI executive summary |
| 🎯 **Forecast Accuracy** | Grouped bar accuracy, bias heatmap (team × quarter), accuracy vs. volume scatter, AI analysis |
| 🏢 **Segment Analysis** | Stacked bars, 100% share chart, segment trend lines, pivot table, AI insight |
| 🏭 **Vertical Analysis** | Treemap, horizontal stacked bar (top verticals × products), trend lines, AI recommendation |
| 💼 **Big Deal Intelligence** | Deal composition bar, big-deal % line chart, dependency risk chart, AI risk assessment |
| 🤖 **AI Report Generator** | Per-product report in 4 types (Executive / Forecast / Segment / Risk), live chat with data, PDF export |
| 🧠 **ML Forecasting** *(new)* | XGBoost model trained on historical actuals — predicts FY26 Q2 units for all 30 products, compares against 3 human teams, shows holdout validation and feature importances, AI explanation panel |

---

## 🧠 ML Forecasting — How It Works

### Feature Engineering (`data_loader.py → build_ml_features()`)
| Feature | Description |
|---------|-------------|
| `lag_1` – `lag_4` | Units from prior 1–4 quarters |
| `rolling_avg_4` | Mean of last 4 quarters |
| `rolling_std_4` | Std deviation of last 4 quarters |
| `qoq_growth` | Quarter-over-quarter growth rate |
| `yoy_growth` | Year-over-year growth rate |
| `quarter_num` | 1–4 seasonality encoding |
| `product_encoded` | Label-encoded product name |

### Model (`ml_model.py`)
- **Algorithm**: `XGBRegressor` — `n_estimators=200`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.8`
- **Train set**: FY23 Q2 → FY25 Q3
- **Validation (holdout)**: FY25 Q4 + FY26 Q1
- **Predicts**: FY26 Q2 units for all 30 products
- **Persistence**: model saved to `models/xgb_model.joblib`, auto-loaded on next run via `@st.cache_resource`

### Page Layout
- **KPI row**: Model MAPE on validation · Best predicted product · # products where ML beat all 3 human teams
- **Chart 1**: Grouped bar — XGBoost 🟣 vs Demand Planners 🔵 vs Marketing 🟡 vs Data Science 🟢
- **Chart 2**: Line — actual vs predicted on holdout quarters (per-product selector in sidebar)
- **Chart 3**: Horizontal bar — XGBoost feature importances sorted descending
- **AI Panel**: "Explain ML Results" → Groq streams a 5–6 sentence data-backed analysis

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit, streamlit-option-menu |
| **Data Processing** | Pandas, NumPy, OpenPyXL |
| **Visualisations** | Plotly Express & Graph Objects |
| **Machine Learning** | XGBoost, scikit-learn, joblib |
| **AI Engine** | Groq API (LLaMA 3.3 70B) — streaming |
| **PDF Generation** | markdown-pdf |
| **Auth Persistence** | streamlit-cookies-manager |

---

## 📁 Project Structure

```
sales_dashboard/
├── app.py                  # Main entry point, sidebar nav, routing
├── config.py               # Constants: colours, quarter labels, API config
├── data_loader.py          # All Excel parsers + build_ml_features()
├── ml_model.py             # XGBoost train / load / predict / evaluate
├── requirements.txt
├── models/
│   └── xgb_model.joblib    # Trained model (auto-generated on first run)
├── components/
│   ├── ai_engine.py        # All Groq API functions (streaming + non-streaming)
│   ├── charts.py           # Reusable Plotly chart components
│   └── kpi_cards.py        # KPI card, AI insight box, section header helpers
└── views/
    ├── overview.py         # Page 1 — Portfolio Overview
    ├── forecast.py         # Page 2 — Forecast Accuracy
    ├── segments.py         # Page 3 — Segment Analysis
    ├── verticals.py        # Page 4 — Vertical Analysis
    ├── big_deals.py        # Page 5 — Big Deal Intelligence
    ├── ai_report.py        # Page 6 — AI Report Generator
    └── ml_forecast.py      # Page 7 — ML Forecasting
```

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aryan4-eternity/AI-Report-Generator.git
   cd AI-Report-Generator/sales_dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Configuration:**
   - Get a free API key from [Groq Console](https://console.groq.com/keys)
   - Create a `.env` file in `sales_dashboard/` and add:
     ```env
     GROQ_API_KEY=your_api_key_here
     ```
   - *(Or enter it directly in the sidebar when the app is running — it's saved in cookies)*

4. **Add your data file:**
   - Place `CFL_External Data Pack_Phase1.xlsx` inside the `sales_dashboard/` directory

5. **Run the Dashboard:**
   ```bash
   python -m streamlit run app.py
   ```
   The app will open at **http://localhost:8501**

> **Note:** The XGBoost model trains automatically on first run and saves to `models/xgb_model.joblib`. Subsequent runs load the cached model instantly.

---

## 📊 Data Source

Parses `CFL_External Data Pack_Phase1.xlsx` — a multi-sheet Cisco CFL product demand dataset covering:
- **Actual Bookings**: 30 products × 12 quarters (FY23 Q2 – FY26 Q1)
- **Forecast Targets**: FY26 Q2 predictions from 3 teams (Demand Planners, Marketing, Data Science)
- **Forecast Accuracy & Bias**: 3 teams × 3 quarters × 30 products
- **SCMS**: Segment breakdown (6 segments × 13 quarters)
- **VMS**: Vertical/industry breakdown (~15 verticals × 13 quarters)
- **Big Deal**: Big vs. avg deal split (8 quarters)

# AI Report Generator & Sales EDA Dashboard

A GenAI-powered Exploratory Data Analysis (EDA) sales dashboard built with Python, Streamlit, and Llama 3 (via Groq). This project was designed to ingest financial datasets, perform real-time data analysis, and generate automated, AI-driven business intelligence reports.

## 🚀 Features
* **Exploratory Data Analysis (EDA):** Interactive data visualizations and KPI tracking for sales performance, segment trends, and vertical growth.
* **GenAI Report Generation:** Uses the lightning-fast Groq API (Llama 3) to generate comprehensive executive summaries and risk assessments.
* **Natural Language Q&A:** Chat directly with your sales data to uncover hidden insights.
* **PDF Export:** In-memory markdown-to-PDF conversion for easy sharing of AI-generated reports.
* **Modern UI:** Clean, responsive light-themed UI built natively with Streamlit and `streamlit-option-menu`.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **Data Processing:** Pandas, OpenPyXL
* **Visualizations:** Plotly Express
* **AI Engine:** Groq API (Llama 3)
* **PDF Generation:** markdown-pdf

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aryan4-eternity/AI-Report-Generator.git
   cd AI-Report-Generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Configuration:**
   * Get a free API key from [Groq Console](https://console.groq.com/keys).
   * Create a `.env` file in the root directory and add your key:
     ```env
     GROQ_API_KEY=your_api_key_here
     ```
   * *(Alternatively, you can input your API key directly into the sidebar of the application when it is running).*

4. **Run the Dashboard:**
   ```bash
   streamlit run app.py
   ```

## 📊 Data Source
This application is configured to parse the `CFL_External Data Pack_Phase1.xlsx` dataset, analyzing bookings, segment distribution, big deal risks, and forecast accuracy across multiple financial quarters.

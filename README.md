# 📈 Interactive Financial Analytics: Cross-Industry Risk & Return Dashboard

**Interactive Web App | Track 4 Project for ACC102**


## 1. Project Overview & Target Audience
This project provides an interactive platform for analyzing the risk and return profiles of various US stocks across a full 5-year business cycle (2019-2023). Unlike static reports, this tool allows users to dynamically select assets and benchmarks to test financial hypotheses under different macroeconomic conditions (e.g., the COVID-19 crash and the high-interest-rate environment).

**Target Audience:** - **Retail Investors:** To assess asset volatility and capital preservation.
- **Financial Educators:** To demonstrate the trade-off between risk and reward.
- **Portfolio Managers:** To identify defensive vs. offensive sector performance.

## 2. Key Features (Track 4 Interactivity)
- **Dynamic Ticker Input:** Users can enter any valid CRSP ticker symbol (e.g., `TSLA`, `MSFT`, `NVDA`) to pull real-time data from WRDS.
- **Custom Timeframe:** Adjustable date range to analyze specific market events.
- **Automated Metric Calculation:** Real-time computation of Annualized Return, Volatility, Sharpe Ratio, and Maximum Drawdown.
- **Multi-Dimensional Visualisation:** - Cumulative Return curves.
    - "Underwater" Drawdown charts for risk assessment.
    - Risk vs. Return scatter plots.
- **🤖 AI Assistant Module:** An automated prompt generator that converts complex data tables into structured prompts for deep financial analysis via LLMs (like ChatGPT/Claude).

## 3. Methodology & Technical Workflow
The application follows a professional data pipeline:
1.  **Data Acquisition:** Utilizes the `wrds` library to execute **Parameterised SQL queries** directly against the CRSP database.
2.  **Transformation:** Merges stock-level data with the **Market Index (vwretd)** using Pandas `concat` and `rename` operations to ensure column alignment.
3.  **Analytics Engine:** Implements grouped calculations for performance metrics using Lambda functions and rolling maximums.
4.  **UI Framework:** Built with **Streamlit** to provide a seamless, browser-based user experience.

## 4. Business Insights Generated
The tool highlights critical market patterns observed in the default 2019-2023 data:
- **The Tech Premium (AAPL):** High volatility (32%+) compensated by a superior Sharpe Ratio (1.17), confirming its role as an offensive growth driver.
- **The Defensive Shield (JNJ):** Outperformed the market in capital preservation with the lowest Max Drawdown (-27%), proving its resilience during the pandemic.
- **The Utility Trap (NEE):** A counter-intuitive finding where a "safe" asset suffered a -44% drawdown due to its high sensitivity to the aggressive interest rate hikes in 2022-2023.

## 5. How to Run Locally

### Prerequisites
- Python 3.9+
- A valid **WRDS Account** (Institutional subscription required).

### Installation
1. Clone the repository:
   ```bash
   git clone [your-repository-link]
   ```
2. Install the requirements:
   ```bash
   pip install streamlit wrds pandas matplotlib seaborn tabulate
   ```

### Execution
Launch the app via terminal:
```bash
streamlit run app.py
```

## 6. Project Structure
- `app.py`: The core Streamlit application logic.
- `requirements.txt`: List of Python dependencies.
- `README.md`: Project documentation.
- `images/`: Folder containing screenshots of the dashboard.

## 7. Limitations & Professional Practice
- **Data Latency:** Relies on WRDS server response times.
- **Simplification:** Assumes a risk-free rate of 0 for Sharpe Ratio calculations for comparative simplicity.
- **AI Disclosure:** This project utilized AI tools (Gemini/ChatGPT) for UI layout optimization and boilerplate SQL structure, following course guidelines for academic integrity.

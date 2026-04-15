# ACC102_Python_Product： Cross-Industry Asset Allocation: Risk vs. Return Analysis (2019-2023)
# Author: Junqi (Foxton) Zhang

## 1. Project Objective & Target Audience
Traditional financial wisdom suggests that technology stocks offer high risk and high returns, while utility and healthcare stocks serve as defensive, low-risk assets. This project aims to empirically test this assumption under extreme macroeconomic conditions, including the COVID-19 pandemic crash and the subsequent aggressive interest rate hike cycles. 

**Target Audience:** Retail investors, portfolio managers, and personal financial advisors seeking data-driven insights for cross-industry asset allocation and risk management.

## 2. Data Source & Scope
* **Source:** Wharton Research Data Services (WRDS) - CRSP Daily Stock File. 
* **Time Frame:** January 1st, 2019, to December 31st, 2023 (A full 5-year business cycle ex, during and post pandamic shock).
* **Selected Assets:**
  * **AAPL (Apple):** Technology / Offensive Asset
  * **JPM (JPMorgan Chase):** Financials / Cyclical Asset
  * **JNJ (Johnson & Johnson):** Healthcare / Defensive Asset
  * **NEE (NextEra Energy):** Utilities / Defensive Asset
  * **Market_Index (vwretd):** CRSP Value-Weighted Market Index (Benchmark)

## 3. Methodology & Python Workflow

1. **Data Acquisition:** Parameterised SQL queries via the `wrds` Python API to extract daily total returns.
2. **Data Transformation:** Pandas `LEFT JOIN` and `concat` operations to merge individual stock data with the market benchmark, handling missing values and datetime standardisation.
3. **Metric Calculation:** Computed Cumulative Return, Annualized Volatility, Sharpe Ratio, and Maximum Drawdown to evaluate risk-adjusted performance.
4. **Visualisation:** Deployed `matplotlib` and `seaborn` to generate professional business charts (Line charts, Bar charts, and Scatter plots).

## 4. Key Findings & Business Insights
* Please refer to the charts in the `images` in the notebook output

* **The "Tech King" Premium (AAPL):** Despite exhibiting the highest annualized volatility (32.22%), AAPL provided the highest Sharpe Ratio (1.173) and dominated cumulative wealth generation. It effectively compensated investors for the high risk taken, operating as a pure offensive engine.
* **The Ultimate Defensive Shield (JNJ):** JNJ demonstrated an annualized volatility (19.86%) lower than the broader market index (21.08%). The Underwater Drawdown Chart reveals that during both the 2020 pandemic crash and the 2022 bear market, JNJ suffered the shallowest maximum drawdown (-27.36%). It successfully fulfilled its role as a capital preservation asset.
* **The "Interest Rate Trap" for Utilities (NEE):** A counter-intuitive finding emerged regarding the utility sector. Typically viewed as a safe haven, NEE experienced a massive maximum drawdown of -44.99%, underperforming the market benchmark. This reveals that in an aggressive rate-hike macroeconomic environment, heavy-asset, dividend-yielding utility stocks become highly vulnerable to interest rate risks, thus breaking the traditional "low-risk" stereotype.

* Thus, for risk-averse investors, it would be more suitable to focus on the firm in medical and health field.

## 5. How to Run This Project
To reproduce the analysis locally, please follow these steps:

**Step 1: Install Dependencies**
Ensure you have Python installed, then install the required libraries via terminal:
```bash
pip install wrds pandas matplotlib seaborn
```
If your operation system is MacOS 26 above (Like Mine), please use the code below:
```bash
pip3 install wrds pandas matplotlib seaborn
```

**Step 2: WRDS Authentication**
To fetch the data, you must have an active WRDS institutional account. 
When running the `db = wrds.Connection(...)` cell in the Jupyter Notebook, you will be prompted to enter your WRDS username and password.

**Step 3: Execute the Notebook**
Open `Mini_Task.ipynb` and run the cells sequentially. The code will automatically fetch the data via SQL, process the metrics, and output the final visualisations and summary table.

## 6. Limitations
* **Survivorship and Representativeness Bias:** The analysis relies on single dominant stocks (e.g., AAPL for Tech) rather than full industry ETFs, which may not fully represent the systemic risk of the entire sector.
* **Static Benchmark:** The risk-free rate was assumed to be zero for the Sharpe Ratio calculation to simplify the relative comparison. Future iterations should incorporate dynamic Treasury Yield data for absolute precision.


#### Just a heads up, I am a freshman of GitHub, so please let me know if anything was wrong or you would like to discuss something with me.

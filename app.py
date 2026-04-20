import streamlit as st
import wrds
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 页面配置 / Page configuration
st.set_page_config(page_title="Asset Allocation Tool", layout="wide")
st.title("📊 Cross-Industry Asset Allocation Analysis")
st.markdown("Assess risk and return for different stock tickers compared to the Market Index.")

# --- 侧边栏交互输入 / Sidebar Interactive Inputs ---
st.sidebar.header("User Inputs")
wrds_username = st.sidebar.text_input("WRDS Username", value="")
# 保留密码框，直接传递给连接函数，避免权限问题 / Keep password box, pass directly to connection function to avoid permission issues
wrds_password = st.sidebar.text_input("WRDS Password", type="password")
tickers_input = st.sidebar.text_input("Enter Tickers (comma separated)", value="")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2019-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))

run_button = st.sidebar.button("Run Analysis")

# --- 核心分析逻辑 / Core Analysis Logic ---
if run_button:
    if not wrds_username or not wrds_password:
        st.error("Please provide both WRDS username and password.")
    else:
        try:
            with st.spinner('Connecting to WRDS and fetching data...'):

                # 处理输入的股票代码 / Process the ticker inputs
                ticker_list = [t.strip().upper() for t in tickers_input.split(',')]
                formatted_tickers = ", ".join([f"'{t}'" for t in ticker_list])

                # 建立数据库连接，直接传递凭据 / Establish database connection by passing credentials directly
                db = wrds.Connection(wrds_username=wrds_username, wrds_password=wrds_password)

                # 1. 提取个股数据 / 1. Extract stock data
                sql_stocks = f"""
                SELECT b.ticker, a.date, a.ret AS daily_return
                FROM crsp.dsf AS a
                LEFT JOIN crsp.dsenames AS b ON a.permno = b.permno
                WHERE b.ticker IN ({formatted_tickers})
                AND a.date >= '{start_date}' AND a.date <= '{end_date}'
                AND a.date >= b.namedt AND a.date <= b.nameendt
                """
                df_stocks = db.raw_sql(sql_stocks, date_cols=["date"])

                # 2. 提取大盘指数 (vwretd) / 2. Extract market index (vwretd)
                sql_market = f"""
                SELECT date, vwretd AS daily_return
                FROM crsp.dsi
                WHERE date >= '{start_date}' AND date <= '{end_date}'
                """
                df_market = db.raw_sql(sql_market, date_cols=["date"])

                # 关闭数据库连接 / Close database connection
                db.close()

            with st.spinner('Calculating metrics...'):
                # 3. 数据清洗与合并 / 3. Data cleaning and merging
                if 'ret' in df_stocks.columns:
                    df_stocks = df_stocks.rename(columns={'ret': 'daily_return'})
                if 'vwretd' in df_market.columns:
                    df_market = df_market.rename(columns={'vwretd': 'daily_return'})

                df_market['ticker'] = 'Market_Index'
                # 纵向合并数据 / Concatenate data vertically
                df_final = pd.concat([df_stocks, df_market], ignore_index=True)
                df_final = df_final[['ticker', 'date', 'daily_return']]
                df_final = df_final.sort_values(by=["ticker", "date"]).dropna()

                # 4. 指标计算 / 4. Financial metrics calculation

                # 计算累计收益率 / Calculate cumulative return
                df_final['cum_return'] = df_final.groupby('ticker')['daily_return'].transform(
                    lambda x: (1 + x).cumprod())

                # 计算年化收益率、波动率和夏普比率 / Calculate annualized return, volatility and Sharpe ratio
                annual_return = df_final.groupby('ticker')['daily_return'].mean() * 252
                annual_volatility = df_final.groupby('ticker')['daily_return'].std() * (252 ** 0.5)
                sharpe_ratio = annual_return / annual_volatility

                # 计算最大回撤 / Calculate Maximum Drawdown
                df_final['rolling_max'] = df_final.groupby('ticker')['cum_return'].transform(lambda x: x.cummax())
                df_final['drawdown'] = df_final['cum_return'] / df_final['rolling_max'] - 1
                max_drawdown = df_final.groupby('ticker')['drawdown'].min()

                # 计算 126日（半年）滚动年化波动率 / Calculate rolling 126-day (6-month) annualized volatility
                df_final['rolling_vol'] = df_final.groupby('ticker')['daily_return'].transform(
                    lambda x: x.rolling(window=126).std() * (252 ** 0.5))

                # 新增：计算资产相关性矩阵 / New: Calculate Asset Correlation Matrix
                pivot_df = df_final.pivot(index='date', columns='ticker', values='daily_return')
                corr_matrix = pivot_df.corr()

                # 整合汇总表 / Integrate summary table
                metrics_df = pd.DataFrame({
                    'Annual_Return': annual_return,
                    'Annual_Volatility': annual_volatility,
                    'Sharpe_Ratio': sharpe_ratio,
                    'Max_Drawdown': max_drawdown
                }).reset_index()

            st.success("Analysis Complete!")

            # --- 展示结果 / Result Display ---
            st.subheader("Performance Summary Table")
            st.dataframe(metrics_df.style.format(precision=4))

            # --- 可视化部分 / Visualisation Section ---
            st.subheader("Visualisations")
            sns.set_theme(style="whitegrid")

            # 修改点1：将布局改为 8行 1列，并把画布高度拉长到 48 (8x6)
            fig, axes = plt.subplots(8, 1, figsize=(15, 48))

            # 修改点2：将所有的 axes[x, y] 替换为一维的 axes[0] 到 axes[7]
            # 图1：累计收益率 / Chart 1: Cumulative Return
            sns.lineplot(data=df_final, x='date', y='cum_return', hue='ticker', ax=axes[0])
            axes[0].set_title('Cumulative Return (Growth of $1)', fontsize=14, fontweight='bold')
            axes[0].axhline(y=1, color='black', linestyle='--')

            # 图2：水下曲线（回撤）/ Chart 2: Drawdown (Underwater Chart)
            sns.lineplot(data=df_final, x='date', y='drawdown', hue='ticker', ax=axes[1])
            axes[1].set_title('Drawdown Analysis', fontsize=14, fontweight='bold')
            axes[1].axhline(y=0, color='black', linestyle='-')

            # 图3：年化波动率对比 / Chart 3: Annualized Volatility Comparison
            sns.barplot(data=metrics_df.sort_values('Annual_Volatility'), x='ticker', y='Annual_Volatility', ax=axes[2])
            axes[2].set_title('Annualized Volatility (Total Risk)', fontsize=14, fontweight='bold')

            # 图4：风险收益散点图 / Chart 4: Risk vs Return Scatter Plot
            sns.scatterplot(data=metrics_df, x='Annual_Volatility', y='Annual_Return', hue='ticker', s=200, ax=axes[3])
            axes[3].set_title('Risk vs Return Trade-off', fontsize=14, fontweight='bold')
            for i in range(metrics_df.shape[0]):
                axes[3].text(metrics_df['Annual_Volatility'][i] + 0.005, metrics_df['Annual_Return'][i],
                             metrics_df['ticker'][i])

            # 图5：日收益率分布图 / Chart 5: Daily Return Distribution
            sns.kdeplot(data=df_final, x='daily_return', hue='ticker', fill=True, ax=axes[4])
            axes[4].set_title('Distribution of Daily Returns', fontsize=14, fontweight='bold')
            axes[4].set_xlim(-0.1, 0.1)

            # 图6：滚动年化波动率 / Chart 6: Rolling Volatility (126-day)
            sns.lineplot(data=df_final, x='date', y='rolling_vol', hue='ticker', ax=axes[5])
            axes[5].set_title('Rolling 126-day Volatility', fontsize=14, fontweight='bold')

            # 图7：资产相关性热力图 / Chart 7 (New): Asset Correlation Heatmap
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=0, vmax=1, ax=axes[6], square=False, fmt=".2f")
            axes[6].set_title('Asset Correlation Matrix', fontsize=14, fontweight='bold')

            # 图8：收益率箱线图与尾部风险 / Chart 8 (New): Boxplot & Tail Risk
            sns.boxplot(data=df_final, x='ticker', y='daily_return', ax=axes[7], palette="Set2")
            axes[7].set_title('Return Distribution & Tail Risk (Boxplot)', fontsize=14, fontweight='bold')
            axes[7].axhline(y=0, color='black', linestyle='--', linewidth=1)

            plt.tight_layout()
            st.pyplot(fig)  # 在网页显示图表 / Display plots on web

            # --- AI 提示词生成器 / AI Prompt Generator ---
            st.markdown("---")
            st.subheader("🤖 AI Assistant: Automated Insights")
            st.markdown(
                "Copy the prompt below to ChatGPT / Claude / DeepSeek for expert analysis.")

            try:
                md_table = metrics_df.to_markdown(index=False)
                md_corr = corr_matrix.to_markdown()
            except ImportError:
                md_table = metrics_df.to_string(index=False)
                md_corr = corr_matrix.to_string()

            ai_prompt = f"""Act as an expert portfolio manager. 
Based on the metrics and correlation matrix below (covering 2019 to 2023), please provide:

1. A detailed comparison of risk-adjusted returns (Sharpe Ratio) across sectors.
2. An analysis of the Maximum Drawdown, identifying which assets are most resilient.
3. Insights on diversification based on the Correlation Matrix (which assets provide the best hedge?).
4. Observations on tail risks and extreme volatility events.

Performance Table:
{md_table}

Correlation Matrix:
{md_corr}
"""
            st.code(ai_prompt, language="markdown")

        except Exception as e:
            st.error(f"An error occurred / 运行出错: {e}")
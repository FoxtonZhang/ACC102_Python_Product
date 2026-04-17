import streamlit as st
import wrds
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os  # 用于处理文件路径和权限 / for handling file paths and permissions

# 页面配置 / Page configuration
st.set_page_config(page_title="Asset Allocation Tool", layout="wide")
st.title("📊 Cross-Industry Asset Allocation Analysis")
st.markdown("Assess risk and return for different stock tickers compared to the Market Index.")

# --- 交互式输入侧边栏 / Interactive input sidebar ---
st.sidebar.header("User Inputs")
wrds_username = st.sidebar.text_input("WRDS Username", value="")
# Added password input box, set type to password to hide text
wrds_password = st.sidebar.text_input("WRDS Password", type="password")
tickers_input = st.sidebar.text_input("Enter Tickers (comma separated)", value="")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2019-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))

run_button = st.sidebar.button("Run Analysis")

# --- 核心逻辑 / Core Logic ---
if run_button:
    # 检查是否同时提供了用户名和密码 / Check if both username and password are provided
    if not wrds_username or not wrds_password:
        st.error("Please provide both WRDS username and password. / 请输入 WRDS 的用户名和密码。")
    else:
        try:
            with st.spinner('Connecting to WRDS and fetching data...'):

                # --- 核心修改：在云端服务器动态生成 .pgpass 认证文件 / Core modification: Dynamically generate .pgpass credential file on cloud server ---
                pgpass_path = os.path.expanduser("~/.pgpass")
                with open(pgpass_path, "w") as f:
                    f.write(f"wrds-pgdata.wharton.upenn.edu:9737:wrds:{wrds_username}:{wrds_password}\n")
                # 设置正确的文件权限，否则 PostgreSQL 会拒绝读取 / Set correct file permissions, otherwise PostgreSQL will refuse to read
                os.chmod(pgpass_path, 0o600)
                # -------------------------------------------------------------------------------------------------------

                # 处理输入的股票代码 / Process the ticker inputs
                ticker_list = [t.strip().upper() for t in tickers_input.split(',')]
                # 转换为 SQL 语法要求的格式 / Transform to the required SQL syntax
                formatted_tickers = ", ".join([f"'{t}'" for t in ticker_list])

                # 建立数据库连接 / Establish database connection
                db = wrds.Connection(wrds_username=wrds_username)

                # 1. 提取个股数据 / 1. Extract each stock data
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
                # 3. 数据清洗与合并 / 3. Data cleaning and merge
                if 'ret' in df_stocks.columns:
                    df_stocks = df_stocks.rename(columns={'ret': 'daily_return'})
                if 'vwretd' in df_market.columns:
                    df_market = df_market.rename(columns={'vwretd': 'daily_return'})

                df_market['ticker'] = 'Market_Index'
                # 纵向合并两张表 / Concatenate the two tables vertically
                df_final = pd.concat([df_stocks, df_market], ignore_index=True)
                df_final = df_final[['ticker', 'date', 'daily_return']]
                df_final = df_final.sort_values(by=["ticker", "date"]).dropna()

                # 4. 指标计算 / 4. Index calculation

                # 计算累计收益率 / Calculate cumulative return
                df_final['cum_return'] = df_final.groupby('ticker')['daily_return'].transform(
                    lambda x: (1 + x).cumprod())

                # 计算年化收益与波动率 / Calculate annualized return and volatility
                annual_return = df_final.groupby('ticker')['daily_return'].mean() * 252
                annual_volatility = df_final.groupby('ticker')['daily_return'].std() * (252 ** 0.5)
                # 计算夏普比率 / Calculate Sharpe ratio
                sharpe_ratio = annual_return / annual_volatility

                # 计算最大回撤 / Calculate maximum drawdown
                df_final['rolling_max'] = df_final.groupby('ticker')['cum_return'].transform(lambda x: x.cummax())
                df_final['drawdown'] = df_final['cum_return'] / df_final['rolling_max'] - 1
                max_drawdown = df_final.groupby('ticker')['drawdown'].min()

                # 整合为汇总数据框 / Combine into a summary dataframe
                metrics_df = pd.DataFrame({
                    'Annual_Return': annual_return,
                    'Annual_Volatility': annual_volatility,
                    'Sharpe_Ratio': sharpe_ratio,
                    'Max_Drawdown': max_drawdown
                }).reset_index()

            st.success("Analysis Complete!")

            # 输出表格 / Show table output
            st.subheader("Performance Summary Table")
            st.dataframe(metrics_df.style.format(precision=4))

            # 输出图表 / Show diagram
            st.subheader("Visualisations")
            sns.set_theme(style="whitegrid")
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))

            # 图1：累计收益 / Figure 1: Cumulative return
            sns.lineplot(data=df_final, x='date', y='cum_return', hue='ticker', ax=axes[0, 0])
            axes[0, 0].set_title('Cumulative Return')
            axes[0, 0].axhline(y=1, color='black', linestyle='--')

            # 图2：回撤风险 / Figure 2: Drawdown (Risk)
            sns.lineplot(data=df_final, x='date', y='drawdown', hue='ticker', ax=axes[0, 1])
            axes[0, 1].set_title('Drawdown (Risk)')
            axes[0, 1].axhline(y=0, color='black', linestyle='-')

            # 图3：年化波动率 / Figure 3: Annualized Volatility
            sns.barplot(data=metrics_df.sort_values('Annual_Volatility'), x='ticker', y='Annual_Volatility',
                        ax=axes[1, 0])
            axes[1, 0].set_title('Annualized Volatility')

            # 图4：风险与回报散点图 / Figure 4: Scatterplot of risk vs return
            sns.scatterplot(data=metrics_df, x='Annual_Volatility', y='Annual_Return', hue='ticker', s=200,
                            ax=axes[1, 1])
            axes[1, 1].set_title('Risk vs Return')
            # 为散点图添加标签 / Add labels to the scatterplot
            for i in range(metrics_df.shape[0]):
                axes[1, 1].text(metrics_df['Annual_Volatility'][i] + 0.005, metrics_df['Annual_Return'][i],
                                metrics_df['ticker'][i])

            plt.tight_layout()
            st.pyplot(fig)

            # --- AI 提示词生成器 / AI Prompt Generator ---
            st.markdown("---")
            st.subheader("🤖 AI Assistant: Automated Insights")
            st.markdown(
                "Want to get a professional interpretation? Copy the generated prompt below and paste it into ChatGPT or Claude.")

            # 将数据框转换为 Markdown 格式 / Transform dataframe into markdown
            try:
                md_table = metrics_df.to_markdown(index=False)
            except ImportError:
                md_table = metrics_df.to_string(index=False)

            # 组装 AI 提示词 / Assemble AI prompt
            ai_prompt = f"""Act as an expert financial analyst. 
        Based on the risk and return metrics in the table below (covering a 5-year business cycle from 2019 to 2023), please provide:

        1. 3 key business observations comparing the different assets.
        2. An explanation of which asset represents the best risk-adjusted return (using the Sharpe Ratio).
        3. A brief analysis of the Maximum Drawdown risks, particularly concerning the defensive vs. offensive assets.

        Data Table:
        {md_table}
        """
            st.code(ai_prompt, language="markdown")

        except Exception as e:
            # 捕获并显示错误信息 / Catch and display error information
            st.error(f"An error occurred during execution: {e}")

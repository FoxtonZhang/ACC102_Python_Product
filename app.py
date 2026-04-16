import streamlit as st
import wrds
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


st.set_page_config(page_title="Asset Allocation Tool", layout="wide")
st.title("📊 Cross-Industry Asset Allocation Analysis")
st.markdown("Assess risk and return for different stock tickers compared to the Market Index.")

# --- Interactive  inputs ---
st.sidebar.header("User Inputs")
wrds_username = st.sidebar.text_input("WRDS Username", value="junqi_zhang")
tickers_input = st.sidebar.text_input("Enter Tickers (comma separated)", value="AAPL, NEE, JNJ, JPM")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2019-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))

run_button = st.sidebar.button("Run Analysis")

# --- Core Logic ---
if run_button:
    if not wrds_username:
        st.error("Please provide a WRDS username.")
    else:
        try:
            with st.spinner('Connecting to WRDS and fetching data...'):
                # process the ticker inputs
                ticker_list = [t.strip().upper() for t in tickers_input.split(',')]
                # Transform to the required SQL syntax
                formatted_tickers = ", ".join([f"'{t}'" for t in ticker_list])

                db = wrds.Connection(wrds_username=wrds_username)

                # 1. Extract each stock data
                sql_stocks = f"""
                SELECT b.ticker, a.date, a.ret AS daily_return
                FROM crsp.dsf AS a
                LEFT JOIN crsp.dsenames AS b ON a.permno = b.permno
                WHERE b.ticker IN ({formatted_tickers})
                AND a.date >= '{start_date}' AND a.date <= '{end_date}'
                AND a.date >= b.namedt AND a.date <= b.nameendt
                """
                df_stocks = db.raw_sql(sql_stocks, date_cols=["date"])

                # 2. extract S&P 500 index (vwretd)
                sql_market = f"""
                SELECT date, vwretd AS daily_return
                FROM crsp.dsi
                WHERE date >= '{start_date}' AND date <= '{end_date}'
                """
                df_market = db.raw_sql(sql_market, date_cols=["date"])
                db.close()

            with st.spinner('Calculating metrics...'):
                # 3. data cleaning and merge
                if 'ret' in df_stocks.columns:
                    df_stocks = df_stocks.rename(columns={'ret': 'daily_return'})
                if 'vwretd' in df_market.columns:
                    df_market = df_market.rename(columns={'vwretd': 'daily_return'})

                df_market['ticker'] = 'Market_Index'
                df_final = pd.concat([df_stocks, df_market], ignore_index=True)
                df_final = df_final[['ticker', 'date', 'daily_return']]
                df_final = df_final.sort_values(by=["ticker", "date"]).dropna()

                # 4. index calculation
                df_final['cum_return'] = df_final.groupby('ticker')['daily_return'].transform(
                    lambda x: (1 + x).cumprod())

                annual_return = df_final.groupby('ticker')['daily_return'].mean() * 252
                annual_volatility = df_final.groupby('ticker')['daily_return'].std() * (252 ** 0.5)
                sharpe_ratio = annual_return / annual_volatility

                df_final['rolling_max'] = df_final.groupby('ticker')['cum_return'].transform(lambda x: x.cummax())
                df_final['drawdown'] = df_final['cum_return'] / df_final['rolling_max'] - 1
                max_drawdown = df_final.groupby('ticker')['drawdown'].min()

                metrics_df = pd.DataFrame({
                    'Annual_Return': annual_return,
                    'Annual_Volatility': annual_volatility,
                    'Sharpe_Ratio': sharpe_ratio,
                    'Max_Drawdown': max_drawdown
                }).reset_index()

            st.success("Analysis Complete!")

            # show table putput
            st.subheader("Performance Summary Table")
            st.dataframe(metrics_df.style.format(precision=4))

            # show diagram
            st.subheader("Visualisations")
            sns.set_theme(style="whitegrid")
            fig, axes = plt.subplots(2, 2, figsize=(18, 12))

            # Figure 1: cumulative return
            sns.lineplot(data=df_final, x='date', y='cum_return', hue='ticker', ax=axes[0, 0])
            axes[0, 0].set_title('Cumulative Return')
            axes[0, 0].axhline(y=1, color='black', linestyle='--')

            # Figure 2:
            sns.lineplot(data=df_final, x='date', y='drawdown', hue='ticker', ax=axes[0, 1])
            axes[0, 1].set_title('Drawdown (Risk)')
            axes[0, 1].axhline(y=0, color='black', linestyle='-')

            # Figure 3: Volatility
            sns.barplot(data=metrics_df.sort_values('Annual_Volatility'), x='ticker', y='Annual_Volatility',
                        ax=axes[1, 0])
            axes[1, 0].set_title('Annualized Volatility')

            # Figure 4: Scatterplot of risk return
            sns.scatterplot(data=metrics_df, x='Annual_Volatility', y='Annual_Return', hue='ticker', s=200,
                            ax=axes[1, 1])
            axes[1, 1].set_title('Risk vs Return')
            for i in range(metrics_df.shape[0]):
                axes[1, 1].text(metrics_df['Annual_Volatility'][i] + 0.005, metrics_df['Annual_Return'][i],
                                metrics_df['ticker'][i])

            plt.tight_layout()
            st.pyplot(fig)
            # --- AI Prompt Generator ---
            st.markdown("---")
            st.subheader("🤖 AI Assistant: Automated Insights")
            st.markdown(
                "Want to get a professional interpretation? Copy the generated prompt below and paste it into ChatGPT or Claude.")

            # Transform dataframe into markdown
            try:
                md_table = metrics_df.to_markdown(index=False)
            except ImportError:
                md_table = metrics_df.to_string(index=False)

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
            st.error(f"An error occurred during execution: {e}")
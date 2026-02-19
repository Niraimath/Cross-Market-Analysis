import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cross-Market Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.main { background: #0d0f14; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0f14 0%, #111420 100%);
    border-right: 1px solid #1e2230;
}
h1, h2, h3 { font-family: 'Space Mono', monospace; }
.metric-card {
    background: linear-gradient(135deg, #12151f 0%, #1a1f2e 100%);
    border: 1px solid #252a3a;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 8px;
}
.metric-card:hover { border-color: #4f6ef7; transition: border-color 0.2s; }
.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #5a6480;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.75rem;
    font-weight: 700;
    color: #e8ecf8;
    line-height: 1.1;
}
.metric-sub { font-size: 0.72rem; color: #4f6ef7; margin-top: 6px; }
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4f6ef7;
    border-left: 3px solid #4f6ef7;
    padding-left: 10px;
    margin: 1.8rem 0 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── DB helpers ────────────────────────────────────────────────────────────────
def find_db():
    """Search for the database file in common locations relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "mydb (4).db"),                          # same folder
        os.path.join(script_dir, "CROSSMARKET", "mydb (4).db"),           # subfolder
        os.path.join(os.path.dirname(script_dir), "mydb (4).db"),         # parent folder
        os.path.join(os.path.dirname(script_dir), "CROSSMARKET", "mydb (4).db"),
        os.path.join(os.path.expanduser("~"), "Downloads", "mydb (4).db"),
        os.path.join(os.path.expanduser("~"), "Downloads", "CROSSMARKET", "mydb (4).db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]  # return default; will show friendly error below

DB_PATH = find_db()

def get_conn():
    if not os.path.exists(DB_PATH):
        st.error(f"""
### ❌ Database not found

Could not find `mydb (4).db`. Please make sure **app.py and the database file are in the same folder**.

**Searched locations:**
- Same folder as app.py: `{os.path.dirname(os.path.abspath(__file__))}/`
- Subfolder: `{os.path.dirname(os.path.abspath(__file__))}/CROSSMARKET/`

**How to fix:** Copy `mydb (4).db` into the same folder as `app.py` and restart.
        """)
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(show_spinner=False)
def run_query(sql: str, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)

@st.cache_data(show_spinner=False)
def get_bitcoin_coin_id():
    """Find the correct coin_id for Bitcoin."""
    df = run_query("""
        SELECT DISTINCT coin_id FROM crypto_prices
        WHERE LOWER(coin_id) LIKE '%bitcoin%' OR LOWER(coin_id) LIKE '%btc%'
        LIMIT 1
    """)
    if not df.empty:
        return df["coin_id"].iloc[0]
    # Fallback: highest average price
    df2 = run_query("""
        SELECT coin_id, AVG(price_usd) AS avg_p
        FROM crypto_prices GROUP BY coin_id ORDER BY avg_p DESC LIMIT 1
    """)
    return df2["coin_id"].iloc[0] if not df2.empty else None

@st.cache_data(show_spinner=False)
def get_db_date_range():
    """Get the actual date range available across all tables."""
    ranges = []
    for table, col in [("crypto_prices","date"), ("oil_prices","date"), ("stock_prices","date")]:
        try:
            df = run_query(f"SELECT MIN(date({col})) as mn, MAX(date({col})) as mx FROM {table}")
            if not df.empty and df["mn"].iloc[0]:
                ranges.append((
                    pd.to_datetime(df["mn"].iloc[0], format='mixed', dayfirst=False).date(),
                    pd.to_datetime(df["mx"].iloc[0], format='mixed', dayfirst=False).date(),
                ))
        except:
            pass
    if not ranges:
        return date(2022, 1, 1), date.today()
    all_mins = [r[0] for r in ranges]
    all_maxs = [r[1] for r in ranges]
    return min(all_mins), max(all_maxs)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Cross-Market")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🌐 Market Overview", "🛠 SQL Query Runner", "🪙 Top 3 Crypto Analysis"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    

# PAGE 1 – Cross-Market Overview
if page == "🌐 Market Overview":
    st.title("📊 Cross-Market Overview")
    st.caption("Crypto • Oil • Stock Market")

    db_min, db_max = get_db_date_range()

    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=db_min, min_value=db_min, max_value=db_max)
    with col2:
        end_date = st.date_input("End Date", value=db_max, min_value=db_min, max_value=db_max)

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    sd, ed = str(start_date), str(end_date)

    
    btc_id = get_bitcoin_coin_id()
    if not btc_id:
        st.error("Could not find Bitcoin in the database. Check the `crypto_prices` table.")
        with st.expander("Debug: Available coin_ids"):
            st.dataframe(run_query("SELECT DISTINCT coin_id FROM crypto_prices LIMIT 20"))
        st.stop()

    
    sql = """
        WITH all_dates AS (
            SELECT DISTINCT date(date) AS date FROM crypto_prices  WHERE date(date) BETWEEN :sd AND :ed
            UNION
            SELECT DISTINCT date(date) AS date FROM oil_prices     WHERE date(date) BETWEEN :sd AND :ed
            UNION
            SELECT DISTINCT date(date) AS date FROM stock_prices   WHERE date(date) BETWEEN :sd AND :ed
        )
        SELECT
            d.date,
            cp.price_usd  AS bitcoin_price,
            o.price       AS oil_price,
            sp.close      AS sp500_close,
            ni.close      AS nifty_close
        FROM all_dates d
        LEFT JOIN (
            SELECT date(date) AS date, price_usd FROM crypto_prices WHERE coin_id = :btc
        ) cp ON d.date = cp.date
        LEFT JOIN (
            SELECT date(date) AS date, price FROM oil_prices
        ) o ON d.date = o.date
        LEFT JOIN (
            SELECT date(date) AS date, close FROM stock_prices WHERE ticker = '^GSPC'
        ) sp ON d.date = sp.date
        LEFT JOIN (
            SELECT date(date) AS date, close FROM stock_prices WHERE ticker = '^NSEI'
        ) ni ON d.date = ni.date
        ORDER BY d.date DESC
    """

    with st.spinner("Loading market data…"):
        with get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params={"sd": sd, "ed": ed, "btc": btc_id})

    
    df = df[~(df[["bitcoin_price","oil_price","sp500_close","nifty_close"]].isnull().all(axis=1))].copy()
    df["date"] = pd.to_datetime(df["date"], format='mixed', dayfirst=False).dt.normalize()

    if df.empty:
        st.warning("No data found for the selected date range. Try widening the range.")
        with st.expander("🔍 Debug info"):
            st.write("**Bitcoin coin_id detected:**", btc_id)
            st.write("**Crypto date range:**", run_query("SELECT MIN(date(date)) mn, MAX(date(date)) mx FROM crypto_prices"))
            st.write("**Oil date range:**",    run_query("SELECT MIN(date(date)) mn, MAX(date(date)) mx FROM oil_prices"))
            st.write("**Stock date range:**",  run_query("SELECT MIN(date(date)) mn, MAX(date(date)) mx FROM stock_prices"))
            st.write("**Stock tickers:**", run_query("SELECT DISTINCT ticker FROM stock_prices"))
        st.stop()

   
    btc_avg = df["bitcoin_price"].mean()
    oil_avg = df["oil_price"].mean()
    sp_avg  = df["sp500_close"].mean()
    ni_avg  = df["nifty_close"].mean()

    latest_date = df["date"].max().strftime("%Y-%m-%d")
    st.markdown(f'<p style="color:#4f6ef7;font-size:0.8rem;margin:0.5rem 0;">{latest_date}</p>', unsafe_allow_html=True)

  
    m1, m2, m3, m4 = st.columns(4)

    def fmt_val(v, decimals=2):
        if pd.isna(v): return "N/A"
        return f"{v:,.{decimals}f}"

    with m1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">₿ Bitcoin Avg ($)</div>
            <div class="metric-value">{fmt_val(btc_avg, 2)}</div>
            <div class="metric-sub">USD average</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">🛢 Oil Avg ($)</div>
            <div class="metric-value">{fmt_val(oil_avg, 2)}</div>
            <div class="metric-sub">USD/barrel average</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">🇺🇸 S&P 500 Avg</div>
            <div class="metric-value">{fmt_val(sp_avg, 2)}</div>
            <div class="metric-sub">Index pts average</div>
        </div>""", unsafe_allow_html=True)

    with m4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">🇮🇳 NIFTY Avg</div>
            <div class="metric-value">{fmt_val(ni_avg, 2)}</div>
            <div class="metric-sub">Index pts average</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    
    st.markdown('<div class="section-header">Normalized Price Trends (Base = 100)</div>', unsafe_allow_html=True)

    plot_df = df.sort_values("date").set_index("date")[
        ["bitcoin_price","oil_price","sp500_close","nifty_close"]
    ].copy()

    for c in plot_df.columns:
        first = plot_df[c].dropna()
        if not first.empty:
            plot_df[c] = plot_df[c] / first.iloc[0] * 100

    norm = plot_df.reset_index().melt(id_vars="date", var_name="Market", value_name="Value")
    norm["Market"] = norm["Market"].map({
        "bitcoin_price": "Bitcoin",
        "oil_price": "Crude Oil",
        "sp500_close": "S&P 500",
        "nifty_close": "NIFTY 50",
    })

    fig = px.line(
        norm.dropna(), x="date", y="Value", color="Market",
        color_discrete_map={
            "Bitcoin":   "#f7931a",
            "Crude Oil": "#4fd1c5",
            "S&P 500":   "#4f6ef7",
            "NIFTY 50":  "#e879f9",
        },
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="#12151f", plot_bgcolor="#0d0f14",
        legend=dict(bgcolor="#12151f", bordercolor="#252a3a"),
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        yaxis_title="Normalized Value (Base=100)",
    )
    st.plotly_chart(fig, use_container_width=True)

    
    st.markdown('<div class="section-header">📋 Daily Market Snapshot</div>', unsafe_allow_html=True)

    snap = df.copy()
    snap["date"] = snap["date"].dt.strftime("%Y-%m-%d")
    snap = snap.rename(columns={
        "bitcoin_price": "bitcoin_price",
        "oil_price":     "oil_price",
        "sp500_close":   "sp500",
        "nifty_close":   "nifty",
    })

    def safe_fmt(x, decimals=4):
        try:
            if pd.isna(x): return "—"
            return f"{x:,.{decimals}f}"
        except:
            return str(x)

    st.dataframe(
        snap.style.format({
            "bitcoin_price": lambda x: safe_fmt(x, 4),
            "oil_price":     lambda x: safe_fmt(x, 2),
            "sp500":         lambda x: safe_fmt(x, 4),
            "nifty":         lambda x: safe_fmt(x, 4),
        }),
        use_container_width=True,
        height=420,
    )


# PAGE 2 – SQL Query Runner

elif page == "🛠 SQL Query Runner":
    st.title("🛠 SQL Query Runner")

    
    QUERY_GROUPS = {
        "📊 Cryptocurrencies (Metadata)": {
            "1. Top 3 Cryptocurrencies by Market Cap": """SELECT name, market_cap
FROM cryptocurrencies
ORDER BY market_cap DESC
LIMIT 3;""",
            "2. Coins Where Circulating Supply > 90% of Total": """SELECT name, circulating_supply, total_supply
FROM cryptocurrencies
WHERE circulating_supply >= 0.9 * total_supply;""",
            "3. Coins Within 10% of All-Time High (ATH)": """SELECT name, current_price, ath
FROM cryptocurrencies
WHERE current_price >= 0.9 * ath;""",
            "4. Avg Market Cap Rank of Coins With Volume > $1B": """SELECT AVG(market_cap_rank) AS avg_rank
FROM cryptocurrencies
WHERE total_volume > 1000000000;""",
            "5. Most Recently Updated Coin": """SELECT name, last_updated
FROM cryptocurrencies
ORDER BY last_updated DESC
LIMIT 1;""",
        },
        "💰 Crypto Prices (Daily)": {
            "6. Highest Bitcoin Price (Last 365 Days)": """SELECT MAX(price_usd) AS max_price
FROM crypto_prices
WHERE coin_id = 'bitcoin'
AND date(date) >= DATE('now', '-365 day');""",
            "7. Average Ethereum Price (Past 1 Year)": """SELECT ROUND(AVG(price_usd), 2) AS avg_price
FROM crypto_prices
WHERE coin_id = 'ethereum'
AND date(date) >= DATE('now', '-365 day');""",
            "8. Bitcoin Daily Price Trend in 2025": """SELECT date(date) AS date, price_usd
FROM crypto_prices
WHERE coin_id = 'bitcoin'
AND date(date) BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY date;""",
            "9. Coin With Highest Average Price (All Time)": """SELECT coin_id, ROUND(AVG(price_usd), 2) AS avg_price
FROM crypto_prices
GROUP BY coin_id
ORDER BY avg_price DESC
LIMIT 1;""",
            "10. Bitcoin % Price Change (Sep 2024 to Sep 2025)": """SELECT
  ROUND((MAX(price_usd) - MIN(price_usd)) * 100.0 / MIN(price_usd), 2) AS pct_change
FROM crypto_prices
WHERE coin_id = 'bitcoin'
AND date(date) BETWEEN '2024-09-01' AND '2025-09-30';""",
        },
        "🛢 Oil Prices": {
            "11. Highest Oil Price (Last 5 Years)": """SELECT ROUND(MAX(price), 2) AS max_oil_price
FROM oil_prices
WHERE date(date) >= DATE('now', '-5 years');""",
            "12. Average Oil Price Per Year": """SELECT strftime('%Y', date) AS year,
       ROUND(AVG(price), 2) AS avg_price
FROM oil_prices
GROUP BY year
ORDER BY year;""",
            "13. Oil Prices During COVID Crash (Mar–Apr 2020)": """SELECT date(date) AS date, price
FROM oil_prices
WHERE date(date) BETWEEN '2020-03-01' AND '2020-04-30'
ORDER BY date;""",
            "14. Lowest Oil Price (All Time)": """SELECT ROUND(MIN(price), 2) AS min_oil_price
FROM oil_prices;""",
            "15. Oil Price Volatility Per Year (Max - Min)": """SELECT strftime('%Y', date) AS year,
       ROUND(MAX(price) - MIN(price), 2) AS volatility
FROM oil_prices
GROUP BY year
ORDER BY year;""",
        },
        "📈 Stock Prices": {
            "16. All Stock Prices for S&P 500 (^GSPC)": """SELECT date(date) AS date, open, high, low, close, volume
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY date DESC
LIMIT 100;""",
            "17. Highest Closing Price for NASDAQ (^IXIC)": """SELECT ROUND(MAX(close), 2) AS max_close
FROM stock_prices
WHERE ticker = '^IXIC';""",
            "18. Top 5 Days With Highest Price Spread for S&P 500": """SELECT date(date) AS date,
       ROUND(high - low, 2) AS spread
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY spread DESC
LIMIT 5;""",
            "19. Monthly Average Closing Price Per Ticker": """SELECT ticker,
       strftime('%Y-%m', date) AS month,
       ROUND(AVG(close), 2) AS avg_close
FROM stock_prices
GROUP BY ticker, month
ORDER BY ticker, month;""",
            "20. Average Trading Volume of NSEI in 2024": """SELECT ROUND(AVG(volume), 0) AS avg_volume
FROM stock_prices
WHERE ticker = '^NSEI'
AND strftime('%Y', date) = '2024';""",
        },
        "🔗 Cross-Market Join Queries": {
            "21. Bitcoin vs Oil Average Price in 2025": """SELECT
  ROUND(AVG(cp.price_usd), 2) AS avg_bitcoin,
  ROUND(AVG(op.price), 2)     AS avg_oil
FROM crypto_prices cp
JOIN oil_prices op ON date(cp.date) = date(op.date)
WHERE cp.coin_id = 'bitcoin'
AND date(cp.date) BETWEEN '2025-01-01' AND '2025-12-31';""",
            "22. Bitcoin vs S&P 500 (Correlation Check)": """SELECT date(cp.date) AS date,
       cp.price_usd AS bitcoin_price,
       sp.close     AS sp500_close
FROM crypto_prices cp
JOIN stock_prices sp ON date(cp.date) = date(sp.date)
WHERE cp.coin_id = 'bitcoin'
AND sp.ticker = '^GSPC'
ORDER BY date DESC
LIMIT 60;""",
            "23. Ethereum vs NASDAQ Daily Prices in 2025": """SELECT date(cp.date) AS date,
       cp.price_usd AS ethereum_price,
       sp.close     AS nasdaq_close
FROM crypto_prices cp
JOIN stock_prices sp ON date(cp.date) = date(sp.date)
WHERE cp.coin_id = 'ethereum'
AND sp.ticker = '^IXIC'
AND date(cp.date) BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY date;""",
            "24. Oil Price Spikes vs Bitcoin Price Change": """SELECT date(op.date) AS date,
       op.price          AS oil_price,
       cp.price_usd      AS bitcoin_price
FROM oil_prices op
JOIN crypto_prices cp ON date(op.date) = date(cp.date)
WHERE cp.coin_id = 'bitcoin'
ORDER BY op.price DESC
LIMIT 20;""",
            "25. Top 3 Crypto Coins vs NIFTY (^NSEI) 2025": """SELECT date(cp.date) AS date,
       cp.coin_id,
       cp.price_usd AS crypto_price,
       sp.close     AS nifty_close
FROM crypto_prices cp
JOIN stock_prices sp ON date(cp.date) = date(sp.date)
WHERE sp.ticker = '^NSEI'
AND date(cp.date) BETWEEN '2025-01-01' AND '2025-12-31'
AND cp.coin_id IN (
    SELECT coin_id FROM crypto_prices
    GROUP BY coin_id ORDER BY AVG(price_usd) DESC LIMIT 3
)
ORDER BY date, cp.coin_id;""",
            "26. S&P 500 vs Crude Oil on Same Dates": """SELECT date(sp.date) AS date,
       sp.close  AS sp500_close,
       op.price  AS oil_price
FROM stock_prices sp
JOIN oil_prices op ON date(sp.date) = date(op.date)
WHERE sp.ticker = '^GSPC'
ORDER BY date DESC
LIMIT 60;""",
            "27. Bitcoin vs Crude Oil (Same Date Correlation)": """SELECT date(cp.date) AS date,
       cp.price_usd AS bitcoin_price,
       op.price     AS oil_price
FROM crypto_prices cp
JOIN oil_prices op ON date(cp.date) = date(op.date)
WHERE cp.coin_id = 'bitcoin'
ORDER BY date DESC
LIMIT 60;""",
            "28. NASDAQ vs Ethereum Price Trends": """SELECT date(sp.date) AS date,
       sp.close     AS nasdaq_close,
       cp.price_usd AS ethereum_price
FROM stock_prices sp
JOIN crypto_prices cp ON date(sp.date) = date(cp.date)
WHERE sp.ticker = '^IXIC'
AND cp.coin_id = 'ethereum'
ORDER BY date DESC
LIMIT 60;""",
            "29. Top 3 Crypto Coins Joined with Stock Indices (2025)": """SELECT date(cp.date) AS date,
       cp.coin_id,
       cp.price_usd AS crypto_price,
       sp.ticker,
       sp.close     AS stock_close
FROM crypto_prices cp
JOIN stock_prices sp ON date(cp.date) = date(sp.date)
WHERE date(cp.date) BETWEEN '2025-01-01' AND '2025-12-31'
AND cp.coin_id IN (
    SELECT coin_id FROM crypto_prices
    GROUP BY coin_id ORDER BY AVG(price_usd) DESC LIMIT 3
)
AND sp.ticker IN ('^GSPC', '^NSEI', '^IXIC')
ORDER BY date, cp.coin_id, sp.ticker;""",
            "30. Multi-Join: Stocks + Oil + Bitcoin (Daily)": """SELECT date(cp.date) AS date,
       cp.price_usd AS bitcoin_price,
       op.price     AS oil_price,
       sp.close     AS sp500_close
FROM crypto_prices cp
JOIN oil_prices op   ON date(cp.date) = date(op.date)
JOIN stock_prices sp ON date(cp.date) = date(sp.date)
WHERE cp.coin_id = 'bitcoin'
AND sp.ticker = '^GSPC'
ORDER BY date DESC
LIMIT 60;""",
        },
    }

    
    PREDEFINED = {}
    for group_queries in QUERY_GROUPS.values():
        PREDEFINED.update(group_queries)

    st.markdown('<div class="section-header">Select a Query</div>', unsafe_allow_html=True)

    cat_col, q_col = st.columns([1, 2])
    with cat_col:
        category = st.selectbox("Category", list(QUERY_GROUPS.keys()), label_visibility="visible")
    with q_col:
        query_names = list(QUERY_GROUPS[category].keys())
        selected_name = st.selectbox("Query", query_names, label_visibility="visible")

    selected = PREDEFINED[selected_name]
    st.code(selected.strip(), language="sql")

    if st.button("▶  Run Query", use_container_width=True):
        try:
            with st.spinner("Executing…"):
                result = run_query(selected)
            st.success(f"✅ {len(result)} row(s) returned")
            st.dataframe(result, use_container_width=True)

            num_cols = result.select_dtypes(include="number").columns.tolist()
            if len(result) > 1 and num_cols:
                x_col = result.columns[0]
                # Use line chart if first column looks like a date/time series
                is_timeseries = (
                    "date" in str(x_col).lower() or
                    "month" in str(x_col).lower() or
                    "year" in str(x_col).lower()
                )
                color_col = None
                if "coin_id" in result.columns:
                    color_col = "coin_id"
                elif "ticker" in result.columns:
                    color_col = "ticker"

                if is_timeseries and len(num_cols) >= 1:
                    fig2 = px.line(
                        result, x=x_col, y=num_cols[0],
                        color=color_col,
                        template="plotly_dark",
                        color_discrete_sequence=["#4f6ef7","#f7931a","#4fd1c5","#e879f9","#facc15"],
                    )
                else:
                    fig2 = px.bar(
                        result, x=x_col, y=num_cols[0],
                        color=color_col,
                        template="plotly_dark",
                        color_discrete_sequence=["#4f6ef7","#f7931a","#4fd1c5","#e879f9","#facc15"],
                    )
                fig2.update_layout(
                    paper_bgcolor="#12151f", plot_bgcolor="#0d0f14",
                    margin=dict(l=10, r=10, t=10, b=10),
                    hovermode="x unified",
                    legend=dict(bgcolor="#12151f", bordercolor="#252a3a"),
                )
                st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Query error: {e}")


# PAGE 3 – Top 3 Crypto Analysis

elif page == "🪙 Top 3 Crypto Analysis":
    st.title("🪙 Top 3 Crypto Analysis")

    @st.cache_data(show_spinner=False)
    def get_top3():
        
        df = run_query("""
            SELECT coin_id, price_usd
            FROM crypto_prices
            WHERE date(date) = (
                SELECT MAX(date(date)) FROM crypto_prices AS cp2
                WHERE cp2.coin_id = crypto_prices.coin_id
            )
            GROUP BY coin_id
            ORDER BY price_usd DESC
            LIMIT 3
        """)
        if len(df) < 3:
            
            df = run_query("""
                SELECT coin_id, AVG(price_usd) AS avg_p
                FROM crypto_prices
                GROUP BY coin_id
                ORDER BY avg_p DESC
                LIMIT 3
            """)
        return df["coin_id"].tolist() if not df.empty else []

    top3 = get_top3()
    if not top3:
        st.warning("No cryptocurrency data found.")
        st.stop()

    
    @st.cache_data(show_spinner=False)
    def get_coin_display_names(coin_ids):
        placeholders = ",".join(["?" for _ in coin_ids])
        df = run_query(
            f"SELECT id, name, symbol FROM cryptocurrencies WHERE LOWER(id) IN ({placeholders})",
            tuple(c.lower() for c in coin_ids)
        )
        mapping = {}
        for _, row in df.iterrows():
            mapping[row["id"]] = f"{row['name']} ({row['symbol'].upper()})"
        return mapping

    name_map = get_coin_display_names(tuple(top3))
    display_labels = [name_map.get(c, c.title()) for c in top3]
    label_to_id = dict(zip(display_labels, top3))

    db_min, db_max = get_db_date_range()

    st.markdown('<div class="section-header">Filters</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        selected_label = st.selectbox("Select Coin", display_labels)
        coin = label_to_id[selected_label]
    with c2:
        start_c = st.date_input("From", value=db_min, key="cs")
    with c3:
        end_c = st.date_input("To", value=db_max, key="ce")

    if start_c > end_c:
        st.error("Invalid date range.")
        st.stop()

    cdf = run_query(
        "SELECT date(date) AS date, price_usd FROM crypto_prices WHERE coin_id=? AND date(date) BETWEEN ? AND ? ORDER BY date(date)",
        (coin, str(start_c), str(end_c))
    )
    if cdf.empty:
        st.warning("No data for selected coin and date range.")
        st.stop()

    cdf["date"] = pd.to_datetime(cdf["date"], format='mixed', dayfirst=False).dt.normalize()

    st.markdown('<div class="section-header">Price Statistics</div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    for col, label, val in [
        (s1, "Current Price", cdf["price_usd"].iloc[-1]),
        (s2, "All-Time High",  cdf["price_usd"].max()),
        (s3, "All-Time Low",   cdf["price_usd"].min()),
        (s4, "Average Price",  cdf["price_usd"].mean()),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">${val:,.2f}</div>
                <div class="metric-sub">USD</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-header">{coin.upper()} Daily Price</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=cdf["date"], y=cdf["price_usd"],
        mode="lines", name=coin.upper(),
        line=dict(color="#f7931a", width=2),
        fill="tozeroy", fillcolor="rgba(247,147,26,0.07)",
    ))
    fig3.update_layout(
        template="plotly_dark", paper_bgcolor="#12151f", plot_bgcolor="#0d0f14",
        hovermode="x unified", margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="Price (USD)", xaxis_title="Date",
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-header">Raw Data</div>', unsafe_allow_html=True)
    display_c = cdf.copy()
    display_c["date"] = display_c["date"].dt.strftime("%Y-%m-%d")
    display_c.columns = ["Date", "Price (USD)"]
    st.dataframe(display_c.style.format({"Price (USD)": "${:,.4f}"}), use_container_width=True, height=350)

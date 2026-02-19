# Cross-Market-Analysis
Cross-Market Analysis: Crypto, Oil &amp; Stock Markets using Python, SQL and Streamlit.
# Cross-Market Analysis: Crypto, Oil & Stocks 📊
---
## What this project actually does

Three pages, each focused on something different:

**Page 1 — Market Overview**
Pick a date range and get a snapshot of how Bitcoin, crude oil, the S&P 500, and NIFTY 50 moved together (or didn't). There's a normalized trend chart that puts all four on the same scale so you can actually compare them visually, plus average metrics and a daily data table.

**Page 2 — SQL Query Runner**
30 pre-written SQL queries organized into 5 categories. You pick a category, pick a query, and it runs against the live database — returns a table and auto-generates a chart. Covers everything from "what was the highest Bitcoin price in the last year" to multi-table joins comparing crypto with oil and stock indices on the same dates.

**Page 3 — Top 3 Crypto Analysis**
Automatically detects the top 3 cryptocurrencies by latest price, lets you pick one, filter by date, and see a full price history with stats (current price, ATH, ATL, average).

---

## The data tables

Four SQLite tables, all stored locally in `mydb (4).db`:

- `cryptocurrencies` — metadata: market cap, circulating supply, ATH, volume, etc.
- `crypto_prices` — daily prices for top coins (USD)
- `oil_prices` — daily crude oil prices
- `stock_prices` — daily OHLCV data for S&P 500 (`^GSPC`), NIFTY 50 (`^NSEI`), and NASDAQ (`^IXIC`)

---

## Tech stack

| What | Why |
|------|-----|
| Python | Core language |
| Streamlit | Web app framework |
| SQLite3 | Local database |
| Pandas | Data wrangling |
| Plotly Express | Interactive charts |

No external APIs. No paid services. Everything runs locally off the database file.

---

## Running it locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/cross-market-analysis.git
cd cross-market-analysis
```

**2. Install dependencies**
```bash
pip install streamlit pandas plotly
```

**3. Make sure the database file is in the same folder as `app.py`**

The app looks for `mydb (4).db` in the same directory. If it can't find it, it'll tell you exactly where it's looking.

**4. Run**
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Some things worth noting

- Markets don't trade every day — weekends, holidays, different time zones. The queries handle missing dates with LEFT JOINs rather than dropping rows, so you don't lose crypto data just because oil didn't trade that day.
- The normalized chart on Page 1 sets everything to base 100 so you can compare directional movement regardless of price scale (Bitcoin at $90k vs oil at $70 wouldn't make sense on the same axis otherwise).
- All 30 SQL queries in Page 2 are real, runnable queries — not placeholders. Some of the join queries across 3 tables are actually useful for spotting correlations.

---

## Project structure

```
cross-market-analysis/
├── app.py              # Main Streamlit app (single file)
├── mydb (4).db         # SQLite database with all market data
└── README.md
```

---

Tools: Python · SQL · Streamlit · Plotly · SQLite



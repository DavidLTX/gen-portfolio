#!/usr/bin/env python3
"""
update_prices.py
Fetches latest prices for UPRO, VUAA (EUR→USD), and SPX.
Updates the <!-- PRICE_DATA_START/END --> JSON block in gen_portfolio_dashboard.html.
Run by GitHub Actions daily on weekdays at 10 PM UTC (5 AM SGT next day).
"""

import json
import re
import sys
from datetime import datetime, timezone

import yfinance as yf

# ── Portfolio constants ───────────────────────────────────────────────────
UPRO_SHARES      = 74
VUAA_SHARES      = 59
UPRO_COST_BASIS  = 6756.44
VUAA_COST_BASIS  = 7155.90
TOTAL_COST       = 13912.34
CASH             = 124.65
YEAR1_END_NAV    = 15163.75
YEAR1_SNAPSHOT_PNL = 2134.21
HTML_FILE        = "gen_portfolio_dashboard.html"

def fetch_prices():
    tickers = yf.Tickers("UPRO VUAA.AS EURUSD=X ^GSPC")
    upro_price  = tickers.tickers["UPRO"].fast_info.last_price
    vuaa_eur    = tickers.tickers["VUAA.AS"].fast_info.last_price
    eur_usd     = tickers.tickers["EURUSD=X"].fast_info.last_price
    spx_price   = tickers.tickers["^GSPC"].fast_info.last_price
    vuaa_price  = vuaa_eur * eur_usd
    return upro_price, vuaa_price, spx_price

def build_data(upro_p, vuaa_p, spx_p):
    upro_v   = upro_p * UPRO_SHARES
    vuaa_v   = vuaa_p * VUAA_SHARES
    stocks   = upro_v + vuaa_v
    nav      = stocks + CASH
    upro_pnl = upro_v - UPRO_COST_BASIS
    vuaa_pnl = vuaa_v - VUAA_COST_BASIS
    tot_pnl  = upro_pnl + vuaa_pnl
    nav_chg  = nav - YEAR1_END_NAV
    today    = datetime.now(timezone.utc).strftime("%-d %b %Y")

    return {
        "upro_price":     round(upro_p,  2),
        "vuaa_price":     round(vuaa_p,  2),
        "spx_price":      round(spx_p,   2),
        "nav":            round(nav,      2),
        "nav_change":     round(nav_chg,  2),
        "nav_change_pct": round(nav_chg / YEAR1_END_NAV * 100, 2),
        "upro_value":     round(upro_v,   2),
        "vuaa_value":     round(vuaa_v,   2),
        "stocks_total":   round(stocks,   2),
        "upro_pnl":       round(upro_pnl, 2),
        "vuaa_pnl":       round(vuaa_pnl, 2),
        "total_pnl":      round(tot_pnl,  2),
        "upro_pnl_pct":   round(upro_pnl / UPRO_COST_BASIS * 100, 2),
        "vuaa_pnl_pct":   round(vuaa_pnl / VUAA_COST_BASIS * 100, 2),
        "total_pnl_pct":  round(tot_pnl  / TOTAL_COST      * 100, 2),
        "vs_yr1":         round(tot_pnl  - YEAR1_SNAPSHOT_PNL,    2),
        "last_updated":   today,
    }

def update_html(data):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    new_block = (
        "<!-- PRICE_DATA_START -->\n"
        f"<script id=\"price-data\" type=\"application/json\">\n"
        f"{json.dumps(data, indent=2)}\n"
        "</script>\n"
        "<!-- PRICE_DATA_END -->"
    )
    html, n = re.subn(
        r"<!-- PRICE_DATA_START -->.*?<!-- PRICE_DATA_END -->",
        new_block, html, flags=re.DOTALL
    )
    if n == 0:
        print("ERROR: PRICE_DATA block not found in HTML.", file=sys.stderr)
        sys.exit(1)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {HTML_FILE} with prices as of {data['last_updated']}")

if __name__ == "__main__":
    print("Fetching prices...")
    upro_p, vuaa_p, spx_p = fetch_prices()
    print(f"  UPRO: ${upro_p:.2f}  VUAA: ${vuaa_p:.2f}  SPX: ${spx_p:.2f}")
    data = build_data(upro_p, vuaa_p, spx_p)
    update_html(data)
    print("Done.")

from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {"symbol": "AAPL", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "chart_symbol": "NASDAQ:TSLA"},
]

def safe_float(value):
    try:
        return round(float(value), 2)
    except Exception:
        return None

def get_period_high_low(df, days):
    sub = df.tail(days)
    if sub.empty:
        return None, None
    high_val = sub["High"].max()
    low_val = sub["Low"].min()
    return safe_float(high_val), safe_float(low_val)

def get_stock(symbol, chart_symbol):
    try:
        df = yf.download(
            symbol,
            period="1y",
            interval="1d",
            progress=False,
            auto_adjust=True,
            threads=False
        )

        if df is None or df.empty:
            return None

        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()

        if len(close) < 5:
            return None

        price = safe_float(close.iloc[-1])
        daily_high = safe_float(high.iloc[-1])
        daily_low = safe_float(low.iloc[-1])

        weekly_high, weekly_low = get_period_high_low(df, 5)
        monthly_high, monthly_low = get_period_high_low(df, 21)
        high_3m, low_3m = get_period_high_low(df, 63)
        high_6m, low_6m = get_period_high_low(df, 126)
        high_9m, low_9m = get_period_high_low(df, 189)
        high_12m, low_12m = get_period_high_low(df, 252)

        return {
            "symbol": symbol,
            "chart_symbol": chart_symbol,
            "price": price,
            "signal": "HOLD",
            "confidence": 50.0,
            "daily_high": daily_high,
            "daily_low": daily_low,
            "weekly_high": weekly_high,
            "weekly_low": weekly_low,
            "monthly_high": monthly_high,
            "monthly_low": monthly_low,
            "high_3m": high_3m,
            "low_3m": low_3m,
            "high_6m": high_6m,
            "low_6m": low_6m,
            "high_9m": high_9m,
            "low_9m": low_9m,
            "high_12m": high_12m,
            "low_12m": low_12m,
        }
    except Exception:
        return None

@app.route("/")
def home():
    scored = []

    for stock in STOCKS:
        item = get_stock(stock["symbol"], stock["chart_symbol"])
        if item:
            scored.append(item)

    if not scored:
        scored = [{
            "symbol": "AAPL",
            "chart_symbol": "NASDAQ:AAPL",
            "price": 180.00,
            "signal": "HOLD",
            "confidence": 50.0,
            "daily_high": 182.00,
            "daily_low": 178.00,
            "weekly_high": 183.00,
            "weekly_low": 177

from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime
import math
import pandas as pd

app = Flask(__name__)

stocks = [
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "NASDAQ", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ", "currency": "USD"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "NASDAQ", "currency": "USD"},
    {"symbol": "AZN.L", "name": "AstraZeneca plc", "market": "LSE", "currency": "GBP"},
    {"symbol": "HSBA.L", "name": "HSBC Holdings plc", "market": "LSE", "currency": "GBP"},
    {"symbol": "BARC.L", "name": "Barclays plc", "market": "LSE", "currency": "GBP"},
    {"symbol": "0700.HK", "name": "Tencent Holdings Ltd.", "market": "HKEX", "currency": "HKD"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "market": "NSE", "currency": "INR"},
]

def clean_num(value):
    try:
        if value is None or pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return "-"
        return round(float(value), 2)
    except Exception:
        return "-"

def get_signal(price, ma50, ma200):
    if price is None or pd.isna(price):
        return "HOLD", 0
    if ma50 is None or pd.isna(ma50):
        return "HOLD", 40
    if ma200 is None or pd.isna(ma200):
        if price > ma50:
            return "BUY", 65
        if price < ma50:
            return "SELL", 65
        return "HOLD", 50

    if price > ma50 and ma50 > ma200:
        return "BUY", 85
    if price < ma50 and ma50 < ma200:
        return "SELL", 85
    return "HOLD", 55

def range_high_low(hist, days):
    sub = hist.tail(days)
    if sub.empty:
        return "-", "-"
    high_val = clean_num(sub["High"].max())
    low_val = clean_num(sub["Low"].min())
    return high_val, low_val

@app.route("/")
def index():
    selected_symbol = request.args.get("symbol", stocks[0]["symbol"])
    scored = []

    for s in stocks:
        try:
            ticker = yf.Ticker(s["symbol"])
            hist = ticker.history(period="1y", auto_adjust=False)

            if hist.empty:
                scored.append({
                    **s,
                    "price": "-",
                    "signal": "HOLD",
                    "confidence": 0,
                    "d_high": "-",
                    "d_low": "-",
                    "w_high": "-",
                    "w_low": "-",
                    "m_high": "-",
                    "m_low": "-",
                    "m3_high": "-",
                    "m3_low": "-",
                    "m6_high": "-",
                    "m6_low": "-",
                    "m9_high": "-",
                    "m9_low": "-",
                    "m12_high": "-",
                    "m12_low": "-",
                    "chart_symbol": f"{s['market']}:{s['symbol']}",
                })
                continue

            hist = hist.copy()
            hist = hist[["Open", "High", "Low", "Close"]].dropna(how="all")
            hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
            hist["High"] = pd.to_numeric(hist["High"], errors="coerce")
            hist["Low"] = pd.to_numeric(hist["Low"], errors="coerce")
            hist = hist.dropna(subset=["Close", "High", "Low"], how="any")

            if hist.empty:
                scored.append({
                    **s,
                    "price": "-",
                    "signal": "HOLD",
                    "confidence": 0,
                    "d_high": "-",
                    "d_low": "-",
                    "w_high": "-",
                    "w_low": "-",
                    "m_high": "-",
                    "m_low": "-",
                    "m3_high": "-",
                    "m3_low": "-",
                    "m6_high": "-",
                    "m6_low": "-",
                    "m9_high": "-",
                    "m9_low": "-",
                    "m12_high": "-",
                    "m12_low": "-",
                    "chart_symbol": f"{s['market']}:{s['symbol']}",
                })
                continue

            price_raw = hist["Close"].iloc[-1]
            ma50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
            ma200 = hist["Close"].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None

            signal, confidence = get_signal(price_raw, ma50, ma200)

            d_high = clean_num(hist["High"].iloc[-1])
            d_low = clean_num(hist["Low"].iloc[-1])

            w_high, w_low = range_high_low(hist, 5)
            m_high, m_low = range_high_low(hist, 22)
            m3_high, m3_low = range_high_low(hist, 66)
            m6_high, m6_low = range_high_low(hist, 132)
            m9_high, m9_low = range_high_low(hist, 198)
            m12_high = clean_num(hist["High"].max())
            m12_low = clean_num(hist["Low"].min())

            scored.append({
                **s,
                "price": clean_num(price_raw),
                "signal": signal,
                "confidence": confidence,
                "d_high": d_high,
                "d_low": d_low,
                "w_high": w_high,
                "w_low": w_low,
                "m_high": m_high,
                "m_low": m_low,
                "m3_high": m3_high,
                "m3_low": m3_low,
                "m6_high": m6_high,
                "m6_low": m6_low,
                "m9_high": m9_high,
                "m9_low": m9_low,
                "m12_high": m12_high,
                "m12_low": m12_low,
                "chart_symbol": f"{s['market']}:{s['symbol']}",
            })
        except Exception:
            scored.append({
                **s,
                "price": "-",
                "signal": "HOLD",
                "confidence": 0,
                "d_high": "-",
                "d_low": "-",
                "w_high": "-",
                "w_low": "-",
                "m_high": "-",
                "m_low": "-",
                "m3_high": "-",
                "m3_low": "-",
                "m6_high": "-",
                "m6_low": "-",
                "m9_high": "-",
                "m9_low": "-",
                "m12_high": "-",
                "m12_low": "-",
                "chart_symbol": f"{s['market']}:{s['symbol']}",
            })

    scored = sorted(scored, key=lambda x: x["confidence"], reverse=True)

    best = next((s for s in scored if s["symbol"] == selected_symbol), scored[0])

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(debug=True)

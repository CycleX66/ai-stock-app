from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime
import math

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

def safe(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return round(value, 2)

def get_signal(price, ma50, ma200):
    if ma200 is None or ma50 is None:
        return "HOLD", 40

    if price > ma50 and ma50 > ma200:
        return "BUY", 85
    elif price < ma50 and ma50 < ma200:
        return "SELL", 85
    else:
        return "HOLD", 55


@app.route("/")
def index():
    selected_symbol = request.args.get("symbol", stocks[0]["symbol"])
    scored = []

    for s in stocks:
        ticker = yf.Ticker(s["symbol"])
        hist = ticker.history(period="1y")

        if hist.empty or len(hist) < 50:
            continue

        price_raw = hist["Close"].iloc[-1]
        price = safe(price_raw)

        ma50 = hist["Close"].rolling(50).mean().iloc[-1]
        ma200 = hist["Close"].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None

        signal, confidence = get_signal(price_raw, ma50, ma200)

        d_high = safe(hist["High"].iloc[-1])
        d_low = safe(hist["Low"].iloc[-1])

        w = hist.tail(5)
        w_high = safe(w["High"].max())
        w_low = safe(w["Low"].min())

        m = hist.tail(22)
        m_high = safe(m["High"].max())
        m_low = safe(m["Low"].min())

        m3 = hist.tail(66)
        m3_high = safe(m3["High"].max())
        m3_low = safe(m3["Low"].min())

        m6 = hist.tail(132)
        m6_high = safe(m6["High"].max())
        m6_low = safe(m6["Low"].min())

        m9 = hist.tail(198)
        m9_high = safe(m9["High"].max())
        m9_low = safe(m9["Low"].min())

        m12_high = safe(hist["High"].max())
        m12_low = safe(hist["Low"].min())

        scored.append({
            **s,
            "price": price,
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
            "chart_symbol": f"{s['market']}:{s['symbol']}"
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

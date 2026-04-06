from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime

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

def get_signal(price, ma50, ma200):
    if price > ma50 and ma50 > ma200:
        return "BUY", 80
    elif price < ma50 and ma50 < ma200:
        return "SELL", 80
    else:
        return "HOLD", 50

@app.route("/")
def index():
    selected_symbol = request.args.get("symbol", stocks[0]["symbol"])
    scored = []

    for s in stocks:
        ticker = yf.Ticker(s["symbol"])
        hist = ticker.history(period="1y")

        if hist.empty:
            continue

        price = round(hist["Close"].iloc[-1], 2)

        ma50 = hist["Close"].rolling(50).mean().iloc[-1]
        ma200 = hist["Close"].rolling(200).mean().iloc[-1]

        signal, confidence = get_signal(price, ma50, ma200)

        d_high = round(hist["High"].iloc[-1], 2)
        d_low = round(hist["Low"].iloc[-1], 2)

        w = hist.tail(5)
        w_high = round(w["High"].max(), 2)
        w_low = round(w["Low"].min(), 2)

        m = hist.tail(22)
        m_high = round(m["High"].max(), 2)
        m_low = round(m["Low"].min(), 2)

        m3 = hist.tail(66)
        m3_high = round(m3["High"].max(), 2)
        m3_low = round(m3["Low"].min(), 2)

        m6 = hist.tail(132)
        m6_high = round(m6["High"].max(), 2)
        m6_low = round(m6["Low"].min(), 2)

        m9 = hist.tail(198)
        m9_high = round(m9["High"].max(), 2)
        m9_low = round(m9["Low"].min(), 2)

        m12_high = round(hist["High"].max(), 2)
        m12_low = round(hist["Low"].min(), 2)

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

    # sort best first
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

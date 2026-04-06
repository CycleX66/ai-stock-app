from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {"symbol": "AAPL", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "chart_symbol": "NASDAQ:TSLA"},
]

def safe(value):
    try:
        return round(float(value), 2)
    except:
        return "-"

def get_range(df, days):
    try:
        sub = df.tail(days)
        if sub.empty:
            return "-", "-"
        return safe(sub["High"].max()), safe(sub["Low"].min())
    except:
        return "-", "-"

def get_stock(symbol, chart_symbol):
    try:
        ticker = yf.Ticker(symbol)

        df = ticker.history(period="1y")

        if df.empty:
            return None

        price = safe(df["Close"].iloc[-1])

        d_high = safe(df["High"].iloc[-1])
        d_low = safe(df["Low"].iloc[-1])

        w_high, w_low = get_range(df, 5)
        m_high, m_low = get_range(df, 21)

        m3_high, m3_low = get_range(df, 63)
        m6_high, m6_low = get_range(df, 126)
        m9_high, m9_low = get_range(df, 189)
        m12_high, m12_low = get_range(df, 252)

        return {
            "symbol": symbol,
            "chart_symbol": chart_symbol,
            "price": price,
            "signal": "HOLD",
            "confidence": 50.0,

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
        }

    except Exception as e:
        print("ERROR:", e)
        return None

@app.route("/")
def home():
    scored = []

    for s in STOCKS:
        data = get_stock(s["symbol"], s["chart_symbol"])
        if data:
            scored.append(data)

    if not scored:
        return "No market data available."

    best = scored[0]

    selected = request.args.get("symbol")
    if selected:
        for s in scored:
            if s["symbol"] == selected:
                best = s

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

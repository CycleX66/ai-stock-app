from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "market": "NASDAQ",
        "chart_symbol": "NASDAQ:AAPL",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "market": "NASDAQ",
        "chart_symbol": "NASDAQ:MSFT",
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "market": "NASDAQ",
        "chart_symbol": "NASDAQ:NVDA",
    },
    {
        "symbol": "TSLA",
        "name": "Tesla, Inc.",
        "market": "NASDAQ",
        "chart_symbol": "NASDAQ:TSLA",
    },
]

def safe_float(value):
    try:
        return round(float(value), 2)
    except Exception:
        return "-"

def get_range(df, days):
    sub = df.tail(days)
    if sub.empty:
        return "-", "-"
    return safe_float(sub["High"].max()), safe_float(sub["Low"].min())

def get_signal(df):
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    last = df.iloc[-1]
    ma20 = last["MA20"]
    ma50 = last["MA50"]

    if ma20 > ma50:
        return "BUY", 75
    elif ma20 < ma50:
        return "SELL", 75
    return "HOLD", 50

def get_stock(stock):
    try:
        df = yf.Ticker(stock["symbol"]).history(period="1y")
        if df.empty:
            return None

        df = df.dropna()
        if df.empty:
            return None

        signal, confidence = get_signal(df)

        return {
            "name": stock["name"],
            "symbol": stock["symbol"],
            "market": stock["market"],
            "chart_symbol": stock["chart_symbol"],
            "price": safe_float(df["Close"].iloc[-1]),
            "signal": signal,
            "confidence": confidence,
            "d_high": safe_float(df["High"].iloc[-1]),
            "d_low": safe_float(df["Low"].iloc[-1]),
            "w_high": get_range(df, 5)[0],
            "w_low": get_range(df, 5)[1],
            "m_high": get_range(df, 21)[0],
            "m_low": get_range(df, 21)[1],
            "m3_high": get_range(df, 63)[0],
            "m3_low": get_range(df, 63)[1],
            "m6_high": get_range(df, 126)[0],
            "m6_low": get_range(df, 126)[1],
            "m9_high": get_range(df, 189)[0],
            "m9_low": get_range(df, 189)[1],
            "m12_high": get_range(df, 252)[0],
            "m12_low": get_range(df, 252)[1],
        }
    except Exception:
        return None

@app.route("/")
def home():
    scored = []
    for stock in STOCKS:
        item = get_stock(stock)
        if item:
            scored.append(item)

    if not scored:
        scored = [
            {
                "name": "Apple Inc.",
                "symbol": "AAPL",
                "market": "NASDAQ",
                "chart_symbol": "NASDAQ:AAPL",
                "price": 180.00,
                "signal": "HOLD",
                "confidence": 50,
                "d_high": 182.00,
                "d_low": 178.00,
                "w_high": 183.00,
                "w_low": 177.00,
                "m_high": 185.00,
                "m_low": 175.00,
                "m3_high": 190.00,
                "m3_low": 170.00,
                "m6_high": 195.00,
                "m6_low": 165.00,
                "m9_high": 198.00,
                "m9_low": 160.00,
                "m12_high": 200.00,
                "m12_low": 155.00,
            }
        ]

    best = max(scored, key=lambda x: x["confidence"])

    selected = request.args.get("symbol")
    if selected:
        for item in scored:
            if item["symbol"] == selected:
                best = item
                break

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

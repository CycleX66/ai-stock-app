from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "NASDAQ", "currency": "USD", "chart_symbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ", "currency": "USD", "chart_symbol": "NASDAQ:MSFT"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ", "currency": "USD", "chart_symbol": "NASDAQ:NVDA"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "NASDAQ", "currency": "USD", "chart_symbol": "NASDAQ:TSLA"},

    {"symbol": "AZN.L", "name": "AstraZeneca plc", "market": "LSE", "currency": "GBP", "chart_symbol": "NASDAQ:AZN"},
    {"symbol": "HSBA.L", "name": "HSBC Holdings plc", "market": "LSE", "currency": "GBP", "chart_symbol": "NYSE:HSBC"},
    {"symbol": "BARC.L", "name": "Barclays plc", "market": "LSE", "currency": "GBP", "chart_symbol": "NYSE:BCS"},

    {"symbol": "0700.HK", "name": "Tencent Holdings Ltd.", "market": "HKEX", "currency": "HKD", "chart_symbol": "HKEX:700"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "market": "NSE", "currency": "INR", "chart_symbol": "NSE:RELIANCE"},
]

def safe_float(value):
    try:
        return round(float(value), 2)
    except:
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

    if last["MA20"] > last["MA50"]:
        return "BUY", 75
    elif last["MA20"] < last["MA50"]:
        return "SELL", 75
    return "HOLD", 50

def get_stock(stock):
    try:
        df = yf.Ticker(stock["symbol"]).history(period="1y")

        if df.empty:
            raise Exception("No data")

        df = df.dropna()

        signal, confidence = get_signal(df)

        return {
            "name": stock["name"],
            "symbol": stock["symbol"],
            "market": stock["market"],
            "currency": stock["currency"],
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

    except:
        return {
            "name": stock["name"],
            "symbol": stock["symbol"],
            "market": stock["market"],
            "currency": stock["currency"],
            "chart_symbol": stock["chart_symbol"],
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
        }

@app.route("/")
def home():
    scored = []

    for stock in STOCKS:
        item = get_stock(stock)
        scored.append(item)

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

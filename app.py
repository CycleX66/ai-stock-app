from flask import Flask, render_template
import yfinance as yf
import pandas as pd
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

def clean(value):
    try:
        if value is None or pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return "-"
        return round(float(value), 2)
    except:
        return "-"

def raw(value):
    try:
        return float(value)
    except:
        return None

def currency_symbol(c):
    return {
        "USD": "$",
        "GBP": "£",
        "HKD": "HK$",
        "INR": "₹",
    }.get(c, "")

def money(v, c):
    if v == "-" or v is None:
        return "-"
    return f"{currency_symbol(c)}{float(v):,.2f}"

def get_signal(price, ma50, ma200):
    if price is None:
        return "HOLD", 0, "Flat"

    if ma50 is None:
        return "HOLD", 40, "Flat"

    if ma200 is None:
        if price > ma50:
            return "BUY", 65, "Up"
        if price < ma50:
            return "SELL", 65, "Down"
        return "HOLD", 50, "Flat"

    if price > ma50 and ma50 > ma200:
        return "BUY", 85, "Up"
    if price < ma50 and ma50 < ma200:
        return "SELL", 85, "Down"

    return "HOLD", 55, "Flat"

def score(signal, confidence, price, high, low):
    if price is None or high is None or low is None:
        return confidence

    try:
        rng = high - low
        if rng <= 0:
            return confidence

        pos = (price - low) / rng

        if signal == "BUY":
            return round(confidence + (1 - pos) * 15, 1)

        if signal == "SELL":
            return round(confidence + pos * 15, 1)

        return round(confidence - abs(pos - 0.5) * 10, 1)

    except:
        return confidence

@app.route("/")
def index():

    results = []

    for s in stocks:
        try:
            t = yf.Ticker(s["symbol"])
            hist = t.history(period="1y")

            if hist.empty:
                continue

            hist = hist.dropna()

            price = raw(hist["Close"].iloc[-1])

            ma50 = hist["Close"].rolling(50).mean().iloc[-1]
            ma200 = hist["Close"].rolling(200).mean().iloc[-1]

            sig, conf, trend = get_signal(price, raw(ma50), raw(ma200))

            d_high = clean(hist["High"].iloc[-1])
            d_low = clean(hist["Low"].iloc[-1])

            w_high = clean(hist["High"].tail(5).max())
            w_low = clean(hist["Low"].tail(5).min())

            m_high = clean(hist["High"].tail(22).max())
            m_low = clean(hist["Low"].tail(22).min())

            sc = score(sig, conf, price, raw(m_high), raw(m_low))

            results.append({
                **s,
                "price": money(clean(price), s["currency"]),
                "signal": sig,
                "confidence": conf,
                "score": sc,
                "trend": trend,

                "day": f"{money(d_high,s['currency'])} / {money(d_low,s['currency'])}",
                "week": f"{money(w_high,s['currency'])} / {money(w_low,s['currency'])}",
                "month": f"{money(m_high,s['currency'])} / {money(m_low,s['currency'])}",
            })

        except:
            pass

    # 🔥 SORT (BUY FIRST, THEN SCORE)
    order = {"BUY": 3, "HOLD": 2, "SELL": 1}

    results = sorted(
        results,
        key=lambda x: (order[x["signal"]], x["score"]),
        reverse=True
    )

    # 🔥 BEST TRADE (BUY PRIORITY)
    buys = [r for r in results if r["signal"] == "BUY"]

    if buys:
        best = sorted(buys, key=lambda x: x["score"], reverse=True)[0]
    else:
        best = results[0]

    return render_template("index.html", scored=results, best=best)

if __name__ == "__main__":
    app.run(debug=True)

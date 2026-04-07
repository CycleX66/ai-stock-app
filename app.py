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

def raw_num(value):
    try:
        if value is None or pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return None
        return float(value)
    except Exception:
        return None

def currency_symbol(currency):
    symbols = {
        "USD": "$",
        "GBP": "£",
        "HKD": "HK$",
        "INR": "₹",
    }
    return symbols.get(currency, "")

def format_money(value, currency):
    if value == "-" or value is None:
        return "-"
    symbol = currency_symbol(currency)
    return f"{symbol}{float(value):,.2f}"

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

def range_high_low(hist, days):
    sub = hist.tail(days)
    if sub.empty:
        return "-", "-"
    high_val = clean_num(sub["High"].max())
    low_val = clean_num(sub["Low"].min())
    return high_val, low_val

def get_best_price(ticker, hist):
    if not hist.empty and "Close" in hist.columns:
        close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if not close_series.empty:
            return float(close_series.iloc[-1])

    try:
        fi = ticker.fast_info
        last_price = raw_num(fi.get("lastPrice"))
        if last_price is not None:
            return last_price
    except Exception:
        pass

    try:
        fi = ticker.fast_info
        prev_close = raw_num(fi.get("previousClose"))
        if prev_close is not None:
            return prev_close
    except Exception:
        pass

    try:
        info = ticker.info
        current_price = raw_num(info.get("currentPrice"))
        if current_price is not None:
            return current_price
    except Exception:
        pass

    try:
        info = ticker.info
        regular_price = raw_num(info.get("regularMarketPrice"))
        if regular_price is not None:
            return regular_price
    except Exception:
        pass

    return None

def opportunity_score(signal, confidence, price, month_high, month_low):
    if price is None or month_high is None or month_low is None:
        return confidence

    try:
        rng = month_high - month_low
        if rng <= 0:
            return confidence

        position = (price - month_low) / rng

        if signal == "BUY":
            bonus = (1 - position) * 15
            return round(confidence + bonus, 1)

        if signal == "SELL":
            bonus = position * 15
            return round(confidence + bonus, 1)

        distance_from_middle = abs(position - 0.5)
        return round(confidence - distance_from_middle * 10, 1)

    except Exception:
        return confidence

def signal_rank(item):
    signal_order = {
        "BUY": 3,
        "HOLD": 2,
        "SELL": 1,
    }
    return (
        signal_order.get(item["signal"], 0),
        item["score"],
        item["confidence"]
    )

@app.route("/")
def index():
    selected_symbol = request.args.get("symbol")
    scored = []

    for s in stocks:
        try:
            ticker = yf.Ticker(s["symbol"])
            hist = ticker.history(period="1y", auto_adjust=False)

            if hist.empty:
                scored.append({
                    **s,
                    "price": "-",
                    "price_display": "-",
                    "signal": "HOLD",
                    "confidence": 0,
                    "score": 0,
                    "trend": "Flat",
                    "d_high": "-",
                    "d_low": "-",
                    "d_high_display": "-",
                    "d_low_display": "-",
                    "w_high": "-",
                    "w_low": "-",
                    "w_high_display": "-",
                    "w_low_display": "-",
                    "m_high": "-",
                    "m_low": "-",
                    "m_high_display": "-",
                    "m_low_display": "-",
                    "m3_high": "-",
                    "m3_low": "-",
                    "m3_high_display": "-",
                    "m3_low_display": "-",
                    "m6_high": "-",
                    "m6_low": "-",
                    "m6_high_display": "-",
                    "m6_low_display": "-",
                    "m9_high": "-",
                    "m9_low": "-",
                    "m9_high_display": "-",
                    "m9_low_display": "-",
                    "m12_high": "-",
                    "m12_low": "-",
                    "m12_high_display": "-",
                    "m12_low_display": "-",
                    "chart_symbol": f"{s['market']}:{s['symbol']}",
                })
                continue

            hist = hist.copy()
            hist = hist[["Open", "High", "Low", "Close"]].dropna(how="all")
            hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
            hist["High"] = pd.to_numeric(hist["High"], errors="coerce")
            hist["Low"] = pd.to_numeric(hist["Low"], errors="coerce")
            hist = hist.dropna(subset=["High", "Low"], how="any")

            price_raw = get_best_price(ticker, hist)

            close_for_ma = pd.to_numeric(hist["Close"], errors="coerce").dropna()
            ma50 = close_for_ma.rolling(50).mean().iloc[-1] if len(close_for_ma) >= 50 else None
            ma200 = close_for_ma.rolling(200).mean().iloc[-1] if len(close_for_ma) >= 200 else None

            signal, confidence, trend = get_signal(price_raw, raw_num(ma50), raw_num(ma200))

            d_high = clean_num(hist["High"].iloc[-1]) if not hist.empty else "-"
            d_low = clean_num(hist["Low"].iloc[-1]) if not hist.empty else "-"

            w_high, w_low = range_high_low(hist, 5)
            m_high, m_low = range_high_low(hist, 22)
            m3_high, m3_low = range_high_low(hist, 66)
            m6_high, m6_low = range_high_low(hist, 132)
            m9_high, m9_low = range_high_low(hist, 198)
            m12_high = clean_num(hist["High"].max()) if not hist.empty else "-"
            m12_low = clean_num(hist["Low"].min()) if not hist.empty else "-"

            score = opportunity_score(
                signal=signal,
                confidence=confidence,
                price=raw_num(price_raw),
                month_high=raw_num(m_high),
                month_low=raw_num(m_low),
            )

            scored.append({
                **s,
                "price": clean_num(price_raw),
                "price_display": format_money(clean_num(price_raw), s["currency"]),
                "signal": signal,
                "confidence": confidence,
                "score": score,
                "trend": trend,

                "d_high": d_high,
                "d_low": d_low,
                "d_high_display": format_money(d_high, s["currency"]),
                "d_low_display": format_money(d_low, s["currency"]),

                "w_high": w_high,
                "w_low": w_low,
                "w_high_display": format_money(w_high, s["currency"]),
                "w_low_display": format_money(w_low, s["currency"]),

                "m_high": m_high,
                "m_low": m_low,
                "m_high_display": format_money(m_high, s["currency"]),
                "m_low_display": format_money(m_low, s["currency"]),

                "m3_high": m3_high,
                "m3_low": m3_low,
                "m3_high_display": format_money(m3_high, s["currency"]),
                "m3_low_display": format_money(m3_low, s["currency"]),

                "m6_high": m6_high,
                "m6_low": m6_low,
                "m6_high_display": format_money(m6_high, s["currency"]),
                "m6_low_display": format_money(m6_low, s["currency"]),

                "m9_high": m9_high,
                "m9_low": m9_low,
                "m9_high_display": format_money(m9_high, s["currency"]),
                "m9_low_display": format_money(m9_low, s["currency"]),

                "m12_high": m12_high,
                "m12_low": m12_low,
                "m12_high_display": format_money(m12_high, s["currency"]),
                "m12_low_display": format_money(m12_low, s["currency"]),

                "chart_symbol": f"{s['market']}:{s['symbol']}",
            })
        except Exception:
            scored.append({
                **s,
                "price": "-",
                "price_display": "-",
                "signal": "HOLD",
                "confidence": 0,
                "score": 0,
                "trend": "Flat",
                "d_high": "-",
                "d_low": "-",
                "d_high_display": "-",
                "d_low_display": "-",
                "w_high": "-",
                "w_low": "-",
                "w_high_display": "-",
                "w_low_display": "-",
                "m_high": "-",
                "m_low": "-",
                "m_high_display": "-",
                "m_low_display": "-",
                "m3_high": "-",
                "m3_low": "-",
                "m3_high_display": "-",
                "m3_low_display": "-",
                "m6_high": "-",
                "m6_low": "-",
                "m6_high_display": "-",
                "m6_low_display": "-",
                "m9_high": "-",
                "m9_low": "-",
                "m9_high_display": "-",
                "m9_low_display": "-",
                "m12_high": "-",
                "m12_low": "-",
                "m12_high_display": "-",
                "m12_low_display": "-",
                "chart_symbol": f"{s['market']}:{s['symbol']}",
            })

    scored = sorted(scored, key=signal_rank, reverse=True)

    if selected_symbol:
        best = next((s for s in scored if s["symbol"] == selected_symbol), scored[0])
    else:
        best = scored[0]

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        now=datetime.now()
    )

if __name__ == "__main__":
    app.run(debug=True)

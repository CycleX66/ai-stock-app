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
    except Exception:
        return "-"

def raw(value):
    try:
        if value is None or pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            return None
        return float(value)
    except Exception:
        return None

def currency_symbol(currency):
    return {
        "USD": "$",
        "GBP": "£",
        "HKD": "HK$",
        "INR": "₹",
    }.get(currency, "")

def money(v, c):
    if v == "-" or v is None:
        return "-"
    return f"{currency_symbol(c)}{float(v):,.2f}"

def get_best_price(ticker, hist):
    try:
        close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if not close_series.empty:
            return float(close_series.iloc[-1])
    except Exception:
        pass

    try:
        fi = ticker.fast_info
        last_price = raw(fi.get("lastPrice"))
        if last_price is not None:
            return last_price
    except Exception:
        pass

    try:
        fi = ticker.fast_info
        prev_close = raw(fi.get("previousClose"))
        if prev_close is not None:
            return prev_close
    except Exception:
        pass

    try:
        info = ticker.info
        current_price = raw(info.get("currentPrice"))
        if current_price is not None:
            return current_price
    except Exception:
        pass

    try:
        info = ticker.info
        regular_price = raw(info.get("regularMarketPrice"))
        if regular_price is not None:
            return regular_price
    except Exception:
        pass

    return None

def compute_rsi(close_series, period=14):
    delta = close_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def rsi_status(rsi):
    if rsi is None:
        return "Unknown"
    if rsi <= 30:
        return "Oversold"
    if rsi >= 70:
        return "Overbought"
    return "Neutral"

def get_signal(price, ma50, ma200, rsi):
    if price is None:
        return "HOLD", 0, "Flat"

    if ma50 is None:
        return "HOLD", 40, "Flat"

    trend = "Flat"

    if ma200 is None:
        if price > ma50:
            trend = "Up"
        elif price < ma50:
            trend = "Down"
    else:
        if price > ma50 and ma50 > ma200:
            trend = "Up"
        elif price < ma50 and ma50 < ma200:
            trend = "Down"

    if rsi is None:
        if trend == "Up":
            return "BUY", 70, trend
        if trend == "Down":
            return "SELL", 70, trend
        return "HOLD", 50, trend

    if trend == "Up" and rsi < 70:
        confidence = 75
        if rsi <= 35:
            confidence = 90
        elif rsi <= 45:
            confidence = 82
        return "BUY", confidence, trend

    if trend == "Down" and rsi > 30:
        confidence = 75
        if rsi >= 65:
            confidence = 90
        elif rsi >= 55:
            confidence = 82
        return "SELL", confidence, trend

    if rsi <= 30:
        return "BUY", 80, "Rebound"

    if rsi >= 70:
        return "SELL", 80, "Stretched"

    return "HOLD", 55, trend

def score(signal, confidence, price, high, low, rsi):
    base = confidence

    try:
        if price is not None and high is not None and low is not None:
            rng = high - low
            if rng > 0:
                pos = (price - low) / rng

                if signal == "BUY":
                    base += (1 - pos) * 10
                elif signal == "SELL":
                    base += pos * 10
                else:
                    base -= abs(pos - 0.5) * 6
    except Exception:
        pass

    try:
        if rsi is not None:
            if signal == "BUY" and rsi <= 35:
                base += 8
            elif signal == "SELL" and rsi >= 65:
                base += 8
            elif signal == "HOLD" and 45 <= rsi <= 55:
                base += 3
    except Exception:
        pass

    return round(base, 1)

def get_reason(signal, trend, rsi_value, rsi_flag, price, month_high, month_low):
    reasons = []

    if trend == "Up":
        reasons.append("uptrend")
    elif trend == "Down":
        reasons.append("downtrend")
    elif trend == "Rebound":
        reasons.append("rebound setup")
    elif trend == "Stretched":
        reasons.append("stretched move")

    if rsi_flag == "Oversold":
        reasons.append("oversold RSI")
    elif rsi_flag == "Overbought":
        reasons.append("overbought RSI")
    elif rsi_flag == "Neutral" and rsi_value is not None:
        reasons.append("neutral RSI")

    try:
        if price is not None and month_high is not None and month_low is not None and month_high > month_low:
            pos = (price - month_low) / (month_high - month_low)
            if pos <= 0.25:
                reasons.append("near monthly low")
            elif pos >= 0.75:
                reasons.append("near monthly high")
            else:
                reasons.append("mid monthly range")
    except Exception:
        pass

    if signal == "BUY" and "oversold RSI" in reasons:
        return "Rebound from oversold conditions"
    if signal == "SELL" and "overbought RSI" in reasons:
        return "Overbought with downside risk"

    return ", ".join(reasons[:2]) if reasons else "Mixed signals"

def confidence_label(value):
    if value >= 85:
        return "High"
    if value >= 65:
        return "Medium"
    return "Low"

@app.route("/")
def index():
    results = []

    for s in stocks:
        try:
            t = yf.Ticker(s["symbol"])
            hist = t.history(period="1y", auto_adjust=False)

            if hist.empty:
                continue

            hist = hist.copy()
            hist = hist[["Open", "High", "Low", "Close"]].dropna(how="all")
            hist["Close"] = pd.to_numeric(hist["Close"], errors="coerce")
            hist["High"] = pd.to_numeric(hist["High"], errors="coerce")
            hist["Low"] = pd.to_numeric(hist["Low"], errors="coerce")
            hist = hist.dropna(subset=["High", "Low"], how="any")

            if hist.empty:
                continue

            price = get_best_price(t, hist)

            close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()

            ma50 = close_series.rolling(50).mean().iloc[-1] if len(close_series) >= 50 else None
            ma200 = close_series.rolling(200).mean().iloc[-1] if len(close_series) >= 200 else None

            rsi_series = compute_rsi(close_series)
            rsi_value = raw(rsi_series.iloc[-1]) if not rsi_series.empty else None
            rsi_text = clean(rsi_value)
            rsi_flag = rsi_status(rsi_value)

            sig, conf, trend = get_signal(price, raw(ma50), raw(ma200), rsi_value)

            d_high = clean(hist["High"].iloc[-1])
            d_low = clean(hist["Low"].iloc[-1])

            w_high = clean(hist["High"].tail(5).max())
            w_low = clean(hist["Low"].tail(5).min())

            m_high = clean(hist["High"].tail(22).max())
            m_low = clean(hist["Low"].tail(22).min())

            m3_high = clean(hist["High"].tail(66).max())
            m3_low = clean(hist["Low"].tail(66).min())

            m6_high = clean(hist["High"].tail(132).max())
            m6_low = clean(hist["Low"].tail(132).min())

            m9_high = clean(hist["High"].tail(198).max())
            m9_low = clean(hist["Low"].tail(198).min())

            m12_high = clean(hist["High"].max())
            m12_low = clean(hist["Low"].min())

            sc = score(sig, conf, price, raw(m_high), raw(m_low), rsi_value)
            conf_label = confidence_label(conf)
            reason = get_reason(sig, trend, rsi_value, rsi_flag, price, raw(m_high), raw(m_low))

            results.append({
                **s,
                "price": clean(price),
                "price_display": money(clean(price), s["currency"]),
                "signal": sig,
                "confidence": conf,
                "confidence_label": conf_label,
                "score": sc,
                "trend": trend,
                "rsi": rsi_text,
                "rsi_flag": rsi_flag,
                "reason": reason,

                "d_high_display": money(d_high, s["currency"]),
                "d_low_display": money(d_low, s["currency"]),
                "w_high_display": money(w_high, s["currency"]),
                "w_low_display": money(w_low, s["currency"]),
                "m_high_display": money(m_high, s["currency"]),
                "m_low_display": money(m_low, s["currency"]),
                "m3_high_display": money(m3_high, s["currency"]),
                "m3_low_display": money(m3_low, s["currency"]),
                "m6_high_display": money(m6_high, s["currency"]),
                "m6_low_display": money(m6_low, s["currency"]),
                "m9_high_display": money(m9_high, s["currency"]),
                "m9_low_display": money(m9_low, s["currency"]),
                "m12_high_display": money(m12_high, s["currency"]),
                "m12_low_display": money(m12_low, s["currency"]),
            })

        except Exception:
            continue

    signal_order = {"BUY": 3, "HOLD": 2, "SELL": 1}

    results = sorted(
        results,
        key=lambda x: (signal_order.get(x["signal"], 0), x["score"]),
        reverse=True
    )

    buy_stocks = [r for r in results if r["signal"] == "BUY"]

    if buy_stocks:
        best = sorted(buy_stocks, key=lambda x: x["score"], reverse=True)[0]
    else:
        best = results[0]

    return render_template("index.html", scored=results, best=best)

if __name__ == "__main__":
    app.run(debug=True)

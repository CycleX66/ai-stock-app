from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import math
import pandas as pd
import yfinance as yf

app = Flask(__name__, template_folder="templates")
app.secret_key = "cyc1ex-super-secret-key-change-this"

# =========================================================
# CycleX AI - starter universe
# =========================================================

UNIVERSE = [
    # US - Nasdaq
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "META", "name": "Meta Platforms, Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},

    # US - Dow
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "V", "name": "Visa Inc.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "MCD", "name": "McDonald's Corporation", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},

    # UK - FTSE 100
    {"symbol": "AZN.L", "name": "AstraZeneca plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "HSBA.L", "name": "HSBC Holdings plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "BARC.L", "name": "Barclays plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "SHEL.L", "name": "Shell plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "ULVR.L", "name": "Unilever PLC", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},

    # UK - FTSE 250
    {"symbol": "BAB.L", "name": "Babcock International Group PLC", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "GFRD.L", "name": "Galliford Try Holdings plc", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "ITRK.L", "name": "Intertek Group plc", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},

    # UK - FTSE All-Share
    {"symbol": "LGEN.L", "name": "Legal & General Group Plc", "market": "UK", "index": "FTSE All-Share", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "MNG.L", "name": "M&G plc", "market": "UK", "index": "FTSE All-Share", "exchange": "LSE", "currency": "GBP"},

    # Hong Kong - Hang Seng
    {"symbol": "0700.HK", "name": "Tencent Holdings Ltd.", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},
    {"symbol": "1299.HK", "name": "AIA Group Limited", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},
    {"symbol": "9988.HK", "name": "Alibaba Group Holding Limited", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},

    # India
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "market": "India", "index": "India Large Cap", "exchange": "NSE", "currency": "INR"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd.", "market": "India", "index": "India Large Cap", "exchange": "NSE", "currency": "INR"},
    {"symbol": "INFY.NS", "name": "Infosys Limited", "market": "India", "index": "India Large Cap", "exchange": "NSE", "currency": "INR"},
]

MARKET_OPTIONS = ["All Markets", "US", "UK", "Hong Kong", "India"]
INDEX_OPTIONS = [
    "All Indices",
    "Nasdaq",
    "Dow Jones",
    "FTSE 100",
    "FTSE 250",
    "FTSE All-Share",
    "Hang Seng",
    "India Large Cap",
]
RISK_OPTIONS = ["Defensive", "Cautious", "Balanced", "Growth", "Aggressive"]

DISCLAIMERS = [
    "CycleX AI provides market intelligence and analytics only. It does not provide personal financial advice.",
    "Investments can go down as well as up. You may get back less than you invest.",
    "Past performance is not a reliable indicator of future results.",
]

# =========================================================
# Helpers
# =========================================================

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

def money(value, currency):
    if value == "-" or value is None:
        return "-"
    return f"{currency_symbol(currency)}{float(value):,.2f}"

def get_best_price(ticker, hist):
    try:
        close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if not close_series.empty:
            return float(close_series.iloc[-1])
    except Exception:
        pass

    try:
        fi = ticker.fast_info
        for key in ("lastPrice", "previousClose"):
            v = raw(fi.get(key))
            if v is not None:
                return v
    except Exception:
        pass

    try:
        info = ticker.info
        for key in ("currentPrice", "regularMarketPrice"):
            v = raw(info.get(key))
            if v is not None:
                return v
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

def confidence_label(value):
    if value >= 85:
        return "High"
    if value >= 65:
        return "Medium"
    return "Low"

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

def stock_risk_band(volatility_pct, confidence):
    score_value = 0

    if volatility_pct is None:
        score_value += 2
    elif volatility_pct < 20:
        score_value += 1
    elif volatility_pct < 35:
        score_value += 2
    else:
        score_value += 3

    if confidence >= 85:
        score_value -= 1
    elif confidence < 60:
        score_value += 1

    if score_value <= 1:
        return "Low"
    if score_value <= 3:
        return "Medium"
    return "High"

def allowed_risk_bands(user_risk):
    mapping = {
        "Defensive": {"Low"},
        "Cautious": {"Low", "Medium"},
        "Balanced": {"Low", "Medium"},
        "Growth": {"Low", "Medium", "High"},
        "Aggressive": {"Low", "Medium", "High"},
    }
    return mapping.get(user_risk, {"Low", "Medium"})

def filter_universe(market_choice, index_choice):
    filtered = UNIVERSE

    if market_choice != "All Markets":
        filtered = [x for x in filtered if x["market"] == market_choice]

    if index_choice != "All Indices":
        filtered = [x for x in filtered if x["index"] == index_choice]

    return filtered

def scan_universe(selected_market, selected_index, selected_risk):
    filtered = filter_universe(selected_market, selected_index)
    results = []

    for s in filtered:
        try:
            ticker = yf.Ticker(s["symbol"])
            hist = ticker.history(period="1y", auto_adjust=False)

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

            price = get_best_price(ticker, hist)
            close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()

            if close_series.empty:
                continue

            ma50 = close_series.rolling(50).mean().iloc[-1] if len(close_series) >= 50 else None
            ma200 = close_series.rolling(200).mean().iloc[-1] if len(close_series) >= 200 else None

            rsi_series = compute_rsi(close_series)
            rsi_value = raw(rsi_series.iloc[-1]) if not rsi_series.empty else None
            rsi_text = clean(rsi_value)
            rsi_flag = rsi_status(rsi_value)

            signal, confidence, trend = get_signal(price, raw(ma50), raw(ma200), rsi_value)

            d_high = clean(hist["High"].iloc[-1])
            d_low = clean(hist["Low"].iloc[-1])
            w_high = clean(hist["High"].tail(5).max())
            w_low = clean(hist["Low"].tail(5).min())
            m_high = clean(hist["High"].tail(22).max())
            m_low = clean(hist["Low"].tail(22).min())

            annualised_vol = None
            try:
                returns = close_series.pct_change().dropna()
                if not returns.empty:
                    annualised_vol = float(returns.std() * (252 ** 0.5) * 100)
            except Exception:
                pass

            scanner_score = score(signal, confidence, price, raw(m_high), raw(m_low), rsi_value)
            risk_band = stock_risk_band(annualised_vol, confidence)
            reason = get_reason(signal, trend, rsi_value, rsi_flag, price, raw(m_high), raw(m_low))

            results.append({
                "name": s["name"],
                "symbol": s["symbol"],
                "market": s["market"],
                "index": s["index"],
                "exchange": s["exchange"],
                "currency": s["currency"],
                "signal": signal,
                "score": scanner_score,
                "confidence": confidence,
                "confidence_label": confidence_label(confidence),
                "trend": trend,
                "rsi": rsi_text,
                "rsi_flag": rsi_flag,
                "reason": reason,
                "risk_band": risk_band,
                "volatility_pct": clean(annualised_vol),
                "price_display": money(clean(price), s["currency"]),
                "price_raw": raw(price),
                "d_high_display": money(d_high, s["currency"]),
                "d_low_display": money(d_low, s["currency"]),
                "w_high_display": money(w_high, s["currency"]),
                "w_low_display": money(w_low, s["currency"]),
                "m_high_display": money(m_high, s["currency"]),
                "m_low_display": money(m_low, s["currency"]),
            })

        except Exception:
            continue

    allowed = allowed_risk_bands(selected_risk)
    results = [x for x in results if x["risk_band"] in allowed]

    signal_order = {"BUY": 3, "HOLD": 2, "SELL": 1}
    results = sorted(results, key=lambda x: (signal_order.get(x["signal"], 0), x["score"]), reverse=True)

    return results

# =========================================================
# Portfolio helpers
# =========================================================

def get_portfolios():
    return session.get("portfolios", {})

def save_portfolios(portfolios):
    session["portfolios"] = portfolios
    session.modified = True

def get_portfolio_for_risk(risk):
    portfolios = get_portfolios()
    return portfolios.get(risk, [])

def fetch_current_price(symbol):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d", auto_adjust=False)
        if not hist.empty:
            close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()
            if not close_series.empty:
                return float(close_series.iloc[-1])
    except Exception:
        pass
    return None

def build_portfolio_analytics(holdings):
    if not holdings:
        return {
            "summary": [],
            "portfolio_labels": [],
            "portfolio_values": [],
            "portfolio_return_pct": 0,
            "individual_charts": []
        }

    frames = []
    individual_charts = []
    summary = []

    for holding in holdings:
        symbol = holding["symbol"]
        name = holding["name"]
        currency = holding["currency"]
        purchase_date = holding["purchase_date"]
        purchase_price = raw(holding["purchase_price"])

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=purchase_date, auto_adjust=False)
            if hist.empty:
                continue

            close_series = pd.to_numeric(hist["Close"], errors="coerce").dropna()
            if close_series.empty:
                continue

            if purchase_price is None:
                purchase_price = float(close_series.iloc[0])

            current_price = float(close_series.iloc[-1])
            current_return_pct = round(((current_price - purchase_price) / purchase_price) * 100, 2)

            df = close_series.to_frame(name=symbol)
            frames.append(df)

            labels = [d.strftime("%Y-%m-%d") for d in df.index]
            values = [round(float(v), 2) for v in df[symbol].tolist()]

            individual_charts.append({
                "symbol": symbol,
                "name": name,
                "labels": labels,
                "values": values,
                "purchase_date": purchase_date,
                "purchase_price_display": money(purchase_price, currency),
                "current_price_display": money(current_price, currency),
                "return_pct": current_return_pct,
                "currency": currency
            })

            summary.append({
                "symbol": symbol,
                "name": name,
                "purchase_date": purchase_date,
                "purchase_price_display": money(purchase_price, currency),
                "current_price_display": money(current_price, currency),
                "return_pct": current_return_pct,
                "currency": currency
            })

        except Exception:
            continue

    if not frames:
        return {
            "summary": [],
            "portfolio_labels": [],
            "portfolio_values": [],
            "portfolio_return_pct": 0,
            "individual_charts": []
        }

    portfolio_df = pd.concat(frames, axis=1).sort_index().ffill().dropna(how="all")
    portfolio_df["Total"] = portfolio_df.sum(axis=1)

    portfolio_labels = [d.strftime("%Y-%m-%d") for d in portfolio_df.index]
    portfolio_values = [round(float(v), 2) for v in portfolio_df["Total"].tolist()]

    portfolio_return_pct = 0
    if portfolio_values:
        start_value = portfolio_values[0]
        end_value = portfolio_values[-1]
        if start_value:
            portfolio_return_pct = round(((end_value - start_value) / start_value) * 100, 2)

    return {
        "summary": summary,
        "portfolio_labels": portfolio_labels,
        "portfolio_values": portfolio_values,
        "portfolio_return_pct": portfolio_return_pct,
        "individual_charts": individual_charts
    }

# =========================================================
# Routes
# =========================================================

@app.route("/")
def home():
    selected_risk = request.args.get("risk", "Balanced").capitalize()
    if selected_risk not in RISK_OPTIONS:
        selected_risk = "Balanced"

    selected_market = request.args.get("market", "All Markets")
    if selected_market not in MARKET_OPTIONS:
        selected_market = "All Markets"

    selected_index = request.args.get("index", "All Indices")
    if selected_index not in INDEX_OPTIONS:
        selected_index = "All Indices"

    scored = scan_universe(selected_market, selected_index, selected_risk)
    best = scored[0] if scored else None

    portfolio_holdings = get_portfolio_for_risk(selected_risk)
    portfolio_data = build_portfolio_analytics(portfolio_holdings)

    portfolio_symbols = {h["symbol"] for h in portfolio_holdings}

    return render_template(
        "index.html",
        scored=scored,
        best=best,
        risk=selected_risk,
        market_options=MARKET_OPTIONS,
        index_options=INDEX_OPTIONS,
        risk_options=RISK_OPTIONS,
        selected_market=selected_market,
        selected_index=selected_index,
        disclaimers=DISCLAIMERS,
        now=datetime.now().strftime("%H:%M:%S"),
        portfolio_data=portfolio_data,
        portfolio_symbols=portfolio_symbols
    )

@app.route("/onboarding")
def onboarding():
    selected_risk = request.args.get("risk", "Balanced").capitalize()
    if selected_risk not in RISK_OPTIONS:
        selected_risk = "Balanced"

    return render_template(
        "onboarding.html",
        risk=selected_risk,
        risk_options=RISK_OPTIONS,
        market_options=MARKET_OPTIONS,
        index_options=INDEX_OPTIONS
    )

@app.route("/portfolio/add", methods=["POST"])
def add_to_portfolio():
    symbol = request.form.get("symbol")
    risk = request.form.get("risk", "Balanced").capitalize()
    market = request.form.get("market", "All Markets")
    index = request.form.get("index", "All Indices")

    if risk not in RISK_OPTIONS:
        risk = "Balanced"

    meta = next((x for x in UNIVERSE if x["symbol"] == symbol), None)
    if not meta:
        return redirect(url_for("home", risk=risk, market=market, index=index))

    portfolios = get_portfolios()
    holdings = portfolios.get(risk, [])

    if symbol not in [h["symbol"] for h in holdings]:
        purchase_price = fetch_current_price(symbol)
        holdings.append({
            "symbol": symbol,
            "name": meta["name"],
            "currency": meta["currency"],
            "purchase_date": datetime.now().strftime("%Y-%m-%d"),
            "purchase_price": purchase_price
        })
        portfolios[risk] = holdings
        save_portfolios(portfolios)

    return redirect(url_for("home", risk=risk, market=market, index=index))

@app.route("/portfolio/remove", methods=["POST"])
def remove_from_portfolio():
    symbol = request.form.get("symbol")
    risk = request.form.get("risk", "Balanced").capitalize()
    market = request.form.get("market", "All Markets")
    index = request.form.get("index", "All Indices")

    portfolios = get_portfolios()
    holdings = portfolios.get(risk, [])
    holdings = [h for h in holdings if h["symbol"] != symbol]
    portfolios[risk] = holdings
    save_portfolios(portfolios)

    return redirect(url_for("home", risk=risk, market=market, index=index))

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import math
import pandas as pd
import yfinance as yf

app = Flask(__name__)
app.secret_key = "replace-this-with-a-long-random-secret"

# =========================================================
# COMPLIANCE-ORIENTED PLATFORM COPY
# =========================================================

DISCLAIMERS = [
    "This platform provides market intelligence and analytics only. It does not provide personal financial advice.",
    "Investments can go down as well as up. You may get back less than you invest.",
    "Past performance is not a reliable indicator of future results.",
    "You remain responsible for your own investment decisions.",
]

RISK_CATEGORY_TEXT = {
    "Defensive": "Defensive users typically prefer lower volatility and stronger capital preservation.",
    "Cautious": "Cautious users typically prefer lower-risk investments and moderate fluctuations.",
    "Balanced": "Balanced users typically accept moderate volatility for moderate growth potential.",
    "Growth": "Growth users typically accept higher volatility for stronger return potential.",
    "Aggressive": "Aggressive users typically accept high volatility and larger drawdowns for higher upside potential.",
}

# =========================================================
# MARKETS / INDICES / SAMPLE UNIVERSE
# NOTE:
# This starter uses a maintained sample universe you can expand.
# For production, plug in index constituent feeds because indices
# rebalance over time.
# =========================================================

UNIVERSE = [
    # US / Nasdaq
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "market": "US", "index": "Nasdaq", "exchange": "NASDAQ", "currency": "USD"},

    # US / Dow Jones
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "V", "name": "Visa Inc.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "MCD", "name": "McDonald's Corporation", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "market": "US", "index": "Dow Jones", "exchange": "NYSE", "currency": "USD"},

    # UK / FTSE 100
    {"symbol": "AZN.L", "name": "AstraZeneca plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "HSBA.L", "name": "HSBC Holdings plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "BARC.L", "name": "Barclays plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "SHEL.L", "name": "Shell plc", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "ULVR.L", "name": "Unilever PLC", "market": "UK", "index": "FTSE 100", "exchange": "LSE", "currency": "GBP"},

    # UK / FTSE 250
    {"symbol": "BAB.L", "name": "Babcock International Group PLC", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "GFRD.L", "name": "Galliford Try Holdings plc", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "ITRK.L", "name": "Intertek Group plc", "market": "UK", "index": "FTSE 250", "exchange": "LSE", "currency": "GBP"},

    # UK / FTSE All-Share
    {"symbol": "LGEN.L", "name": "Legal & General Group Plc", "market": "UK", "index": "FTSE All-Share", "exchange": "LSE", "currency": "GBP"},
    {"symbol": "MNG.L", "name": "M&G plc", "market": "UK", "index": "FTSE All-Share", "exchange": "LSE", "currency": "GBP"},

    # Hong Kong / Hang Seng
    {"symbol": "0700.HK", "name": "Tencent Holdings Ltd.", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},
    {"symbol": "1299.HK", "name": "AIA Group Limited", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},
    {"symbol": "9988.HK", "name": "Alibaba Group Holding Limited", "market": "Hong Kong", "index": "Hang Seng", "exchange": "HKEX", "currency": "HKD"},

    # India / example universe
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "market": "India", "index": "India Large Cap", "exchange": "NSE", "currency": "INR"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd.", "market": "India", "index": "India Large Cap", "exchange": "NSE", "currency": "INR"},
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

# =========================================================
# UTILITIES
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
    return 100 - (100 / (1 + rs))

def rsi_status(rsi):
    if rsi is None:
        return "Unknown"
    if rsi <= 30:
        return "Oversold"
    if rsi >= 70:
        return "Overbought"
    return "Neutral"

# =========================================================
# USER RISK PROFILING
# =========================================================

def calculate_risk_score(form_data):
    """
    Weighted score 1-10 style, then mapped to category.
    """
    objectives = int(form_data.get("objectives", 3))
    risk_tolerance = int(form_data.get("risk_tolerance", 3))
    capacity_for_loss = int(form_data.get("capacity_for_loss", 3))
    time_horizon = int(form_data.get("time_horizon", 3))
    experience = int(form_data.get("experience", 3))

    weighted = (
        objectives * 0.10 +
        risk_tolerance * 0.30 +
        capacity_for_loss * 0.25 +
        time_horizon * 0.20 +
        experience * 0.15
    )

    return round(weighted * 2, 1)  # roughly 2-10 scale

def risk_category_from_score(score):
    if score <= 2.5:
        return "Defensive"
    if score <= 4.5:
        return "Cautious"
    if score <= 6.5:
        return "Balanced"
    if score <= 8.5:
        return "Growth"
    return "Aggressive"

def capacity_override_required(form_data):
    """
    Simple guardrail for capacity for loss.
    """
    capacity_for_loss = int(form_data.get("capacity_for_loss", 3))
    emergency_buffer = int(form_data.get("emergency_buffer", 3))
    if capacity_for_loss <= 2 or emergency_buffer <= 2:
        return True
    return False

# =========================================================
# STOCK RISK BANDING
# =========================================================

def stock_risk_band(volatility_pct, market_cap_bucket, signal_confidence):
    """
    Low / Medium / High risk banding.
    """
    score = 0

    if volatility_pct is None:
        score += 2
    elif volatility_pct < 20:
        score += 1
    elif volatility_pct < 35:
        score += 2
    else:
        score += 3

    if market_cap_bucket == "Large":
        score += 1
    elif market_cap_bucket == "Mid":
        score += 2
    else:
        score += 3

    if signal_confidence >= 85:
        score -= 1
    elif signal_confidence < 60:
        score += 1

    if score <= 2:
        return "Low"
    if score <= 4:
        return "Medium"
    return "High"

def guess_market_cap_bucket(symbol):
    # Simple starter heuristic. Replace with real fundamentals later.
    if symbol in {"AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "AZN.L", "HSBA.L", "0700.HK", "9988.HK", "RELIANCE.NS", "TCS.NS"}:
        return "Large"
    if symbol in {"BARC.L", "SHEL.L", "ULVR.L", "JPM", "V", "MCD", "CAT", "1299.HK"}:
        return "Large"
    return "Mid"

# =========================================================
# SIGNAL ENGINE (DE-PERSONALISED)
# =========================================================

def get_signal(price, ma50, ma200, rsi):
    if price is None:
        return "HOLD", 0, "Flat"

    if ma50 is None:
        return "HOLD", 40, "Flat"

    trend = "Flat"
    if ma200 is None:
        trend = "Up" if price > ma50 else "Down" if price < ma50 else "Flat"
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

# =========================================================
# FILTERING LAYER (FILTERING, NOT ADVISING)
# =========================================================

def universe_filter(items, market_choice, index_choice):
    filtered = items

    if market_choice and market_choice != "All Markets":
        filtered = [x for x in filtered if x["market"] == market_choice]

    if index_choice and index_choice != "All Indices":
        filtered = [x for x in filtered if x["index"] == index_choice]

    return filtered

def risk_filter(items, user_category, restrict_high_risk=False):
    """
    Compliant framing: this narrows the list shown, but does not say
    a stock is suitable. It is a filtering layer only.
    """
    allowed = {
        "Defensive": {"Low"},
        "Cautious": {"Low"},
        "Balanced": {"Low", "Medium"},
        "Growth": {"Low", "Medium", "High"},
        "Aggressive": {"Low", "Medium", "High"},
    }.get(user_category, {"Low", "Medium"})

    if restrict_high_risk:
        allowed = {"Low", "Medium"} if "High" in allowed else allowed

    return [x for x in items if x["risk_band"] in allowed]

# =========================================================
# MARKET SCAN
# =========================================================

def scan_universe(selected_market, selected_index):
    scoped = universe_filter(UNIVERSE, selected_market, selected_index)
    results = []

    for s in scoped:
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

            opportunity_score = score(signal, confidence, price, raw(m_high), raw(m_low), rsi_value)
            reason = get_reason(signal, trend, rsi_value, rsi_flag, price, raw(m_high), raw(m_low))

            annualised_vol = None
            try:
                returns = close_series.pct_change().dropna()
                if not returns.empty:
                    annualised_vol = float(returns.std() * (252 ** 0.5) * 100)
            except Exception:
                pass

            market_cap_bucket = guess_market_cap_bucket(s["symbol"])
            risk_band = stock_risk_band(annualised_vol, market_cap_bucket, confidence)

            results.append({
                "name": s["name"],
                "symbol": s["symbol"],
                "market": s["market"],
                "index": s["index"],
                "exchange": s["exchange"],
                "currency": s["currency"],

                "signal": signal,
                "score": opportunity_score,
                "confidence": confidence,
                "confidence_label": confidence_label(confidence),
                "trend": trend,
                "rsi": rsi_text,
                "rsi_flag": rsi_flag,
                "reason": reason,
                "risk_band": risk_band,
                "market_cap_bucket": market_cap_bucket,
                "volatility_pct": clean(annualised_vol),

                "price_display": money(clean(price), s["currency"]),
                "d_high_display": money(d_high, s["currency"]),
                "d_low_display": money(d_low, s["currency"]),
                "w_high_display": money(w_high, s["currency"]),
                "w_low_display": money(w_low, s["currency"]),
                "m_high_display": money(m_high, s["currency"]),
                "m_low_display": money(m_low, s["currency"]),
            })
        except Exception:
            continue

    order = {"BUY": 3, "HOLD": 2, "SELL": 1}
    return sorted(results, key=lambda x: (order.get(x["signal"], 0), x["score"]), reverse=True)

# =========================================================
# SESSION HELPERS
# =========================================================

def get_user_profile():
    return session.get("profile", {})

def save_user_profile(profile):
    session["profile"] = profile

def get_portfolio():
    return session.get("portfolio", [])

def save_portfolio(portfolio):
    session["portfolio"] = portfolio

# =========================================================
# ROUTES
# =========================================================

@app.route("/", methods=["GET"])
def home():
    profile = get_user_profile()
    if not profile:
        return redirect(url_for("onboarding"))

    selected_market = request.args.get("market", profile.get("market_scope", "All Markets"))
    selected_index = request.args.get("index", profile.get("index_scope", "All Indices"))
    risk_view = request.args.get("risk_view", "All")

    scanned = scan_universe(selected_market, selected_index)

    restrict_high = profile.get("capacity_override", False)
    filtered_for_user = risk_filter(scanned, profile.get("risk_category", "Balanced"), restrict_high_risk=restrict_high)

    if risk_view in {"Low", "Medium", "High"}:
        filtered_for_user = [x for x in filtered_for_user if x["risk_band"] == risk_view]

    best = filtered_for_user[0] if filtered_for_user else None

    return render_template(
        "index.html",
        scored=filtered_for_user,
        best=best,
        now=datetime.now().strftime("%H:%M:%S"),
        disclaimers=DISCLAIMERS,
        profile=profile,
        market_options=MARKET_OPTIONS,
        index_options=INDEX_OPTIONS,
        selected_market=selected_market,
        selected_index=selected_index,
        risk_view=risk_view,
        portfolio=get_portfolio(),
        compliance_message=(
            f"You are in the {profile.get('risk_category', 'Balanced')} category. "
            f"You may prefer to explore investments labelled "
            f"{'low and medium risk' if profile.get('risk_category') == 'Balanced' else profile.get('risk_category', '').lower()}."
        ),
    )

@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if request.method == "POST":
        score_value = calculate_risk_score(request.form)
        category = risk_category_from_score(score_value)
        override = capacity_override_required(request.form)

        profile = {
            "objectives": int(request.form.get("objectives", 3)),
            "risk_tolerance": int(request.form.get("risk_tolerance", 3)),
            "capacity_for_loss": int(request.form.get("capacity_for_loss", 3)),
            "time_horizon": int(request.form.get("time_horizon", 3)),
            "experience": int(request.form.get("experience", 3)),
            "emergency_buffer": int(request.form.get("emergency_buffer", 3)),
            "risk_score": score_value,
            "risk_category": category,
            "capacity_override": override,
            "market_scope": request.form.get("market_scope", "All Markets"),
            "index_scope": request.form.get("index_scope", "All Indices"),
        }

        save_user_profile(profile)
        if "portfolio" not in session:
            save_portfolio([])

        return redirect(url_for("home"))

    return render_template(
        "onboarding.html",
        disclaimers=DISCLAIMERS,
        market_options=MARKET_OPTIONS,
        index_options=INDEX_OPTIONS,
        risk_category_text=RISK_CATEGORY_TEXT,
    )

@app.route("/portfolio/add", methods=["POST"])
def add_to_portfolio():
    symbol = request.form.get("symbol")
    if not symbol:
        return redirect(url_for("home"))

    portfolio = get_portfolio()
    if symbol not in portfolio:
        portfolio.append(symbol)
        save_portfolio(portfolio)

    return redirect(url_for("home"))

@app.route("/portfolio/remove", methods=["POST"])
def remove_from_portfolio():
    symbol = request.form.get("symbol")
    portfolio = get_portfolio()
    portfolio = [s for s in portfolio if s != symbol]
    save_portfolio(portfolio)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)

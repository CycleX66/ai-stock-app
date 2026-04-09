from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import uuid

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "cyclex-super-secret-key-change-this"

RISK_OPTIONS = ["Defensive", "Cautious", "Balanced", "Growth", "Aggressive"]
MARKET_OPTIONS = ["All Markets", "US", "UK", "Hong Kong"]
SIGNAL_OPTIONS = ["All Signals", "BUY", "HOLD", "SELL"]

STOCKS = [
    {"symbol": "MCD", "name": "McDonald's", "market": "US", "exchange": "NYSE", "currency": "USD", "signal": "BUY", "score": 97.4, "price": 304.85, "risk_band": "Low"},
    {"symbol": "MSFT", "name": "Microsoft", "market": "US", "exchange": "NASDAQ", "currency": "USD", "signal": "BUY", "score": 95.2, "price": 372.29, "risk_band": "Medium"},
    {"symbol": "ULVR.L", "name": "Unilever", "market": "UK", "exchange": "LSE", "currency": "GBP", "signal": "BUY", "score": 95.6, "price": 42.72, "risk_band": "Low"},
    {"symbol": "SHEL.L", "name": "Shell", "market": "UK", "exchange": "LSE", "currency": "GBP", "signal": "HOLD", "score": 86.4, "price": 33.73, "risk_band": "Medium"},
    {"symbol": "BARC.L", "name": "Barclays", "market": "UK", "exchange": "LSE", "currency": "GBP", "signal": "BUY", "score": 79.4, "price": 4.43, "risk_band": "Medium"},
    {"symbol": "0700.HK", "name": "Tencent", "market": "Hong Kong", "exchange": "HKEX", "currency": "HKD", "signal": "BUY", "score": 88.1, "price": 489.20, "risk_band": "Medium"},
    {"symbol": "1299.HK", "name": "AIA Group", "market": "Hong Kong", "exchange": "HKEX", "currency": "HKD", "signal": "BUY", "score": 77.6, "price": 88.65, "risk_band": "Medium"},
    {"symbol": "NVDA", "name": "NVIDIA", "market": "US", "exchange": "NASDAQ", "currency": "USD", "signal": "HOLD", "score": 84.7, "price": 902.15, "risk_band": "High"},
    {"symbol": "AAPL", "name": "Apple", "market": "US", "exchange": "NASDAQ", "currency": "USD", "signal": "BUY", "score": 91.8, "price": 188.54, "risk_band": "Low"},
    {"symbol": "AZN.L", "name": "AstraZeneca", "market": "UK", "exchange": "LSE", "currency": "GBP", "signal": "BUY", "score": 76.2, "price": 104.30, "risk_band": "Low"},
]

DISCLAIMERS = [
    "CycleX AI provides market intelligence and analytics only. It does not provide personal financial advice.",
    "Investments can go down as well as up. You may get back less than you invest.",
    "Past performance is not a reliable indicator of future results.",
]


def currency_symbol(currency):
    return {"USD": "$", "GBP": "£", "HKD": "HK$"}.get(currency, "")


def money(value, currency):
    return f"{currency_symbol(currency)}{value:,.2f}"


def ensure_state():
    if "user_risk" not in session:
        session["user_risk"] = "Balanced"
    if "portfolios" not in session:
        session["portfolios"] = {}
    if "active_portfolio_id" not in session:
        session["active_portfolio_id"] = None


def create_default_portfolio():
    portfolios = session["portfolios"]
    if portfolios:
        return
    pid = str(uuid.uuid4())
    portfolios[pid] = {
        "id": pid,
        "name": "My Balanced Portfolio",
        "risk": session.get("user_risk", "Balanced"),
        "market": "All Markets",
        "currency": "Mixed",
        "holdings": []
    }
    session["portfolios"] = portfolios
    session["active_portfolio_id"] = pid
    session.modified = True


def get_portfolios():
    ensure_state()
    return session["portfolios"]


def get_active_portfolio():
    ensure_state()
    portfolios = session["portfolios"]
    pid = session.get("active_portfolio_id")
    if pid and pid in portfolios:
        return portfolios[pid]
    if portfolios:
        first_id = next(iter(portfolios.keys()))
        session["active_portfolio_id"] = first_id
        session.modified = True
        return portfolios[first_id]
    return None


def get_stock(symbol):
    for stock in STOCKS:
        if stock["symbol"] == symbol:
            return stock
    return None


def filter_stocks(risk, market, signal):
    filtered = STOCKS[:]

    if market != "All Markets":
        filtered = [s for s in filtered if s["market"] == market]

    if signal != "All Signals":
        filtered = [s for s in filtered if s["signal"] == signal]

    risk_mapping = {
        "Defensive": {"Low"},
        "Cautious": {"Low", "Medium"},
        "Balanced": {"Low", "Medium"},
        "Growth": {"Low", "Medium", "High"},
        "Aggressive": {"Low", "Medium", "High"},
    }

    allowed = risk_mapping.get(risk, {"Low", "Medium"})
    filtered = [s for s in filtered if s["risk_band"] in allowed]
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered


def build_portfolio_summary(portfolio):
    holdings = portfolio.get("holdings", [])
    summary = []
    total_value = 0

    for holding in holdings:
        stock = get_stock(holding["symbol"])
        if not stock:
            continue

        units = float(holding["units"])
        current_price = float(stock["price"])
        current_value = units * current_price
        purchase_price = float(holding["purchase_price"])
        cost_value = units * purchase_price
        return_pct = 0
        if purchase_price > 0:
            return_pct = ((current_price - purchase_price) / purchase_price) * 100

        total_value += current_value

        summary.append({
            "name": stock["name"],
            "symbol": stock["symbol"],
            "market": stock["market"],
            "exchange": stock["exchange"],
            "currency": stock["currency"],
            "units": units,
            "purchase_date": holding["purchase_date"],
            "purchase_price_display": money(purchase_price, stock["currency"]),
            "current_price_display": money(current_price, stock["currency"]),
            "current_value_display": money(current_value, stock["currency"]),
            "return_pct": round(return_pct, 2),
        })

    return {
        "holdings": summary,
        "holdings_count": len(summary),
        "total_value": round(total_value, 2),
    }


def build_portfolio_cards():
    cards = []
    portfolios = get_portfolios()
    active = get_active_portfolio()

    for pid, portfolio in portfolios.items():
        summary = build_portfolio_summary(portfolio)
        cards.append({
            "id": pid,
            "name": portfolio["name"],
            "risk": portfolio["risk"],
            "market": portfolio["market"],
            "currency": portfolio["currency"],
            "holdings_count": summary["holdings_count"],
            "total_value": summary["total_value"],
            "is_active": active and active["id"] == pid
        })
    return cards


@app.route("/")
def home():
    ensure_state()
    create_default_portfolio()

    view = request.args.get("view", "dashboard")
    risk = request.args.get("risk", session.get("user_risk", "Balanced"))
    market = request.args.get("market", "All Markets")
    signal = request.args.get("signal", "All Signals")

    active_portfolio = get_active_portfolio()
    filtered_stocks = filter_stocks(risk, market, signal)
    portfolio_summary = build_portfolio_summary(active_portfolio)
    portfolio_cards = build_portfolio_cards()

    best = filtered_stocks[0] if filtered_stocks else None

    portfolio_chart_labels = []
    portfolio_chart_values = []
    for i, holding in enumerate(portfolio_summary["holdings"], start=1):
        portfolio_chart_labels.append(holding["symbol"])
        raw_val = holding["current_value_display"].replace("£", "").replace("$", "").replace("HK$", "").replace(",", "")
        try:
            portfolio_chart_values.append(float(raw_val))
        except Exception:
            portfolio_chart_values.append(0)

    comparison_labels = [card["name"] for card in portfolio_cards]
    comparison_values = [card["total_value"] for card in portfolio_cards]

    return render_template(
        "index.html",
        view=view,
        risk=risk,
        market=market,
        signal=signal,
        risk_options=RISK_OPTIONS,
        market_options=MARKET_OPTIONS,
        signal_options=SIGNAL_OPTIONS,
        disclaimers=DISCLAIMERS,
        stocks=filtered_stocks,
        best=best,
        active_portfolio=active_portfolio,
        portfolio_summary=portfolio_summary,
        portfolio_cards=portfolio_cards,
        portfolio_chart_labels=portfolio_chart_labels,
        portfolio_chart_values=portfolio_chart_values,
        comparison_labels=comparison_labels,
        comparison_values=comparison_values,
        now=datetime.now().strftime("%H:%M:%S")
    )


@app.route("/onboarding")
def onboarding():
    ensure_state()
    return render_template(
        "onboarding.html",
        risk=session.get("user_risk", "Balanced"),
        risk_options=RISK_OPTIONS
    )


@app.route("/set-profile", methods=["POST"])
def set_profile():
    ensure_state()
    session["user_risk"] = request.form.get("risk", "Balanced")
    session.modified = True
    create_default_portfolio()
    return redirect("/")


@app.route("/portfolio/create", methods=["POST"])
def portfolio_create():
    ensure_state()
    name = request.form.get("name", "").strip() or "New Portfolio"
    risk = request.form.get("risk", "Balanced")
    market = request.form.get("market", "All Markets")
    currency = request.form.get("currency", "Mixed").strip() or "Mixed"

    pid = str(uuid.uuid4())
    portfolios = session["portfolios"]
    portfolios[pid] = {
        "id": pid,
        "name": name,
        "risk": risk,
        "market": market,
        "currency": currency,
        "holdings": []
    }
    session["portfolios"] = portfolios
    session["active_portfolio_id"] = pid
    session.modified = True
    return redirect("/?view=dashboard")


@app.route("/portfolio/select", methods=["POST"])
def portfolio_select():
    ensure_state()
    pid = request.form.get("portfolio_id")
    if pid in session["portfolios"]:
        session["active_portfolio_id"] = pid
        session.modified = True
    return redirect("/?view=dashboard")


@app.route("/portfolio/add", methods=["POST"])
def portfolio_add():
    ensure_state()
    active = get_active_portfolio()
    if not active:
        return redirect("/")

    symbol = request.form.get("symbol")
    units_text = request.form.get("units", "1").strip()

    try:
        units = float(units_text)
    except Exception:
        units = 1.0

    if units <= 0:
        units = 1.0

    stock = get_stock(symbol)
    if not stock:
        return redirect("/?view=opportunities")

    holdings = active["holdings"]
    for item in holdings:
        if item["symbol"] == symbol:
            item["units"] = float(item["units"]) + units
            session.modified = True
            return redirect("/?view=dashboard")

    holdings.append({
        "symbol": symbol,
        "units": units,
        "purchase_price": stock["price"],
        "purchase_date": datetime.now().strftime("%d %b %Y")
    })
    session.modified = True
    return redirect("/?view=dashboard")


@app.route("/portfolio/remove", methods=["POST"])
def portfolio_remove():
    ensure_state()
    active = get_active_portfolio()
    if not active:
        return redirect("/?view=dashboard")

    symbol = request.form.get("symbol")
    active["holdings"] = [h for h in active["holdings"] if h["symbol"] != symbol]
    session.modified = True
    return redirect("/?view=dashboard")


if __name__ == "__main__":
    app.run(debug=True)

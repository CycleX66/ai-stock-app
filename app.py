from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import uuid

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "cyclex-super-secret-key-change-this"

RISK_OPTIONS = ["Defensive", "Cautious", "Balanced", "Growth", "Aggressive"]
MARKET_OPTIONS = ["All Markets", "US", "UK", "Hong Kong"]
SIGNAL_OPTIONS = ["All Signals", "BUY", "HOLD", "SELL"]

STOCKS = [
    {
        "symbol": "MCD", "name": "McDonald's", "market": "US", "exchange": "NYSE", "currency": "USD",
        "signal": "BUY", "score": 97.4, "price": 304.85, "risk_band": "Low",
        "reason_short": "Defensive consumer name with strong relative score and steady price structure.",
        "reasoning": {
            "why_shown": "Ranks highly within the current filtered opportunity set.",
            "technical": "Stable price behaviour, constructive trend, lower volatility profile.",
            "fundamental": "Large-cap brand with resilient business model and defensive characteristics.",
            "event": "No adverse catalyst currently dominating the setup.",
            "macro": "More resilient in mixed macro conditions than higher-beta names.",
            "risk_fit": "Best aligned with Defensive and Cautious screening outputs."
        }
    },
    {
        "symbol": "MSFT", "name": "Microsoft", "market": "US", "exchange": "NASDAQ", "currency": "USD",
        "signal": "BUY", "score": 95.2, "price": 372.29, "risk_band": "Medium",
        "reason_short": "High-quality mega-cap with strong score and broad institutional support.",
        "reasoning": {
            "why_shown": "Strong rank across market quality, leadership, and signal consistency.",
            "technical": "Positive price structure and strong relative trend versus peers.",
            "fundamental": "High-quality revenue base, scale, profitability, and balance-sheet strength.",
            "event": "Supported by continuing AI and enterprise software narrative.",
            "macro": "Large-cap tech remains sensitive to rates but supported by structural demand.",
            "risk_fit": "Most suitable for Cautious, Balanced, Growth."
        }
    },
    {
        "symbol": "ULVR.L", "name": "Unilever", "market": "UK", "exchange": "LSE", "currency": "GBP",
        "signal": "BUY", "score": 95.6, "price": 42.72, "risk_band": "Low",
        "reason_short": "Lower-risk UK large-cap with defensive earnings profile and solid ranking.",
        "reasoning": {
            "why_shown": "Ranks strongly in lower-risk filtered output.",
            "technical": "Relatively stable trend with lower volatility than cyclical peers.",
            "fundamental": "Global consumer staples profile with diversified revenue base.",
            "event": "No major adverse event currently distorting the setup.",
            "macro": "Staples can be more defensive in uncertain environments.",
            "risk_fit": "Well suited to Defensive and Cautious screens."
        }
    },
    {
        "symbol": "SHEL.L", "name": "Shell", "market": "UK", "exchange": "LSE", "currency": "GBP",
        "signal": "HOLD", "score": 86.4, "price": 33.73, "risk_band": "Medium",
        "reason_short": "Strong underlying franchise but more mixed signal profile at current levels.",
        "reasoning": {
            "why_shown": "Still ranks well enough to remain visible, but signal is less compelling than top BUY names.",
            "technical": "More range-bound behaviour relative to leading BUY candidates.",
            "fundamental": "Major energy company with scale, cash generation, and commodity sensitivity.",
            "event": "Commodity price shifts can materially affect the outlook.",
            "macro": "Linked to global energy and geopolitical developments.",
            "risk_fit": "More suitable for Balanced and Growth than Defensive."
        }
    },
    {
        "symbol": "BARC.L", "name": "Barclays", "market": "UK", "exchange": "LSE", "currency": "GBP",
        "signal": "BUY", "score": 79.4, "price": 4.43, "risk_band": "Medium",
        "reason_short": "Financials exposure with reasonable score and cyclical upside characteristics.",
        "reasoning": {
            "why_shown": "Scores adequately within the UK/Balanced-style opportunity set.",
            "technical": "Acceptable structure, though less defensive than top staples/quality names.",
            "fundamental": "Banking exposure with sensitivity to rates and credit conditions.",
            "event": "Financial sector narratives can alter outlook quickly.",
            "macro": "Linked to rates, growth outlook, credit conditions and sentiment.",
            "risk_fit": "More suited to Balanced and Growth profiles."
        }
    },
    {
        "symbol": "0700.HK", "name": "Tencent", "market": "Hong Kong", "exchange": "HKEX", "currency": "HKD",
        "signal": "BUY", "score": 88.1, "price": 489.20, "risk_band": "Medium",
        "reason_short": "Large-cap Asia tech exposure with attractive ranking in Hong Kong filter set.",
        "reasoning": {
            "why_shown": "Ranks near the top of Hong Kong opportunities in current filters.",
            "technical": "Constructive structure versus local peers.",
            "fundamental": "Large platform business with diversified digital ecosystem exposure.",
            "event": "Policy and regulatory developments remain relevant to the thesis.",
            "macro": "Sensitive to China/Hong Kong sentiment and geopolitical headlines.",
            "risk_fit": "Best suited to Balanced and Growth."
        }
    },
    {
        "symbol": "1299.HK", "name": "AIA Group", "market": "Hong Kong", "exchange": "HKEX", "currency": "HKD",
        "signal": "BUY", "score": 77.6, "price": 88.65, "risk_band": "Medium",
        "reason_short": "Asian financial/insurance exposure with reasonable ranking and moderate risk.",
        "reasoning": {
            "why_shown": "Included due to competitive score within Hong Kong opportunities.",
            "technical": "Moderate trend support and reasonable relative ranking.",
            "fundamental": "Large regional insurer with long-duration business characteristics.",
            "event": "Sensitive to economic activity, rates and regional sentiment.",
            "macro": "Linked to Asia growth, rates and financial conditions.",
            "risk_fit": "Most relevant for Balanced and Growth."
        }
    },
    {
        "symbol": "NVDA", "name": "NVIDIA", "market": "US", "exchange": "NASDAQ", "currency": "USD",
        "signal": "HOLD", "score": 84.7, "price": 902.15, "risk_band": "High",
        "reason_short": "High-beta leadership stock with strong narrative but elevated risk characteristics.",
        "reasoning": {
            "why_shown": "High score keeps it visible even though risk band is elevated.",
            "technical": "Momentum remains important, but volatility and positioning are higher.",
            "fundamental": "Exceptional growth narrative, but expectations are also elevated.",
            "event": "News flow and earnings can materially re-price the stock quickly.",
            "macro": "Highly sensitive to rates, sentiment, and AI/semiconductor cycle narrative.",
            "risk_fit": "Best aligned with Growth and Aggressive profiles."
        }
    },
    {
        "symbol": "AAPL", "name": "Apple", "market": "US", "exchange": "NASDAQ", "currency": "USD",
        "signal": "BUY", "score": 91.8, "price": 188.54, "risk_band": "Low",
        "reason_short": "Mega-cap quality with lower relative risk and broad portfolio suitability.",
        "reasoning": {
            "why_shown": "Strong score and broad compatibility with multiple risk profiles.",
            "technical": "Stable trend profile with high liquidity and strong market sponsorship.",
            "fundamental": "Very large, profitable business with premium ecosystem characteristics.",
            "event": "Product cycle and services momentum remain relevant.",
            "macro": "Large-cap quality can hold up better than smaller high-beta names.",
            "risk_fit": "Suitable across Defensive, Cautious, Balanced and Growth filters."
        }
    },
    {
        "symbol": "AZN.L", "name": "AstraZeneca", "market": "UK", "exchange": "LSE", "currency": "GBP",
        "signal": "BUY", "score": 76.2, "price": 104.30, "risk_band": "Low",
        "reason_short": "Healthcare exposure supports lower-risk screening with stable quality profile.",
        "reasoning": {
            "why_shown": "Included due to lower-risk quality profile and acceptable score.",
            "technical": "Less aggressive but comparatively stable setup.",
            "fundamental": "Global pharmaceutical business with defensive characteristics.",
            "event": "Healthcare news flow matters, though less cyclical than many sectors.",
            "macro": "Healthcare often behaves more defensively in uncertain periods.",
            "risk_fit": "Particularly aligned with Defensive and Cautious screens."
        }
    },
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
        "currency": "GBP",
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
    total_value = 0.0
    portfolio_currency = portfolio.get("currency", "GBP")

    for holding in holdings:
        stock = get_stock(holding["symbol"])
        if not stock:
            continue

        units = float(holding["units"])
        current_price = float(stock["price"])
        purchase_price = float(holding["purchase_price"])
        current_value = units * current_price

        return_pct = 0.0
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

        if len(summary) == 1:
            portfolio_currency = stock["currency"]

    return {
        "holdings": summary,
        "holdings_count": len(summary),
        "total_value": round(total_value, 2),
        "total_value_display": money(total_value, portfolio_currency),
        "currency": portfolio_currency
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
            "total_value_display": summary["total_value_display"],
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

    owned_symbols = set()
    if active_portfolio:
        owned_symbols = {h["symbol"] for h in active_portfolio.get("holdings", [])}

    portfolio_chart_labels = []
    portfolio_chart_values = []
    for holding in portfolio_summary["holdings"]:
        portfolio_chart_labels.append(holding["symbol"])
        raw_val = (
            holding["current_value_display"]
            .replace("£", "")
            .replace("$", "")
            .replace("HK$", "")
            .replace(",", "")
        )
        try:
            portfolio_chart_values.append(float(raw_val))
        except Exception:
            portfolio_chart_values.append(0)

    comparison_labels = []
    comparison_values = []
    comparison_currencies = []

    for card in portfolio_cards:
        comparison_labels.append(card["name"])
        comparison_values.append(card["total_value"])
        comparison_currencies.append(card["currency"])

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
        owned_symbols=owned_symbols,
        portfolio_chart_labels=portfolio_chart_labels,
        portfolio_chart_values=portfolio_chart_values,
        comparison_labels=comparison_labels,
        comparison_values=comparison_values,
        comparison_currencies=comparison_currencies,
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
    currency = request.form.get("currency", "GBP").strip() or "GBP"

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

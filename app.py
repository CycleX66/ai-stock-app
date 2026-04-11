from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import uuid

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "cyclex-super-secret-key-change-this"

RISK_OPTIONS = ["Defensive", "Cautious", "Balanced", "Growth", "Aggressive"]
MARKET_OPTIONS = ["All Markets", "US", "UK", "Hong Kong", "Germany"]
SIGNAL_OPTIONS = ["All Signals", "BUY", "HOLD", "SELL"]
CURRENCY_OPTIONS = ["GBP", "USD", "HKD", "EUR", "Mixed"]

STOCKS = [
    {
        "symbol": "MCD", "name": "McDonald's", "market": "US", "exchange": "NYSE", "index": "Dow Jones", "currency": "USD",
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
        "symbol": "MSFT", "name": "Microsoft", "market": "US", "exchange": "NASDAQ", "index": "Nasdaq", "currency": "USD",
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
        "symbol": "ULVR.L", "name": "Unilever", "market": "UK", "exchange": "LSE", "index": "FTSE 100", "currency": "GBP",
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
        "symbol": "SHEL.L", "name": "Shell", "market": "UK", "exchange": "LSE", "index": "FTSE 100", "currency": "GBP",
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
        "symbol": "BARC.L", "name": "Barclays", "market": "UK", "exchange": "LSE", "index": "FTSE 100", "currency": "GBP",
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
        "symbol": "0700.HK", "name": "Tencent", "market": "Hong Kong", "exchange": "HKEX", "index": "Hang Seng", "currency": "HKD",
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
        "symbol": "1299.HK", "name": "AIA Group", "market": "Hong Kong", "exchange": "HKEX", "index": "Hang Seng", "currency": "HKD",
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
        "symbol": "NVDA", "name": "NVIDIA", "market": "US", "exchange": "NASDAQ", "index": "Nasdaq", "currency": "USD",
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
        "symbol": "AAPL", "name": "Apple", "market": "US", "exchange": "NASDAQ", "index": "Nasdaq", "currency": "USD",
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
        "symbol": "AZN.L", "name": "AstraZeneca", "market": "UK", "exchange": "LSE", "index": "FTSE 100", "currency": "GBP",
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
    {
        "symbol": "SAP.DE", "name": "SAP", "market": "Germany", "exchange": "XETRA", "index": "DAX", "currency": "EUR",
        "signal": "BUY", "score": 93.1, "price": 176.40, "risk_band": "Low",
        "reason_short": "High-quality DAX technology leader with strong ranking and broad institutional relevance.",
        "reasoning": {
            "why_shown": "Ranks highly within Germany/DAX opportunities.",
            "technical": "Constructive trend and strong relative strength against regional peers.",
            "fundamental": "Large-scale enterprise software franchise with resilient revenue quality.",
            "event": "Cloud and enterprise transition remains supportive.",
            "macro": "Large-cap quality name with broad institutional sponsorship.",
            "risk_fit": "Suitable across Defensive, Cautious, Balanced and Growth."
        }
    },
    {
        "symbol": "SIE.DE", "name": "Siemens", "market": "Germany", "exchange": "XETRA", "index": "DAX", "currency": "EUR",
        "signal": "BUY", "score": 86.5, "price": 178.90, "risk_band": "Medium",
        "reason_short": "Industrial quality name with strong DAX relevance and cyclical upside.",
        "reasoning": {
            "why_shown": "Ranks well in the German industrial opportunity set.",
            "technical": "Positive structure with solid relative momentum.",
            "fundamental": "Diversified industrial exposure with quality balance-sheet characteristics.",
            "event": "Capex and industrial demand trends remain key drivers.",
            "macro": "Sensitive to European industrial and macro cycles.",
            "risk_fit": "Best for Balanced and Growth."
        }
    },
    {
        "symbol": "ALV.DE", "name": "Allianz", "market": "Germany", "exchange": "XETRA", "index": "DAX", "currency": "EUR",
        "signal": "BUY", "score": 82.3, "price": 268.20, "risk_band": "Low",
        "reason_short": "Large-cap insurance exposure with lower-risk characteristics and solid ranking.",
        "reasoning": {
            "why_shown": "Defensive financial profile keeps it visible in lower-risk sets.",
            "technical": "Stable ranking and less aggressive volatility profile.",
            "fundamental": "Large insurer with durable cash generation and defensive qualities.",
            "event": "Insurance and rates environment remain relevant.",
            "macro": "Can benefit from stable financial conditions and rates backdrop.",
            "risk_fit": "Defensive, Cautious, Balanced."
        }
    },
    {
        "symbol": "DTE.DE", "name": "Deutsche Telekom", "market": "Germany", "exchange": "XETRA", "index": "DAX", "currency": "EUR",
        "signal": "HOLD", "score": 74.8, "price": 23.75, "risk_band": "Low",
        "reason_short": "Defensive telecom exposure with moderate score and steady profile.",
        "reasoning": {
            "why_shown": "Included due to defensive ranking and lower volatility characteristics.",
            "technical": "Steadier but less forceful than top BUY names.",
            "fundamental": "Telecom cash flow stability supports lower-risk screening.",
            "event": "Less catalyst-driven than higher-beta sectors.",
            "macro": "Can behave more defensively in uncertain periods.",
            "risk_fit": "Defensive and Cautious."
        }
    },
    {
        "symbol": "MBG.DE", "name": "Mercedes-Benz Group", "market": "Germany", "exchange": "XETRA", "index": "DAX", "currency": "EUR",
        "signal": "BUY", "score": 78.1, "price": 67.40, "risk_band": "Medium",
        "reason_short": "Cyclical auto exposure with value appeal and moderate ranking.",
        "reasoning": {
            "why_shown": "Included in German opportunities due to cyclical upside characteristics.",
            "technical": "Moderate trend support.",
            "fundamental": "Global auto brand with cyclical and valuation sensitivity.",
            "event": "Auto demand and global trade trends matter materially.",
            "macro": "Sensitive to European growth and consumer conditions.",
            "risk_fit": "Balanced and Growth."
        }
    }
]

DISCLAIMERS = [
    "CycleX AI provides market intelligence and analytics only. It does not provide personal financial advice.",
    "Investments can go down as well as up. You may get back less than you invest.",
    "Past performance is not a reliable indicator of future results.",
]

def currency_symbol(currency):
    return {"USD": "$", "GBP": "£", "HKD": "HK$", "EUR": "€", "Mixed": ""}.get(currency, "")

def money(value, currency):
    return f"{currency_symbol(currency)}{value:,.2f}" if currency != "Mixed" else f"{value:,.2f}"

def ensure_state():
    if "user_risk" not in session:
        session["user_risk"] = "Balanced"
    if "portfolios" not in session:
        session["portfolios"] = {}
    if "active_portfolio_id" not in session:
        session["active_portfolio_id"] = None
    if "portfolio_counter" not in session:
        session["portfolio_counter"] = 0

def next_portfolio_number():
    session["portfolio_counter"] = int(session.get("portfolio_counter", 0)) + 1
    session.modified = True
    return session["portfolio_counter"]

def create_default_portfolio():
    portfolios = session["portfolios"]
    if portfolios:
        return
    pid = str(uuid.uuid4())
    number = next_portfolio_number()
    portfolios[pid] = {
        "id": pid,
        "number": number,
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
            "index": stock["index"],
            "currency": stock["currency"],
            "units": units,
            "purchase_date": holding["purchase_date"],
            "purchase_price_display": money(purchase_price, stock["currency"]),
            "current_price_display": money(current_price, stock["currency"]),
            "current_value_display": money(current_value, stock["currency"]),
            "current_value_raw": round(current_value, 2),
            "return_pct": round(return_pct, 2),
        })

        if len(summary) == 1 and portfolio_currency == "Mixed":
            portfolio_currency = stock["currency"]

    summary.sort(key=lambda x: x["current_value_raw"], reverse=True)

    return {
        "holdings": summary,
        "holdings_count": len(summary),
        "total_value": round(total_value, 2),
        "total_value_display": money(total_value, portfolio_currency),
        "currency": portfolio_currency
    }

def portfolio_period_returns(total_value, holdings_count, number):
    base = 0.0
    if total_value > 0:
        base = min(18.0, 1.8 + (holdings_count * 0.85) + (number * 0.35))
    return {
        "1d": round(base * 0.12, 2),
        "1w": round(base * 0.28, 2),
        "1m": round(base * 0.60, 2),
        "3m": round(base * 1.00, 2),
        "6m": round(base * 1.45, 2),
        "1y": round(base * 2.10, 2),
        "2y": round(base * 2.75, 2),
        "3y": round(base * 3.20, 2),
    }

def build_portfolio_cards():
    cards = []
    portfolios = get_portfolios()
    active = get_active_portfolio()

    for pid, portfolio in portfolios.items():
        summary = build_portfolio_summary(portfolio)
        returns = portfolio_period_returns(summary["total_value"], summary["holdings_count"], portfolio["number"])
        cards.append({
            "id": pid,
            "number": portfolio["number"],
            "name": portfolio["name"],
            "risk": portfolio["risk"],
            "market": portfolio["market"],
            "currency": portfolio["currency"],
            "holdings_count": summary["holdings_count"],
            "total_value": summary["total_value"],
            "total_value_display": summary["total_value_display"],
            "returns": returns,
            "is_active": active and active["id"] == pid
        })
    cards.sort(key=lambda x: x["number"])
    return cards

def build_active_line_series(total_value):
    labels = ["1D", "1W", "1M", "3M", "6M", "1Y", "2Y", "3Y"]
    if total_value <= 0:
        return labels, [0, 0, 0, 0, 0, 0, 0, 0]

    values = [
        round(total_value * 0.92, 2),
        round(total_value * 0.90, 2),
        round(total_value * 0.87, 2),
        round(total_value * 0.84, 2),
        round(total_value * 0.80, 2),
        round(total_value * 0.75, 2),
        round(total_value * 0.69, 2),
        round(total_value * 0.63, 2),
    ]
    return labels, values

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

    pie_labels = []
    pie_values = []
    pie_details = []
    total_val = portfolio_summary["total_value"]

    for holding in portfolio_summary["holdings"]:
        pie_labels.append(holding["symbol"])
        pie_values.append(holding["current_value_raw"])
        pct = round((holding["current_value_raw"] / total_val) * 100, 2) if total_val > 0 else 0
        pie_details.append({
            "name": holding["name"],
            "symbol": holding["symbol"],
            "units": holding["units"],
            "percentage": pct,
            "value_display": holding["current_value_display"]
        })

    comparison_labels = []
    comparison_values = []
    comparison_currencies = []
    for card in portfolio_cards:
        comparison_labels.append(f"P{card['number']}")
        comparison_values.append(card["total_value"])
        comparison_currencies.append(card["currency"])

    performance_labels, performance_values = build_active_line_series(portfolio_summary["total_value"])

    return render_template(
        "index.html",
        view=view,
        risk=risk,
        market=market,
        signal=signal,
        risk_options=RISK_OPTIONS,
        market_options=MARKET_OPTIONS,
        signal_options=SIGNAL_OPTIONS,
        currency_options=CURRENCY_OPTIONS,
        disclaimers=DISCLAIMERS,
        stocks=filtered_stocks,
        best=best,
        active_portfolio=active_portfolio,
        portfolio_summary=portfolio_summary,
        portfolio_cards=portfolio_cards,
        owned_symbols=owned_symbols,
        pie_labels=pie_labels,
        pie_values=pie_values,
        pie_details=pie_details,
        comparison_labels=comparison_labels,
        comparison_values=comparison_values,
        comparison_currencies=comparison_currencies,
        performance_labels=performance_labels,
        performance_values=performance_values,
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
    number = next_portfolio_number()

    portfolios = session["portfolios"]
    portfolios[pid] = {
        "id": pid,
        "number": number,
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

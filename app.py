from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates")


STOCKS = [
    {"name": "McDonald's", "ticker": "MCD", "market": "US", "signal": "BUY", "score": 97.4},
    {"name": "Microsoft", "ticker": "MSFT", "market": "US", "signal": "BUY", "score": 95.2},
    {"name": "Unilever", "ticker": "ULVR.L", "market": "UK", "signal": "BUY", "score": 95.6},
    {"name": "Shell", "ticker": "SHEL.L", "market": "UK", "signal": "HOLD", "score": 86.4},
    {"name": "Barclays", "ticker": "BARC.L", "market": "UK", "signal": "SELL", "score": 72.1},
    {"name": "Tesla", "ticker": "TSLA", "market": "US", "signal": "BUY", "score": 93.8},
    {"name": "NVIDIA", "ticker": "NVDA", "market": "US", "signal": "BUY", "score": 96.1},
    {"name": "AstraZeneca", "ticker": "AZN.L", "market": "UK", "signal": "BUY", "score": 89.3},
    {"name": "HSBC", "ticker": "HSBA.L", "market": "UK", "signal": "HOLD", "score": 74.9},
    {"name": "Alibaba", "ticker": "9988.HK", "market": "Hong Kong", "signal": "BUY", "score": 82.7},
    {"name": "Tencent", "ticker": "0700.HK", "market": "Hong Kong", "signal": "BUY", "score": 90.4},
    {"name": "Reliance", "ticker": "RELIANCE.NS", "market": "India", "signal": "HOLD", "score": 77.8},
]

DISCLAIMERS = [
    "CycleX AI provides market intelligence and analytics only. It does not provide personal financial advice.",
    "Investments can go down as well as up. You may get back less than you invest.",
    "Past performance is not a reliable indicator of future results.",
]


@app.route("/")
def home():
    view = request.args.get("view", "opportunities")
    risk = request.args.get("risk", "All Risk Levels")
    market = request.args.get("market", "All Markets")

    filtered = STOCKS[:]

    if risk == "Low":
        filtered = [s for s in filtered if s["signal"] in ["BUY", "HOLD"] and s["score"] >= 80]
    elif risk == "Medium":
        filtered = [s for s in filtered if s["score"] >= 75]
    elif risk == "High":
        filtered = [s for s in filtered if s["signal"] in ["BUY", "SELL"]]

    if market != "All Markets":
        filtered = [s for s in filtered if s["market"] == market]

    return render_template(
        "index.html",
        view=view,
        stocks=filtered,
        disclaimers=DISCLAIMERS,
        risk=risk,
        market=market
    )


@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")


if __name__ == "__main__":
    app.run(debug=True)

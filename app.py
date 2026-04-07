from flask import Flask, render_template, request

app = Flask(__name__)

# Dummy stock data (safe fallback)
stocks = [
    {"name": "Tesla, Inc.", "ticker": "TSLA", "score": 97.9, "signal": "BUY"},
    {"name": "Microsoft Corporation", "ticker": "MSFT", "score": 95.7, "signal": "BUY"},
    {"name": "AstraZeneca plc", "ticker": "AZN.L", "score": 77.7, "signal": "BUY"},
]

@app.route("/")
def home():
    return render_template("index.html", stocks=stocks)

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

@app.route("/set-risk")
def set_risk():
    risk = request.args.get("risk", "balanced")
    return render_template("index.html", stocks=stocks, risk=risk)

if __name__ == "__main__":
    app.run(debug=True)

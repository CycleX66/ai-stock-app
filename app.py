from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates")

# Simple safe stock list
stocks = [
    {"name": "Tesla, Inc.", "ticker": "TSLA", "score": 97.9, "signal": "BUY"},
    {"name": "Microsoft Corporation", "ticker": "MSFT", "score": 95.7, "signal": "BUY"},
    {"name": "AstraZeneca plc", "ticker": "AZN.L", "score": 77.7, "signal": "BUY"},
]

@app.route("/")
def home():
    risk = request.args.get("risk", "balanced")
    best = stocks[0] if stocks else None

    return render_template(
        "index.html",
        stocks=stocks,
        scored=stocks,
        best=best,
        risk=risk
    )

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

if __name__ == "__main__":
    app.run(debug=True)

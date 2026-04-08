from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates")

stocks = [
    {"name": "Tesla, Inc.", "ticker": "TSLA", "score": 97.9, "signal": "BUY"},
    {"name": "Microsoft Corporation", "ticker": "MSFT", "score": 95.7, "signal": "BUY"},
    {"name": "AstraZeneca plc", "ticker": "AZN.L", "score": 77.7, "signal": "BUY"},
]

@app.route("/")
def home():
    risk = request.args.get("risk", "defensive").lower()
    best = stocks[0] if stocks else None

    return render_template(
        "index.html",
        scored=stocks,
        best=best,
        risk=risk
    )

@app.route("/onboarding")
def onboarding():
    risk = request.args.get("risk", "defensive").lower()
    return render_template("onboarding.html", risk=risk)

if __name__ == "__main__":
    app.run(debug=True)

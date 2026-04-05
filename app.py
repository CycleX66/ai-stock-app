from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Your AI Stock App is LIVE 🚀"

if __name__ == "__main__":
    app.run()

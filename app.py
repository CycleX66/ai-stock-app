from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template, request, redirect, url_for

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SETTINGS_PATH = DATA_DIR / "settings.json"
STATE_PATH = DATA_DIR / "paper_state.json"

DEFAULT_SETTINGS = {
    "markets": "both",
    "uk_symbols": ["BP.L", "HSBA.L", "ULVR.L", "SHEL.L", "AZN.L", "BARC.L"],
    "us_symbols": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "SPY"],
    "custom_symbols": [],
    "starting_cash": 100000.0,
    "safe_mode": True,
}

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_settings():
    settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    return merged

def save_settings(settings):
    save_json(SETTINGS_PATH, settings)

def load_state(settings):
    default_state = {
        "cash": settings["starting_cash"],
        "positions": {},
        "history": [],
        "last_run_utc": None,
    }
    state = load_json(STATE_PATH, default_state)
    state.setdefault("cash", settings["starting_cash"])
    state.setdefault("positions", {})
    state.setdefault("history", [])
    state.setdefault("last_run_utc", None)
    return state

def save_state(state):
    save_json(STATE_PATH, state)

def clean_symbols(symbols):
    out, seen = [], set()
    for s in symbols:
        s = str(s).strip().upper()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out

def get_all_symbols(settings):
    uk = clean_symbols(settings["uk_symbols"])
    us = clean_symbols(settings["us_symbols"])
    custom = clean_symbols(settings.get("custom_symbols", []))
    return clean_symbols(uk + us + custom)

def is_bst(now_utc: datetime) -> bool:
    return 4 <= now_utc.month <= 10

def market_status():
    now_utc = datetime.now(timezone.utc)
    uk_now = now_utc + timedelta(hours=1 if is_bst(now_utc) else 0)
    uk_open = now_utc.weekday() < 5 and ((8 <= uk_now.hour < 16) or (uk_now.hour == 16 and uk_now.minute <= 30))
    us_open = now_utc.weekday() < 5 and ((14 <= now_utc.hour < 21) or (now_utc.hour == 21 and now_utc.minute == 0))
    return {"uk": "OPEN" if uk_open else "CLOSED", "us": "OPEN" if us_open else "CLOSED"}

def fetch_data(symbols, period="6mo", interval="1d"):
    if not symbols:
        return pd.DataFrame()
    data = yf.download(
        tickers=symbols,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    rows = []
    if isinstance(data.columns, pd.MultiIndex):
        for symbol in symbols:
            if symbol not in data.columns.levels[0]:
                continue
            sdf = data[symbol].dropna().copy()
            if sdf.empty:
                continue
            sdf["symbol"] = symbol
            sdf = sdf.reset_index().rename(columns={"Date": "date", "Datetime": "date"})
            rows.append(sdf[["date", "symbol", "Open", "High", "Low", "Close", "Volume"]])
    else:
        sdf = data.dropna().copy()
        if not sdf.empty:
            sdf["symbol"] = symbols[0]
            sdf = sdf.reset_index().rename(columns={"Date": "date", "Datetime": "date"})
            rows.append(sdf[["date", "symbol", "Open", "High", "Low", "Close", "Volume"]])
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out.columns = [c.lower() for c in out.columns]
    return out.sort_values(["symbol", "date"]).reset_index(drop=True)

def calc_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def score_symbols(df, settings):
    if df.empty:
        return pd.DataFrame(columns=[
            "symbol", "market", "signal", "confidence", "score", "close",
            "daily_move", "rsi", "ma_fast", "ma_slow", "trend"
        ])

    result = []
    for symbol, sdf in df.groupby("symbol"):
        sdf = sdf.sort_values("date").copy()
        if len(sdf) < 60:
            continue

        close = sdf["close"]
        volume = sdf["volume"].replace(0, np.nan)

        ma_fast = close.rolling(10).mean().iloc[-1]
        ma_slow = close.rolling(30).mean().iloc[-1]
        rsi = calc_rsi(close, 14).iloc[-1]
        ret_5 = close.iloc[-1] / close.iloc[-6] - 1 if len(close) >= 6 else 0
        ret_20 = close.iloc[-1] / close.iloc[-21] - 1 if len(close) >= 21 else 0
        daily_move = close.iloc[-1] / close.iloc[-2] - 1 if len(close) >= 2 else 0
        vol_20 = close.pct_change().rolling(20).std().iloc[-1]
        range_pct = (sdf["high"].iloc[-1] - sdf["low"].iloc[-1]) / close.iloc[-1]

        vol_mean = volume.rolling(20).mean().iloc[-1]
        vol_std = volume.rolling(20).std().iloc[-1]
        vol_z = ((volume.iloc[-1] - vol_mean) / vol_std) if pd.notna(vol_std) and vol_std != 0 else 0

        trend = 1 if ma_fast > ma_slow else -1
        rsi_score = 0
        if rsi < 35:
            rsi_score = 0.8
        elif rsi > 65:
            rsi_score = -0.8

        raw_score = (
            2.2 * ret_5 +
            1.6 * ret_20 +
            0.9 * ((close.iloc[-1] / ma_fast) - 1 if pd.notna(ma_fast) and ma_fast else 0) +
            1.1 * ((close.iloc[-1] / ma_slow) - 1 if pd.notna(ma_slow) and ma_slow else 0) +
            0.45 * trend +
            0.18 * np.clip(vol_z, -3, 3) +
            rsi_score -
            0.45 * (0 if pd.isna(vol_20) else vol_20) -
            0.15 * range_pct
        )

        if settings.get("safe_mode", True):
            raw_score *= 0.85

        confidence = float(np.clip(50 + raw_score * 18, 0, 100))

        if confidence >= 60:
            signal = "BUY"
        elif confidence <= 40:
            signal = "SELL"
        else:
            signal = "HOLD"

        result.append({
            "symbol": symbol,
            "market": "UK" if symbol.endswith(".L") else "US",
            "signal": signal,
            "confidence": round(confidence, 1),
            "score": round(raw_score, 3),
            "close": round(float(close.iloc[-1]), 2),
            "daily_move": round(float(daily_move) * 100, 2),
            "rsi": round(float(rsi), 1),
            "ma_fast": round(float(ma_fast), 2),
            "ma_slow": round(float(ma_slow), 2),
            "trend": "Up" if trend == 1 else "Down",
        })

    out = pd.DataFrame(result)
    if out.empty:
        return out

    return out.sort_values(["confidence", "symbol"], ascending=[False, True]).reset_index(drop=True)

def get_filtered_scored(settings):
    scored = score_symbols(fetch_data(get_all_symbols(settings)), settings)
    if settings["markets"] == "uk":
        scored = scored[scored["market"] == "UK"]
    elif settings["markets"] == "us":
        scored = scored[scored["market"] == "US"]
    return scored.reset_index(drop=True)

def pick_best(scored):
    if scored.empty:
        return None
    tradable = scored[scored["signal"] != "HOLD"]
    if tradable.empty:
        return scored.iloc[0].to_dict()
    buys = tradable[tradable["signal"] == "BUY"].sort_values("confidence", ascending=False)
    if not buys.empty:
        return buys.iloc[0].to_dict()
    sells = tradable[tradable["signal"] == "SELL"].sort_values("confidence", ascending=True)
    return sells.iloc[0].to_dict() if not sells.empty else tradable.iloc[0].to_dict()

def run_paper_trade(settings):
    scored = get_filtered_scored(settings)
    state = load_state(settings)
    best = pick_best(scored)
    now = datetime.now(timezone.utc).isoformat()

    if best is None:
        state["last_run_utc"] = now
        save_state(state)
        return scored, state, None

    symbol, price, signal = best["symbol"], best["close"], best["signal"]

    if signal == "BUY" and symbol not in state["positions"]:
        budget = min(state["cash"] * 0.2, settings["starting_cash"] * 0.2)
        qty = int(budget / price)
        if qty > 0:
            state["positions"][symbol] = {"qty": qty, "entry_price": price}
            state["cash"] -= qty * price
            state["history"].append({"time": now, "action": "BUY", "symbol": symbol, "qty": qty, "price": price})
    elif signal == "SELL" and symbol in state["positions"]:
        qty = state["positions"][symbol]["qty"]
        state["cash"] += qty * price
        state["history"].append({"time": now, "action": "SELL", "symbol": symbol, "qty": qty, "price": price})
        del state["positions"][symbol]

    state["last_run_utc"] = now
    save_state(state)
    return scored, state, best

def portfolio_value(state, scored):
    latest = {r["symbol"]: r["close"] for _, r in scored.iterrows()} if not scored.empty else {}
    value = float(state["cash"])
    for sym, pos in state["positions"].items():
        value += pos["qty"] * latest.get(sym, pos["entry_price"])
    return round(value, 2)

app = Flask(__name__)

@app.route("/")
def index():
    settings = load_settings()
    scored, state, best = run_paper_trade(settings)
    auto_picks = scored[scored["signal"] != "HOLD"].head(5).to_dict(orient="records") if not scored.empty else []
    return render_template(
        "index.html",
        settings=settings,
        best=best,
        scored=scored.to_dict(orient="records"),
        auto_picks=auto_picks,
        statuses=market_status(),
        paper_value=portfolio_value(state, scored),
        cash=round(state["cash"], 2),
        positions=state["positions"],
        history=list(reversed(state["history"][-10:])),
        last_run=state.get("last_run_utc"),
        custom_set=set(clean_symbols(settings.get("custom_symbols", []))),
    )

@app.route("/settings", methods=["POST"])
def update_settings():
    settings = load_settings()
    settings.update({
        "markets": request.form.get("markets", "both"),
        "safe_mode": request.form.get("safe_mode") == "on",
    })
    save_settings(settings)
    return redirect(url_for("index"))

@app.route("/add_symbol", methods=["POST"])
def add_symbol():
    symbol = request.form.get("symbol", "").strip().upper()
    settings = load_settings()
    custom = clean_symbols(settings.get("custom_symbols", []))
    universe = clean_symbols(settings["uk_symbols"] + settings["us_symbols"] + custom)
    if symbol and symbol not in universe:
        custom.append(symbol)
        settings["custom_symbols"] = custom
        save_settings(settings)
    return redirect(url_for("index"))

@app.route("/remove_symbol/<symbol>", methods=["POST"])
def remove_symbol(symbol):
    settings = load_settings()
    settings["custom_symbols"] = [s for s in clean_symbols(settings.get("custom_symbols", [])) if s != symbol.upper()]
    save_settings(settings)
    return redirect(url_for("index"))

@app.route("/reset_paper", methods=["POST"])
def reset_paper():
    settings = load_settings()
    save_state({"cash": settings["starting_cash"], "positions": {}, "history": [], "last_run_utc": None})
    return redirect(url_for("index"))

@app.route("/api/status")
def api_status():
    settings = load_settings()
    scored, state, best = run_paper_trade(settings)
    return jsonify({
        "best": best,
        "scored": scored.to_dict(orient="records"),
        "portfolio_value": portfolio_value(state, scored),
        "cash": state["cash"],
        "positions": state["positions"],
        "last_run_utc": state.get("last_run_utc"),
        "market_status": market_status(),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

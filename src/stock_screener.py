"""
FCAAK Stock Screener for IDX (Bursa Efek Indonesia).

Screening commands:
  /Score bb5              : Bullish Bias 5 — sangat oversold, near major bottom (favorit)
  /Score bb4              : Bullish Bias 4 — lebih agresif, menangkap pisau jatuh
  /Score acrev            : Accumulation Reversal — divergence + spike
  /Score acrev,nf3d       : ACREV + net foreign buy 3 hari (approximated via volume)
  /Score pc;1             : Price Concentration level 1 (tightest, <3% range)
  /Score pc;2             : Price Concentration level 2 (<5% range)
  /Score pc;3             : Price Concentration level 3 (<8% range)
  /Score hlfibo;90;0;2    : HL Fibonacci screening

FCAAK analysis criteria (ALL must pass ideally):
  ✓ Bullish divergence (RSI composite vs price)
  ✓ Volume spike
  ✓ Tidak membuat lower low baru
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from src.stock_data import fetch_ohlcv, get_screener_universe
from src.stock_indicators import (
    calculate_rsi_composite,
    calculate_bollinger,
    calculate_hl_fibonacci,
    calculate_frequency,
    detect_bullish_divergence,
    detect_volume_spike,
    nearest_fib_level,
)

_WORKERS = 5


# ── BB5 / BB4 ────────────────────────────────────────────────────────────────

def _score_bb(ticker: str, rsi_max: float, proximity_max_pct: float) -> Optional[dict]:
    import pandas as pd
    df = fetch_ohlcv(ticker, period="1y", interval="1d")
    if df.empty or len(df) < 60:
        return None

    rsi   = calculate_rsi_composite(df)
    freq  = calculate_frequency(df)

    cur_close = float(df["Close"].iloc[-1])
    cur_rsi   = float(rsi.iloc[-1])

    # Skip if RSI could not be calculated (bad/insufficient data)
    if pd.isna(cur_rsi) or pd.isna(cur_close):
        return None

    low_52w   = float(df["Low"].tail(252).min())
    proximity = (cur_close - low_52w) / low_52w * 100

    if cur_rsi > rsi_max or proximity > proximity_max_pct:
        return None

    # Lower-low check
    recent_low = float(df["Low"].tail(5).min())
    prev_low   = float(df["Low"].tail(20).head(15).min())
    no_new_ll  = recent_low >= prev_low * 0.98

    div   = detect_bullish_divergence(df["Close"], rsi)
    spike = detect_volume_spike(df)

    score = 0
    if div:        score += 30
    if spike:      score += 20
    if no_new_ll:  score += 20
    score += 15 if cur_rsi < 25 else (10 if cur_rsi < 30 else 0)
    score += 15 if proximity < 5 else (10 if proximity < 10 else 0)

    return {
        "ticker":       ticker,
        "price":        round(cur_close, 0),
        "rsi":          round(cur_rsi, 1),
        "proximity_pct": round(proximity, 1),
        "divergence":   div,
        "spike":        spike,
        "no_new_ll":    no_new_ll,
        "score":        score,
    }


def score_bb5(universe: Optional[list] = None) -> list[dict]:
    """BB5: RSI < 25, within 10% of 52-week low."""
    tickers = universe or get_screener_universe()
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_score_bb, t, 25.0, 10.0): t for t in tickers}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    return sorted(results, key=lambda x: x["score"], reverse=True)


def score_bb4(universe: Optional[list] = None) -> list[dict]:
    """BB4: RSI < 35, within 20% of 52-week low. Lebih agresif."""
    tickers = universe or get_screener_universe()
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_score_bb, t, 35.0, 20.0): t for t in tickers}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    return sorted(results, key=lambda x: x["score"], reverse=True)


# ── ACREV ────────────────────────────────────────────────────────────────────

def _score_acrev(ticker: str) -> Optional[dict]:
    import pandas as pd
    df = fetch_ohlcv(ticker, period="6mo", interval="1d")
    if df.empty or len(df) < 30:
        return None

    rsi  = calculate_rsi_composite(df)
    freq = calculate_frequency(df)

    cur_close = float(df["Close"].iloc[-1])
    cur_rsi   = float(rsi.iloc[-1])
    if pd.isna(cur_rsi) or pd.isna(cur_close):
        return None

    div   = detect_bullish_divergence(df["Close"], rsi)
    spike = detect_volume_spike(df)

    if not div and not spike:
        return None

    # Price range over last 10 bars (consolidation proxy)
    recent_rng = (float(df["High"].tail(10).max()) - float(df["Low"].tail(10).min())) / cur_close * 100

    return {
        "ticker":       ticker,
        "price":        round(cur_close, 0),
        "rsi":          round(cur_rsi, 1),
        "divergence":   div,
        "spike":        spike,
        "range_pct":    round(recent_rng, 1),
    }


def score_acrev(universe: Optional[list] = None) -> list[dict]:
    """ACREV: bullish divergence + volume spike."""
    tickers = universe or get_screener_universe()
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_score_acrev, t): t for t in tickers}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    # Sort: both signals first, then divergence-only
    return sorted(results, key=lambda x: (x["divergence"] and x["spike"],
                                          x["divergence"], x["spike"]), reverse=True)


# ── PC (Price Concentration) ─────────────────────────────────────────────────

def _score_pc(ticker: str, level: int) -> Optional[dict]:
    import pandas as pd
    thresholds = {1: 3.0, 2: 5.0, 3: 8.0}
    thr = thresholds.get(level, 5.0)

    df = fetch_ohlcv(ticker, period="3mo", interval="1d")
    if df.empty or len(df) < 15:
        return None

    rsi = calculate_rsi_composite(df)
    cur_close = float(df["Close"].iloc[-1])
    if pd.isna(cur_close):
        return None

    rng = (float(df["High"].tail(10).max()) - float(df["Low"].tail(10).min())) / cur_close * 100
    if rng > thr:
        return None

    return {
        "ticker":    ticker,
        "price":     round(cur_close, 0),
        "rsi":       round(float(rsi.iloc[-1]), 1),
        "range_pct": round(rng, 2),
        "level":     level,
    }


def score_pc(level: int = 1, universe: Optional[list] = None) -> list[dict]:
    """PC: Price Concentration — tight range over last 10 bars."""
    tickers = universe or get_screener_universe()
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_score_pc, t, level): t for t in tickers}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    return sorted(results, key=lambda x: x["range_pct"])


# ── HLFIBO ───────────────────────────────────────────────────────────────────

def _score_hlfibo(ticker: str, proximity_pct: float, min_level: float, quality: int) -> Optional[dict]:
    import pandas as pd
    df = fetch_ohlcv(ticker, period="1y", interval="1d")
    if df.empty or len(df) < 60:
        return None

    fib = calculate_hl_fibonacci(df)
    rsi = calculate_rsi_composite(df)
    cur_close = float(df["Close"].iloc[-1])
    cur_rsi   = float(rsi.iloc[-1])
    if pd.isna(cur_close) or pd.isna(cur_rsi):
        return None

    # Support-zone fibonacci levels
    support_lvls = ["0.236", "0.382", "0.5", "0.618"]
    check_lvls   = support_lvls if quality >= 2 else list(fib["levels"].keys())

    for lv in check_lvls:
        if float(lv) < min_level:
            continue
        fib_px  = fib["levels"][lv]
        prox    = abs(cur_close - fib_px) / fib_px * 100
        if prox <= (100 - proximity_pct):
            return {
                "ticker":       ticker,
                "price":        round(cur_close, 0),
                "rsi":          round(cur_rsi, 1),
                "fib_level":    lv,
                "fib_price":    round(fib_px, 0),
                "proximity_pct": round(prox, 1),
            }
    return None


def score_hlfibo(proximity_pct: float = 90, min_level: float = 0,
                 quality: int = 2, universe: Optional[list] = None) -> list[dict]:
    """HLFIBO: stocks near a HL-Fibonacci support level."""
    tickers = universe or get_screener_universe()
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        futs = {ex.submit(_score_hlfibo, t, proximity_pct, min_level, quality): t
                for t in tickers}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
    return sorted(results, key=lambda x: x["proximity_pct"])


# ── Output formatter ─────────────────────────────────────────────────────────

def format_screening_results(results: list[dict], label: str, limit: int = 20) -> str:
    if not results:
        return (
            f"🔍 *Score {label}*\n\n"
            "Tidak ada saham yang memenuhi kriteria saat ini.\n"
            "_Coba lagi nanti atau gunakan screening lain._"
        )

    lines = [f"🔍 *Score {label}* — {len(results)} saham", ""]

    for i, r in enumerate(results[:limit], 1):
        ticker = r["ticker"]
        price  = r.get("price", 0)
        rsi    = r.get("rsi", "—")

        badges = []
        if r.get("divergence"):  badges.append("📈Div")
        if r.get("spike"):       badges.append("⚡Spike")
        if r.get("no_new_ll"):   badges.append("✓NoLL")

        meta = []
        if "score"        in r: meta.append(f"Skor:{r['score']}")
        if "proximity_pct" in r: meta.append(f"±{r['proximity_pct']}%52L")
        if "range_pct"    in r: meta.append(f"Range:{r['range_pct']}%")
        if "fib_level"    in r: meta.append(f"Fib:{r['fib_level']}")

        line = f"{i}. *{ticker}* — {price:,.0f}  RSI {rsi}"
        if badges: line += f"  {' '.join(badges)}"
        if meta:   line += f"\n   {' | '.join(meta)}"
        lines.append(line)

    if len(results) > limit:
        lines.append(f"\n_...+{len(results) - limit} saham lainnya_")

    lines.append(f"\n_Chart: /C [ticker] p1,o5,i59,i106_")
    return "\n".join(lines)


# ── Command router ───────────────────────────────────────────────────────────

def run_score_command(command: str) -> str:
    """
    Parse and execute a /Score command string.
    e.g. 'bb5', 'acrev,nf3d', 'pc;1', 'hlfibo;90;0;2'
    """
    parts    = command.strip().lower().split(",")
    main_cmd = parts[0].strip()

    print(f"[Screener] /Score {command}")

    if main_cmd == "bb5":
        return format_screening_results(score_bb5(), "BB5")

    if main_cmd == "bb4":
        return format_screening_results(score_bb4(), "BB4")

    if main_cmd == "acrev":
        return format_screening_results(score_acrev(), "ACREV")

    if main_cmd.startswith("pc"):
        sub   = main_cmd.split(";")
        level = int(sub[1]) if len(sub) > 1 else 1
        return format_screening_results(score_pc(level), f"PC;{level}")

    if main_cmd.startswith("hlfibo"):
        sub   = main_cmd.split(";")
        prox  = float(sub[1]) if len(sub) > 1 else 90
        minlv = float(sub[2]) if len(sub) > 2 else 0
        qual  = int(sub[3])   if len(sub) > 3 else 2
        return format_screening_results(
            score_hlfibo(prox, minlv, qual), f"HLFIBO;{prox};{minlv};{qual}"
        )

    return (
        f"❌ Perintah tidak dikenal: /Score {command}\n\n"
        "*Perintah tersedia:*\n"
        "/Score bb5\n"
        "/Score bb4\n"
        "/Score acrev\n"
        "/Score pc;1  (atau ;2, ;3)\n"
        "/Score hlfibo;90;0;2"
    )

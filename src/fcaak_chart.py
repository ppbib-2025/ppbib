"""
FCAAK Chart Generator for Indonesian stock analysis.

Standard FCAAK chart: /C {ticker} p1,o5,i59,i106
  p1   = daily candlestick
  o5   = Bollinger Bands overlay
  i59  = RSI Composite panel
  i106 = Frequency Analyzer panel
  (HL Fibonacci is always included)

Analysis checklist (FCAAK method):
  1. Bullish divergence di RSI composite vs harga
  2. Spike di frequency analyzer
  3. Tidak membuat LL (lower low) baru
"""
import io
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from src.stock_data import fetch_ohlcv
from src.stock_indicators import (
    calculate_rsi_composite,
    calculate_bollinger,
    calculate_hl_fibonacci,
    calculate_frequency,
    detect_bullish_divergence,
    detect_volume_spike,
    nearest_fib_level,
)

# Period code → (yfinance period, interval)
PERIOD_MAP = {
    "1": ("6mo", "1d"),
    "2": ("2y",  "1wk"),
    "3": ("5y",  "1mo"),
    "4": ("1mo", "60m"),
    "5": ("5d",  "15m"),
}

_DARK   = "#1a1a2e"
_GRID   = "#2a2a4a"
_UP     = "#26a69a"
_DOWN   = "#ef5350"
_BB     = "#4fc3f7"
_RSI    = "#ab47bc"
_FREQ_P = "#42a5f5"
_FREQ_N = "#ef5350"
_WHITE  = "#e0e0e0"
_GRAY   = "#888888"

FIBO_COLORS = {
    "0":     "#ff5252",
    "0.236": "#ff9800",
    "0.382": "#ffeb3b",
    "0.5":   "#8bc34a",
    "0.618": "#26a69a",
    "0.786": "#29b6f6",
    "1":     "#7e57c2",
}

OUTPUT_DIR = "data/charts"


def parse_chart_params(params_str: str) -> dict:
    """Parse 'p1,o5,i59,i106' into structured dict."""
    result = {"period": "1", "overlays": [], "indicators": []}
    for token in params_str.split(","):
        t = token.strip()
        if t.startswith("p"):
            result["period"] = t[1:]
        elif t.startswith("o"):
            result["overlays"].append(t[1:])
        elif t.startswith("i"):
            result["indicators"].append(t[1:])
    return result


def generate_fcaak_chart(ticker: str, params_str: str = "p1,o5,i59,i106") -> tuple:
    """
    Generate FCAAK chart image bytes and analysis dict.
    Returns (image_bytes | None, analysis_dict).
    """
    params = parse_chart_params(params_str)
    yf_period, interval = PERIOD_MAP.get(params["period"], ("6mo", "1d"))

    df = fetch_ohlcv(ticker, period=yf_period, interval=interval)
    if df.empty or len(df) < 30:
        return None, {"error": f"Data tidak tersedia untuk {ticker.upper()}"}

    use_bb   = "5"   in params["overlays"]
    use_rsi  = "59"  in params["indicators"]
    use_freq = "106" in params["indicators"]

    rsi_comp = calculate_rsi_composite(df) if use_rsi else None
    bb       = calculate_bollinger(df)     if use_bb   else None
    fib      = calculate_hl_fibonacci(df)
    freq     = calculate_frequency(df)    if use_freq else None

    current_price = float(df["Close"].iloc[-1])
    bullish_div   = detect_bullish_divergence(df["Close"], rsi_comp) if rsi_comp is not None else False
    vol_spike     = detect_volume_spike(df) if freq is not None else False

    current_rsi  = float(rsi_comp.iloc[-1]) if rsi_comp is not None else None
    fib_lv, fib_px = nearest_fib_level(current_price, fib)

    # LL check: recent 5-bar low vs previous 15-bar low
    recent_low = float(df["Low"].tail(5).min())
    prev_low   = float(df["Low"].tail(20).head(15).min())
    no_new_ll  = recent_low >= prev_low * 0.98

    analysis = {
        "ticker":            ticker.upper(),
        "price":             current_price,
        "rsi_composite":     round(current_rsi, 1) if current_rsi is not None else None,
        "bullish_divergence": bullish_div,
        "volume_spike":      vol_spike,
        "no_new_ll":         no_new_ll,
        "fib_level":         fib_lv,
        "fib_price":         round(fib_px, 0),
        "fib_range":         {"high": round(fib["high"], 0), "low": round(fib["low"], 0)},
        "period":            yf_period,
        "interval":          interval,
    }

    try:
        img_bytes = _draw_chart(df, ticker, rsi_comp, bb, fib, freq, analysis)
        return img_bytes, analysis
    except Exception as e:
        print(f"[FCAAK] Chart error for {ticker}: {e}")
        return None, {**analysis, "chart_error": str(e)}


def _draw_chart(df, ticker, rsi_comp, bb, fib, freq, analysis) -> bytes:
    panels = 1 + (1 if rsi_comp is not None else 0) + (1 if freq is not None else 0)
    ratios = [3] + [1] * (panels - 1)

    fig = plt.figure(figsize=(14, 8), facecolor=_DARK)
    gs  = GridSpec(panels, 1, figure=fig, hspace=0.04, height_ratios=ratios)
    axes = [fig.add_subplot(gs[i]) for i in range(panels)]

    for ax in axes:
        ax.set_facecolor(_DARK)
        ax.tick_params(colors=_GRAY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(_GRID)
        ax.yaxis.tick_right()
        ax.grid(True, color=_GRID, linewidth=0.5, alpha=0.6)

    ax_main = axes[0]
    panel_idx = 1
    n = len(df)
    xs = np.arange(n)

    # ── Candlestick ──────────────────────────────────────────────────────────
    opens  = df["Open"].values
    highs  = df["High"].values
    lows   = df["Low"].values
    closes = df["Close"].values

    for i in xs:
        color = _UP if closes[i] >= opens[i] else _DOWN
        ax_main.plot([i, i], [lows[i], highs[i]], color=color, linewidth=0.7)
        body_h = abs(closes[i] - opens[i]) or (highs[i] - lows[i]) * 0.005
        ax_main.bar(i, body_h, bottom=min(opens[i], closes[i]),
                    color=color, width=0.6, zorder=2)

    # ── Bollinger Bands ──────────────────────────────────────────────────────
    if bb is not None:
        bb_u = bb["upper"].values
        bb_m = bb["middle"].values
        bb_l = bb["lower"].values
        ax_main.plot(xs, bb_u, color=_BB, linewidth=0.8, alpha=0.7)
        ax_main.plot(xs, bb_m, color=_WHITE, linewidth=0.7, alpha=0.4, linestyle="--")
        ax_main.plot(xs, bb_l, color=_BB, linewidth=0.8, alpha=0.7)
        ax_main.fill_between(xs, bb_u, bb_l, alpha=0.04, color=_BB)

    # ── HL Fibonacci ─────────────────────────────────────────────────────────
    p_min = float(df["Low"].min()) * 0.95
    p_max = float(df["High"].max()) * 1.05
    for lv, px in fib["levels"].items():
        if p_min <= px <= p_max:
            c = FIBO_COLORS.get(lv, _WHITE)
            ax_main.axhline(y=px, color=c, linewidth=0.7, alpha=0.6, linestyle=":")
            ax_main.text(n + 0.5, px, f"F{lv}", color=c, fontsize=6, va="center")

    ax_main.set_xlim(-1, n + 6)
    ax_main.set_ylabel("Price (IDR)", color=_GRAY, fontsize=8)

    # Title
    signals = []
    if analysis.get("bullish_divergence"):
        signals.append("✓ Bullish Div")
    if analysis.get("volume_spike"):
        signals.append("⚡ Spike")
    if analysis.get("no_new_ll"):
        signals.append("✓ No-LL")
    rsi_str = f"RSI: {analysis['rsi_composite']}" if analysis.get("rsi_composite") else ""
    title = f"FCAAK | {ticker.upper()} | {rsi_str}"
    if signals:
        title += "  |  " + " | ".join(signals)
    ax_main.set_title(title, color=_WHITE, fontsize=10, pad=6, loc="left")

    # ── RSI Composite ────────────────────────────────────────────────────────
    if rsi_comp is not None:
        ax_rsi = axes[panel_idx]
        panel_idx += 1
        rsi_vals = rsi_comp.reindex(df.index).values

        ax_rsi.plot(xs, rsi_vals, color=_RSI, linewidth=1.2)
        ax_rsi.axhline(70, color=_DOWN, linewidth=0.7, linestyle="--", alpha=0.7)
        ax_rsi.axhline(30, color=_UP,   linewidth=0.7, linestyle="--", alpha=0.7)
        ax_rsi.axhline(50, color=_GRAY, linewidth=0.5, linestyle=":",  alpha=0.5)
        ax_rsi.fill_between(xs, rsi_vals, 70,
                            where=[v > 70 for v in rsi_vals], alpha=0.15, color=_DOWN)
        ax_rsi.fill_between(xs, rsi_vals, 30,
                            where=[v < 30 for v in rsi_vals], alpha=0.15, color=_UP)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.set_ylabel("RSI Comp\n(i59)", color=_GRAY, fontsize=7)
        last_rsi = rsi_vals[~np.isnan(rsi_vals)]
        if len(last_rsi):
            ax_rsi.text(n - 1, last_rsi[-1], f"{last_rsi[-1]:.0f}",
                        color=_RSI, fontsize=8, va="center")

    # ── Frequency Analyzer ───────────────────────────────────────────────────
    if freq is not None:
        ax_freq = axes[panel_idx]
        freq_vals = freq.reindex(df.index).values
        colors = [_FREQ_P if (not np.isnan(v) and v >= 0) else _FREQ_N for v in freq_vals]
        ax_freq.bar(xs, np.nan_to_num(freq_vals), color=colors, width=0.6, alpha=0.8)
        ax_freq.axhline(2.0,  color="#ffeb3b", linewidth=0.7, linestyle="--", alpha=0.8)
        ax_freq.axhline(0,    color=_GRAY,     linewidth=0.5)
        ax_freq.set_ylabel("Freq\n(i106)", color=_GRAY, fontsize=7)

    # ── X-axis dates ─────────────────────────────────────────────────────────
    bot_ax = axes[-1]
    step = max(1, n // 8)
    ticks = list(range(0, n, step))
    labels = [df.index[i].strftime("%d/%m") for i in ticks if i < n]
    bot_ax.set_xticks(ticks[: len(labels)])
    bot_ax.set_xticklabels(labels, color=_GRAY, fontsize=7)

    for ax in axes[:-1]:
        ax.set_xticklabels([])

    plt.tight_layout(pad=0.4)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=_DARK, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def format_fcaak_analysis(ticker: str, analysis: dict) -> str:
    """Format FCAAK analysis as a WhatsApp-friendly text message."""
    if "error" in analysis:
        return f"❌ {analysis['error']}"

    price  = analysis.get("price", 0)
    rsi    = analysis.get("rsi_composite")
    div    = analysis.get("bullish_divergence", False)
    spike  = analysis.get("volume_spike", False)
    no_ll  = analysis.get("no_new_ll", False)
    fib_lv = analysis.get("fib_level", "—")
    fib_rng = analysis.get("fib_range", {})

    rsi_emoji = "🟢" if rsi and rsi < 30 else "🟡" if rsi and rsi < 50 else "🔴"
    rsi_line  = f"{rsi_emoji} RSI Composite: {rsi:.1f}" if rsi is not None else "RSI: —"

    lines = [
        f"📊 *FCAAK | {ticker.upper()}*",
        f"💰 Harga: {price:,.0f}",
        rsi_line,
        f"📐 Fib Level: {fib_lv}  "
        f"(Low {fib_rng.get('low', 0):,.0f} — High {fib_rng.get('high', 0):,.0f})",
        "",
        "*Sinyal:*",
        f"{'✅' if div   else '❌'} Bullish Divergence",
        f"{'⚡' if spike else '⬜'} Volume Spike",
        f"{'✅' if no_ll else '❌'} Tidak ada LL baru",
        "",
    ]

    if div and spike and no_ll:
        lines.append("🔥 *Setup FCAAK kuat* — Divergence + Spike + No LL")
    elif div and not spike:
        lines.append("👀 Divergence ada, *tunggu spike*")
        lines.append("Cek TF kecil: /mfqhis " + ticker.upper())
    elif spike and not div:
        lines.append("⚡ Spike ada, *tunggu divergence*")
    else:
        lines.append("⏳ Setup belum terbentuk — sabar")

    return "\n".join(lines)


# ── /mfqhis & /fq commands ───────────────────────────────────────────────────

def get_mfqhis_analysis(ticker: str) -> str:
    """Multi-frequency history — check spike across multiple timeframes."""
    timeframes = [
        ("15m", "5d",  "15 Menit"),
        ("60m", "1mo", "60 Menit"),
        ("1d",  "3mo", "Harian"),
    ]

    rows = []
    for interval, period, label in timeframes:
        df = fetch_ohlcv(ticker, period=period, interval=interval)
        if df.empty or len(df) < 10:
            rows.append(f"*{label}*: data kosong")
            continue
        rsi  = calculate_rsi_composite(df)
        freq = calculate_frequency(df)
        spike = bool(freq.tail(5).max() >= 2.0)
        cur_rsi = float(rsi.iloc[-1]) if not rsi.empty else None
        rsi_str = f"RSI {cur_rsi:.0f}" if cur_rsi else "—"
        rows.append(f"*{label}*: {rsi_str}" + ("  ⚡ SPIKE" if spike else ""))

    header = f"📊 *Multi-Freq History: {ticker.upper()}*\n"
    return header + "\n".join(rows) if rows else f"❌ Data tidak tersedia untuk {ticker.upper()}"


def get_fq_analysis(ticker: str, months: int = 0) -> str:
    """Frequency analysis — single timeframe, with optional projection."""
    period = f"{months}mo" if months > 0 else "6mo"
    df = fetch_ohlcv(ticker, period=period)
    if df.empty:
        return f"❌ Data tidak tersedia untuk {ticker.upper()}"

    freq = calculate_frequency(df)
    rsi  = calculate_rsi_composite(df)
    cur_freq = float(freq.iloc[-1])
    cur_rsi  = float(rsi.iloc[-1])
    max_freq = float(freq.tail(20).max())

    lines = [
        f"📊 *Frequency Analysis: {ticker.upper()}*",
        f"{'📅 Periode: ' + str(months) + ' bulan' if months else ''}",
        "",
        f"⚡ Freq saat ini: {cur_freq:.2f}σ",
        f"📈 Max freq (20 bar): {max_freq:.2f}σ",
        f"RSI Composite: {cur_rsi:.1f}",
        "",
        "🔥 SPIKE terdeteksi!" if cur_freq >= 2.0 else "⬜ Belum ada spike",
    ]

    if months > 0:
        fib   = calculate_hl_fibonacci(df)
        price = float(df["Close"].iloc[-1])
        tgt_618 = fib["levels"]["0.618"]
        tgt_1   = fib["levels"]["1"]
        pot     = (tgt_618 - price) / price * 100

        lines += [
            "",
            f"🎯 *Proyeksi {months} bulan:*",
            f"Target Fib 0.618 : {tgt_618:,.0f}",
            f"Target High       : {tgt_1:,.0f}",
            f"Potensi upside    : {pot:.1f}%",
        ]

    return "\n".join(l for l in lines if l is not None)

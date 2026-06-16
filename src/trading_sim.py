"""
Simulasi trading Momentum Dip — modal Rp 10 juta.
Jalan tiap hari kerja 09:00 WIB (jam buka BEI).

Aturan portofolio:
  - Modal awal   : Rp 10.000.000
  - Max posisi   : 3 saham sekaligus
  - Ukuran posisi: 30% modal per saham (Rp 3 juta)
  - Min lot      : 1 lot = 100 lembar (standar BEI)

Entry (beli):
  - Momentum Dip score >= 55/100
  - Kas cukup untuk minimal 1 lot
  - Belum punya posisi di ticker tersebut

Exit (jual) — salah satu terpenuhi:
  1. Stop Loss   : harga < EMA200 × 0.97 (−3%)
  2. Take Profit : RSI > 65  ATAU  harga kembali ke EMA50
  3. Max Hold    : 15 hari trading (3 minggu)

Benchmark: IHSG (^JKSE) untuk cek apakah beat market.
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import Optional

import yfinance as yf
import pandas as pd

from src.stock_screener import run_screen, _ema, _rsi

# ─── Konstanta ────────────────────────────────────────────────────────────────

PORTFOLIO_FILE   = "data/portfolio_sim.json"
INITIAL_CAPITAL  = 10_000_000
MAX_POSITIONS    = 3
POSITION_PCT     = 0.30          # 30% kapital per posisi
MIN_ENTRY_SCORE  = 55
MAX_HOLD_DAYS    = 15
SL_BUFFER        = 0.03          # stop loss 3% di bawah EMA200
LOT_SIZE         = 100           # 1 lot = 100 lembar BEI
COMMISSION_PCT   = 0.0015        # biaya transaksi 0.15% per sisi (realistis)


# ─── State Portofolio ─────────────────────────────────────────────────────────

def _load_portfolio() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {
        "cash": INITIAL_CAPITAL,
        "positions": {},          # ticker -> {lots, buy_price, buy_date, score, ema200_at_buy}
        "closed_trades": [],
        "initial_capital": INITIAL_CAPITAL,
        "created_at": datetime.now().isoformat(),
        "benchmark_start": None,  # harga IHSG saat mulai
    }


def _save_portfolio(p: dict):
    os.makedirs("data", exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(p, f, indent=2, ensure_ascii=False)


# ─── Data Harga Real-time ─────────────────────────────────────────────────────

def _fetch_hist(ticker: str, days: int = 420) -> Optional[pd.DataFrame]:
    try:
        t    = yf.Ticker(ticker)
        end  = datetime.now()
        start = end - timedelta(days=days)
        hist = t.history(start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"),
                         auto_adjust=True)
        if hist.empty or len(hist) < 50:
            return None
        return hist
    except Exception:
        return None


def _current_price(ticker: str) -> Optional[float]:
    hist = _fetch_hist(ticker, days=10)
    if hist is None:
        return None
    return float(hist["Close"].iloc[-1])


def _ihsg_price() -> Optional[float]:
    return _current_price("^JKSE")


# ─── Logika Exit ──────────────────────────────────────────────────────────────

def _check_exit(position: dict, hist: pd.DataFrame) -> tuple[bool, str]:
    """
    Return (harus_jual, alasan).
    """
    closes  = hist["Close"].squeeze()
    price   = float(closes.iloc[-1])
    ema200  = float(_ema(closes, 200).iloc[-1])
    ema50   = float(_ema(closes, 50).iloc[-1])
    rsi_val = _rsi(closes)

    buy_date = date.fromisoformat(position["buy_date"])
    trading_days_held = (date.today() - buy_date).days * 5 // 7  # estimasi hari trading

    # 1. Stop Loss
    sl_level = ema200 * (1 - SL_BUFFER)
    if price < sl_level:
        return True, f"🔴 STOP LOSS — harga Rp{price:,.0f} < SL Rp{sl_level:,.0f}"

    # 2. Take Profit: RSI tinggi = saham sudah rebound kuat
    if rsi_val > 65:
        return True, f"🟢 TAKE PROFIT (RSI) — RSI {rsi_val:.1f} > 65, saham sudah rebound"

    # 3. Take Profit: harga kembali ke EMA50 (target awal pullback selesai)
    if price >= ema50 * 0.99:
        return True, f"🟢 TAKE PROFIT (EMA50) — harga Rp{price:,.0f} ≥ EMA50 Rp{ema50:,.0f}"

    # 4. Max hold 15 hari trading
    if trading_days_held >= MAX_HOLD_DAYS:
        pnl_pct = (price - position["buy_price"]) / position["buy_price"] * 100
        action  = "🟢 PROFIT" if pnl_pct > 0 else "🔴 RUGI"
        return True, f"⏰ MAX HOLD tercapai ({MAX_HOLD_DAYS} hari) — {action} {pnl_pct:+.1f}%"

    return False, ""


# ─── Kalkulasi PnL ───────────────────────────────────────────────────────────

def _calc_pnl(position: dict, sell_price: float) -> dict:
    lots       = position["lots"]
    shares     = lots * LOT_SIZE
    buy_price  = position["buy_price"]
    buy_value  = buy_price * shares
    sell_value = sell_price * shares

    buy_cost   = buy_value * COMMISSION_PCT
    sell_cost  = sell_value * COMMISSION_PCT
    net_pnl    = (sell_value - sell_cost) - (buy_value + buy_cost)
    pnl_pct    = net_pnl / (buy_value + buy_cost) * 100
    return_val = sell_value - sell_cost  # uang kembali ke kas

    return {
        "lots":         lots,
        "shares":       shares,
        "buy_price":    buy_price,
        "sell_price":   sell_price,
        "buy_value":    round(buy_value),
        "sell_value":   round(sell_value),
        "net_pnl":      round(net_pnl),
        "pnl_pct":      round(pnl_pct, 2),
        "return_val":   round(return_val),
        "commission":   round(buy_cost + sell_cost),
    }


# ─── Main: Eksekusi Harian ───────────────────────────────────────────────────

def run_daily_trading() -> dict:
    """
    Dipanggil tiap hari kerja jam 09:00 WIB.
    1. Periksa posisi existing → jual jika exit terpenuhi
    2. Screen saham baru → beli jika ada slot & skor tinggi
    3. Hitung nilai portofolio terkini
    4. Return summary untuk WhatsApp
    """
    portfolio = _load_portfolio()
    today     = date.today().isoformat()
    now_str   = datetime.now().strftime("%d %b %Y %H:%M")

    sells  = []
    buys   = []
    errors = []

    # ── Inisialisasi benchmark IHSG ──────────────────────────────────────────
    if portfolio.get("benchmark_start") is None:
        ihsg = _ihsg_price()
        if ihsg:
            portfolio["benchmark_start"] = ihsg
            portfolio["benchmark_start_date"] = today

    # ── FASE 1: Periksa exit posisi yang ada ─────────────────────────────────
    tickers_to_sell = []
    for ticker, pos in list(portfolio["positions"].items()):
        hist = _fetch_hist(ticker)
        if hist is None:
            errors.append(f"⚠️ Gagal ambil data {ticker}")
            continue

        current = float(hist["Close"].iloc[-1])
        should_exit, reason = _check_exit(pos, hist)

        if should_exit:
            pnl = _calc_pnl(pos, current)
            trade_record = {
                "ticker":     ticker,
                "buy_date":   pos["buy_date"],
                "sell_date":  today,
                "reason":     reason,
                **pnl,
            }
            portfolio["cash"] += pnl["return_val"]
            portfolio["closed_trades"].append(trade_record)
            tickers_to_sell.append(ticker)
            sells.append(trade_record)

    for t in tickers_to_sell:
        del portfolio["positions"][t]

    # ── FASE 2: Screen saham baru & beli ─────────────────────────────────────
    slots_available = MAX_POSITIONS - len(portfolio["positions"])

    if slots_available > 0:
        screen_results = run_screen()
        candidates     = screen_results.get("momentum_dip", [])

        # Urutkan: skor tertinggi dulu
        candidates.sort(key=lambda x: x["score"], reverse=True)

        for c in candidates:
            if slots_available <= 0:
                break
            ticker = c["ticker"]
            if ticker in portfolio["positions"]:
                continue  # sudah punya

            score = c["score"]
            if score < MIN_ENTRY_SCORE:
                continue

            current = _current_price(ticker)
            if current is None or current <= 0:
                continue

            # Hitung jumlah lot yang bisa dibeli
            budget    = portfolio["cash"] * POSITION_PCT
            buy_value = budget
            shares    = int(buy_value / current)
            lots      = shares // LOT_SIZE  # bulatkan ke bawah ke lot terdekat
            if lots < 1:
                errors.append(f"⚠️ {ticker}: kas tidak cukup untuk 1 lot (butuh Rp{current*LOT_SIZE:,.0f})")
                continue

            actual_shares = lots * LOT_SIZE
            actual_cost   = actual_shares * current * (1 + COMMISSION_PCT)

            if actual_cost > portfolio["cash"]:
                lots -= 1
                if lots < 1:
                    continue
                actual_shares = lots * LOT_SIZE
                actual_cost   = actual_shares * current * (1 + COMMISSION_PCT)

            # Ambil EMA200 untuk stop loss reference
            hist = _fetch_hist(ticker)
            ema200_val = 0.0
            ema50_val  = 0.0
            if hist is not None:
                closes = hist["Close"].squeeze()
                ema200_val = float(_ema(closes, 200).iloc[-1])
                ema50_val  = float(_ema(closes, 50).iloc[-1])

            portfolio["cash"] -= actual_cost
            portfolio["positions"][ticker] = {
                "lots":            lots,
                "buy_price":       current,
                "buy_date":        today,
                "buy_score":       score,
                "ema200_at_buy":   round(ema200_val, 0),
                "ema50_at_buy":    round(ema50_val, 0),
                "pullback_pct":    c.get("pullback_pct", 0),
                "momentum_3m":     c.get("momentum_3m", 0),
                "target_pct":      c.get("target_pct", 0),
            }

            buys.append({
                "ticker":       ticker,
                "name":         c.get("name", ticker)[:25],
                "lots":         lots,
                "shares":       actual_shares,
                "buy_price":    current,
                "buy_value":    round(actual_cost),
                "score":        score,
                "rsi":          c.get("rsi", 0),
                "pullback_pct": c.get("pullback_pct", 0),
                "ema200":       round(ema200_val, 0),
                "sl_level":     round(ema200_val * (1 - SL_BUFFER), 0),
                "target_pct":   c.get("target_pct", 0),
            })
            slots_available -= 1

    # ── FASE 3: Hitung nilai portofolio ──────────────────────────────────────
    positions_value = 0.0
    positions_detail = []
    for ticker, pos in portfolio["positions"].items():
        current = _current_price(ticker)
        if current is None:
            current = pos["buy_price"]
        shares      = pos["lots"] * LOT_SIZE
        value       = shares * current
        unrealized  = (current - pos["buy_price"]) / pos["buy_price"] * 100
        positions_value += value
        positions_detail.append({
            "ticker":     ticker,
            "lots":       pos["lots"],
            "buy_price":  pos["buy_price"],
            "current":    current,
            "value":      round(value),
            "unrealized": round(unrealized, 2),
            "days_held":  (date.today() - date.fromisoformat(pos["buy_date"])).days,
        })

    total_value = portfolio["cash"] + positions_value

    # ── Hitung IHSG benchmark ─────────────────────────────────────────────────
    ihsg_now   = _ihsg_price() or 0
    ihsg_start = portfolio.get("benchmark_start") or ihsg_now
    ihsg_return = (ihsg_now - ihsg_start) / ihsg_start * 100 if ihsg_start > 0 else 0

    # Return portofolio
    port_return = (total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    # Total closed PnL
    total_realized = sum(t.get("net_pnl", 0) for t in portfolio["closed_trades"])
    win_trades  = [t for t in portfolio["closed_trades"] if t.get("net_pnl", 0) > 0]
    lose_trades = [t for t in portfolio["closed_trades"] if t.get("net_pnl", 0) <= 0]
    win_rate    = len(win_trades) / len(portfolio["closed_trades"]) * 100 if portfolio["closed_trades"] else 0

    # Simpan state
    _save_portfolio(portfolio)

    return {
        "timestamp":         now_str,
        "today":             today,
        "cash":              round(portfolio["cash"]),
        "positions_value":   round(positions_value),
        "total_value":       round(total_value),
        "port_return_pct":   round(port_return, 2),
        "ihsg_return_pct":   round(ihsg_return, 2),
        "alpha":             round(port_return - ihsg_return, 2),
        "sells":             sells,
        "buys":              buys,
        "positions_detail":  positions_detail,
        "total_realized":    round(total_realized),
        "win_rate":          round(win_rate, 1),
        "n_wins":            len(win_trades),
        "n_losses":          len(lose_trades),
        "errors":            errors,
    }


# ─── Formatter WhatsApp ───────────────────────────────────────────────────────

def format_trading_report(r: dict) -> str:
    port_emoji  = "📈" if r["port_return_pct"] >= 0 else "📉"
    alpha_emoji = "✅" if r["alpha"] >= 0 else "⚠️"

    lines = [
        f"🤖 *SIM Trading Momentum Dip — {r['timestamp']}*",
        f"_Modal awal: Rp10.000.000_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "💼 *STATUS PORTOFOLIO*",
        f"   💰 Kas       : Rp{r['cash']:>12,.0f}",
        f"   📊 Posisi    : Rp{r['positions_value']:>12,.0f}",
        f"   🏦 Total     : Rp{r['total_value']:>12,.0f}",
        f"   {port_emoji} Return    : {r['port_return_pct']:+.2f}%",
        f"   📉 IHSG      : {r['ihsg_return_pct']:+.2f}%",
        f"   {alpha_emoji} Alpha     : {r['alpha']:+.2f}% vs pasar",
        "",
    ]

    if r.get("sells"):
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🔁 *TRANSAKSI JUAL HARI INI*")
        for s in r["sells"]:
            emoji = "🟢" if s["net_pnl"] > 0 else "🔴"
            lines += [
                f"{emoji} *{s['ticker'].replace('.JK','')}* — {s['lots']} lot",
                f"   Beli: Rp{s['buy_price']:,.0f} → Jual: Rp{s['sell_price']:,.0f}",
                f"   PnL: Rp{s['net_pnl']:+,.0f} ({s['pnl_pct']:+.2f}%)",
                f"   _{s['reason']}_",
                "",
            ]

    if r.get("buys"):
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🛒 *TRANSAKSI BELI HARI INI*")
        for b in r["buys"]:
            lines += [
                f"🟦 *{b['ticker'].replace('.JK','')}* — {b['lots']} lot ({b['shares']} lbr)",
                f"   Harga: Rp{b['buy_price']:,.0f} | Nilai: Rp{b['buy_value']:,.0f}",
                f"   Skor: {b['score']}/100 | RSI: {b['rsi']} | Pullback: -{b['pullback_pct']}%",
                f"   🛡️ Stop Loss: Rp{b['sl_level']:,.0f} (EMA200-3%)",
                f"   🎯 Target: +{b['target_pct']}% (EMA50)",
                "",
            ]
    elif not r.get("sells"):
        lines += ["", "💤 *Tidak ada transaksi hari ini*", "_Tidak ada setup yang memenuhi kriteria._", ""]

    if r.get("positions_detail"):
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("📂 *POSISI TERBUKA*")
        for p in r["positions_detail"]:
            u_emoji = "🟢" if p["unrealized"] >= 0 else "🔴"
            lines += [
                f"{u_emoji} *{p['ticker'].replace('.JK','')}* — {p['lots']} lot",
                f"   Beli: Rp{p['buy_price']:,.0f} | Skrg: Rp{p['current']:,.0f}",
                f"   Unrealized: {p['unrealized']:+.2f}% | Hold: {p['days_held']} hari",
                "",
            ]

    if r["total_realized"] != 0 or r["win_rate"] > 0:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━",
            "📊 *STATISTIK KESELURUHAN*",
            f"   Realized PnL : Rp{r['total_realized']:+,.0f}",
            f"   Win rate     : {r['win_rate']:.0f}% ({r['n_wins']}W / {r['n_losses']}L)",
            "",
        ]

    if r.get("errors"):
        lines += ["⚠️ " + e for e in r["errors"]]

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ _Ini simulasi. Bukan eksekusi nyata._",
        "_SL = stop loss otomatis. TP = take profit otomatis._",
    ]

    return "\n".join(lines)


# ─── Reset Simulasi ───────────────────────────────────────────────────────────

def reset_simulation():
    """Reset portfolio ke kondisi awal Rp10 juta."""
    if os.path.exists(PORTFOLIO_FILE):
        os.remove(PORTFOLIO_FILE)
    p = _load_portfolio()
    _save_portfolio(p)
    return "✅ Simulasi trading di-reset. Modal: Rp10.000.000"

"""
Screener saham IDX otomatis dengan 3 metode gabungan:
  1. Buy on Weakness (BoW) — sinyal teknikal oversold
  2. Piotroski F-Score    — kualitas fundamental (0-9)
  3. Magic Formula        — value + return on capital (Greenblatt)

Skor gabungan: BoW 40% + Piotroski 40% + Magic Formula 20%
Filter awal: Piotroski >= 5 (buang fundamental buruk)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Watchlist saham IDX: blue chip + mid cap populer
IDX_WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ICBP.JK", "KLBF.JK", "INDF.JK", "SIDO.JK",
    "MYOR.JK", "CPIN.JK", "HMSP.JK", "INTP.JK", "SMGR.JK",
    "PTBA.JK", "ANTM.JK", "ADRO.JK", "ITMG.JK", "INCO.JK",
    "BTPS.JK", "BRIS.JK", "ACES.JK", "MAPI.JK", "ERAA.JK",
    "JPFA.JK", "CUAN.JK", "BREN.JK", "EMTK.JK", "DCII.JK",
    "BBNI.JK", "BNGA.JK", "MDKA.JK", "GOTO.JK", "HEAL.JK",
]


# ─── Indikator Teknikal (implementasi manual, tanpa library ta) ───────────────

def _rsi(closes: pd.Series, period: int = 14) -> float:
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("inf"))
    rsi = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1])


def _stochastic_k(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    lowest_low = low.rolling(period).min()
    highest_high = high.rolling(period).max()
    denom = highest_high - lowest_low
    k = 100 * (close - lowest_low) / denom.replace(0, float("nan"))
    return float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50.0


def _sma(series: pd.Series, period: int) -> float:
    return float(series.rolling(period).mean().iloc[-1])


# ─── Buy on Weakness Score (0-100) ────────────────────────────────────────────

def _bow_score(hist: pd.DataFrame) -> dict:
    """
    Hitung skor Buy on Weakness.
    Makin tinggi = makin oversold TAPI masih di uptrend jangka panjang.
    """
    if len(hist) < 200:
        return {"score": 0, "signals": [], "rsi": 50, "stoch_k": 50,
                "drawdown_pct": 0, "ma50": 0, "ma200": 0, "price": 0}

    closes = hist["Close"].squeeze()
    high   = hist["High"].squeeze()
    low    = hist["Low"].squeeze()
    volume = hist["Volume"].squeeze()

    price  = float(closes.iloc[-1])
    ma20   = _sma(closes, 20)
    ma50   = _sma(closes, 50)
    ma200  = _sma(closes, 200)
    rsi    = _rsi(closes)
    stoch  = _stochastic_k(high, low, closes)

    score   = 0
    signals = []

    # RSI oversold
    if rsi < 25:
        score += 30
        signals.append(f"RSI sangat oversold ({rsi:.1f})")
    elif rsi < 30:
        score += 25
        signals.append(f"RSI oversold ({rsi:.1f})")
    elif rsi < 35:
        score += 15
        signals.append(f"RSI mendekati oversold ({rsi:.1f})")

    # Stochastic oversold
    if stoch < 20:
        score += 20
        signals.append(f"Stochastic oversold (K={stoch:.1f})")
    elif stoch < 30:
        score += 10
        signals.append(f"Stochastic lemah (K={stoch:.1f})")

    # Masih di atas MA200 = downtrend jangka panjang belum terjadi
    if price > ma200:
        score += 20
        signals.append("Di atas MA200 (tren panjang aman)")
    elif price > ma200 * 0.95:
        score += 8
        signals.append("Mendekati MA200 (perhatikan)")

    # Koreksi sementara: harga di bawah MA20 & MA50
    if price < ma20 and price < ma50:
        score += 15
        signals.append("Koreksi di bawah MA20 & MA50")
    elif price < ma20:
        score += 7
        signals.append("Koreksi di bawah MA20")

    # Volume spike = selling exhaustion / capitulation
    avg_vol = float(volume.rolling(20).mean().iloc[-1])
    last_vol = float(volume.iloc[-1])
    if avg_vol > 0 and last_vol > 1.5 * avg_vol:
        score += 15
        signals.append(f"Volume spike ({last_vol/avg_vol:.1f}x rata-rata)")

    # Drawdown dari 52-week high
    high_52w = float(closes.rolling(252).max().iloc[-1])
    drawdown = (high_52w - price) / high_52w * 100 if high_52w > 0 else 0
    if drawdown > 20:
        score += 10
        signals.append(f"Koreksi {drawdown:.0f}% dari puncak")
    elif drawdown > 10:
        score += 5
        signals.append(f"Koreksi {drawdown:.0f}% dari puncak")

    return {
        "score": min(score, 100),
        "signals": signals,
        "rsi": round(rsi, 1),
        "stoch_k": round(stoch, 1),
        "price": price,
        "ma50": round(ma50, 0),
        "ma200": round(ma200, 0),
        "drawdown_pct": round(drawdown, 1),
    }


# ─── Piotroski F-Score (0-9) ──────────────────────────────────────────────────

def _piotroski(info: dict) -> dict:
    """
    9 kriteria fundamental Piotroski:
    Profitabilitas (4) + Likuiditas/Leverage (3) + Efisiensi (2)
    """
    score = 0
    details = []

    # --- Profitabilitas ---
    roa = info.get("returnOnAssets") or 0
    if roa > 0:
        score += 1
        details.append(f"✅ ROA positif ({roa*100:.1f}%)")
    else:
        details.append(f"❌ ROA negatif ({roa*100:.1f}%)")

    ocf = info.get("operatingCashflow") or 0
    if ocf > 0:
        score += 1
        details.append("✅ Operating cash flow positif")
    else:
        details.append("❌ Operating cash flow negatif")

    roe = info.get("returnOnEquity") or 0
    if roe > 0.10:
        score += 1
        details.append(f"✅ ROE {roe*100:.1f}%")
    else:
        details.append(f"❌ ROE rendah ({roe*100:.1f}%)")

    total_assets = info.get("totalAssets") or 0
    accrual = (ocf / total_assets) if total_assets > 0 else 0
    if accrual > roa:
        score += 1
        details.append("✅ Cash earnings > Akuntansi earnings")
    else:
        details.append("❌ Akrual tinggi (earnings kurang berkualitas)")

    # --- Leverage & Likuiditas ---
    current_ratio = info.get("currentRatio") or 0
    if current_ratio > 1.0:
        score += 1
        details.append(f"✅ Current ratio {current_ratio:.1f}x")
    else:
        details.append(f"❌ Current ratio {current_ratio:.1f}x")

    de = info.get("debtToEquity") or 999
    if de < 150:
        score += 1
        details.append(f"✅ D/E ratio {de/100:.2f}x")
    else:
        details.append(f"❌ D/E tinggi ({de/100:.2f}x)")

    gross_margin = info.get("grossMargins") or 0
    if gross_margin > 0.15:
        score += 1
        details.append(f"✅ Gross margin {gross_margin*100:.1f}%")
    else:
        details.append(f"❌ Gross margin tipis ({gross_margin*100:.1f}%)")

    # --- Efisiensi Operasional ---
    rev_growth = info.get("revenueGrowth") or 0
    if rev_growth > 0:
        score += 1
        details.append(f"✅ Revenue tumbuh {rev_growth*100:.1f}%")
    else:
        details.append(f"❌ Revenue turun ({rev_growth*100:.1f}%)")

    net_margin = info.get("profitMargins") or 0
    if net_margin > 0.05:
        score += 1
        details.append(f"✅ Net margin {net_margin*100:.1f}%")
    else:
        details.append(f"❌ Net margin tipis ({net_margin*100:.1f}%)")

    return {"score": score, "details": details}


# ─── Magic Formula Metrics ────────────────────────────────────────────────────

def _magic_formula(info: dict) -> dict:
    """
    Greenblatt Magic Formula:
    - Earnings Yield = EBIT / Enterprise Value (makin tinggi makin murah)
    - Return on Capital = EBIT / Capital Employed
    """
    ebit        = info.get("ebitda") or 0
    market_cap  = info.get("marketCap") or 0
    total_debt  = info.get("totalDebt") or 0
    cash        = info.get("totalCash") or 0
    total_assets = info.get("totalAssets") or 0
    cur_liab    = info.get("totalCurrentLiabilities") or 0

    ev = market_cap + total_debt - cash
    earnings_yield = (ebit / ev * 100) if ev > 0 else 0

    capital_employed = total_assets - cur_liab
    roc = (ebit / capital_employed * 100) if capital_employed > 0 else 0

    pe = info.get("trailingPE") or 0
    pbv = info.get("priceToBook") or 0

    return {
        "earnings_yield": round(earnings_yield, 1),
        "roc": round(roc, 1),
        "pe": round(pe, 1),
        "pbv": round(pbv, 1),
    }


# ─── Main Screener ────────────────────────────────────────────────────────────

def run_screen(watchlist: list[str] | None = None) -> list[dict]:
    """
    Jalankan screening lengkap pada watchlist IDX.
    Return top-10 saham berdasarkan skor gabungan.
    """
    tickers = watchlist or IDX_WATCHLIST
    results = []

    end_date   = datetime.now()
    start_date = end_date - timedelta(days=400)

    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                auto_adjust=True,
            )
            if hist.empty or len(hist) < 50:
                continue

            info = t.info or {}

            bow  = _bow_score(hist)
            piof = _piotroski(info)
            mf   = _magic_formula(info)

            # Normalisasi ke 0-100
            piof_norm = piof["score"] / 9 * 100
            # Earnings yield 30%+ = skor penuh
            mf_norm = min(mf["earnings_yield"] * 3.33, 100) if mf["earnings_yield"] > 0 else 0

            combined = (
                bow["score"]  * 0.40 +
                piof_norm     * 0.40 +
                mf_norm       * 0.20
            )

            # Filter: buang saham fundamental buruk (Piotroski < 5)
            if piof["score"] < 5:
                continue

            # Filter: harus ada sinyal teknikal BoW minimal satu
            if bow["score"] < 10:
                continue

            name = info.get("longName") or info.get("shortName") or ticker
            results.append({
                "ticker":           ticker,
                "name":             name,
                "price":            bow["price"],
                "combined_score":   round(combined, 1),
                "bow_score":        bow["score"],
                "piotroski":        piof["score"],
                "piotroski_detail": piof["details"],
                "mf_ey":            mf["earnings_yield"],
                "mf_roc":           mf["roc"],
                "pe":               mf["pe"],
                "pbv":              mf["pbv"],
                "rsi":              bow["rsi"],
                "stoch_k":          bow["stoch_k"],
                "ma50":             bow["ma50"],
                "ma200":            bow["ma200"],
                "drawdown_pct":     bow["drawdown_pct"],
                "bow_signals":      bow["signals"],
            })

        except Exception as e:
            print(f"[Screener] Skip {ticker}: {e}")

    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results[:10]


# ─── Formatter WhatsApp ───────────────────────────────────────────────────────

def format_screen_report(results: list[dict]) -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")

    if not results:
        return (
            f"📊 *Screener Saham IDX — {now}*\n\n"
            "⚠️ Tidak ada kandidat yang memenuhi kriteria hari ini.\n"
            "_Coba lagi besok atau cek kondisi pasar._"
        )

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    lines = [
        f"📊 *Screener Saham IDX — {now}*",
        "_Metode: Buy on Weakness + Piotroski F-Score + Magic Formula_",
        "",
        "🎯 *Top Kandidat Buy on Weakness:*",
    ]

    for i, r in enumerate(results[:5]):
        m = medals[i] if i < len(medals) else f"{i+1}."
        ticker_short = r["ticker"].replace(".JK", "")
        nama = r["name"][:28] if len(r["name"]) > 28 else r["name"]
        signals_str = " | ".join(r["bow_signals"][:2]) if r["bow_signals"] else "-"

        lines += [
            "",
            f"{m} *{ticker_short}* — _{nama}_",
            f"   💰 Rp{r['price']:,.0f}  |  PE: {r['pe']}x  |  PBV: {r['pbv']}x",
            f"   🏆 Skor: {r['combined_score']}/100  (BoW:{r['bow_score']} | F:{r['piotroski']}/9 | EY:{r['mf_ey']}%)",
            f"   📉 RSI: {r['rsi']} | Stoch: {r['stoch_k']} | Koreksi: -{r['drawdown_pct']}%",
            f"   ✅ _{signals_str}_",
        ]

    lines += [
        "",
        "─────────────────────────",
        "📌 *Cara Pakai BoW:*",
        "  • Entry bertahap saat sinyal muncul",
        "  • Stop loss: di bawah MA200",
        "  • Target: kembali ke MA50 (10-20% upside)",
        "",
        "⚠️ _Bukan rekomendasi investasi. Selalu DYOR._",
    ]

    return "\n".join(lines)


def format_detail_report(result: dict) -> str:
    """Format detail satu saham untuk analisis mendalam."""
    ticker_short = result["ticker"].replace(".JK", "")
    lines = [
        f"🔍 *Analisis Detail: {ticker_short}*",
        f"_{result['name']}_",
        "",
        "*📊 Piotroski F-Score:*",
    ]
    lines += [f"   {d}" for d in result["piotroski_detail"]]
    lines += [
        f"   → *Total: {result['piotroski']}/9*",
        "",
        "*📈 Magic Formula:*",
        f"   Earnings Yield: {result['mf_ey']}%",
        f"   Return on Capital: {result['mf_roc']}%",
        "",
        "*📉 Buy on Weakness:*",
        f"   RSI(14): {result['rsi']}",
        f"   Stochastic K: {result['stoch_k']}",
        f"   MA50: Rp{result['ma50']:,.0f}",
        f"   MA200: Rp{result['ma200']:,.0f}",
        f"   Drawdown dari puncak: -{result['drawdown_pct']}%",
    ]
    return "\n".join(lines)

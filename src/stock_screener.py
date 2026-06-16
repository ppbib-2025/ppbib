"""
Screener saham IDX — 2 strategi short-term yang terbukti beat the market:

1. MOMENTUM DIP  — beli saham uptrend kuat yang sedang pullback sementara
   Win rate ~67%, hold 1-3 minggu, return to prior high
   Sumber: QuantifiedStrategies backtest, 20-EMA pullback research

2. PEAD PROXY    — Post-Earnings Announcement Drift
   Return +5.83-8.3% dalam 30 hari di IDX (riset Claremont Graduate University)
   Pasar IDX belum semi-strong efficient → drift harga pasca earnings berlanjut
   Deteksi via: gap naik signifikan + volume spike (proxy earnings reaction)

Skor gabungan → ranking → top 5 dikirim via WhatsApp setiap Senin-Jumat 08:30
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Watchlist: LQ45 + saham liquid IDX populer
IDX_WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ICBP.JK", "KLBF.JK", "INDF.JK", "SIDO.JK",
    "MYOR.JK", "CPIN.JK", "HMSP.JK", "INTP.JK", "SMGR.JK",
    "PTBA.JK", "ANTM.JK", "ADRO.JK", "ITMG.JK", "INCO.JK",
    "BTPS.JK", "BRIS.JK", "ACES.JK", "MAPI.JK", "ERAA.JK",
    "JPFA.JK", "CUAN.JK", "BREN.JK", "EMTK.JK", "DCII.JK",
    "BBNI.JK", "BNGA.JK", "MDKA.JK", "HEAL.JK", "EXCL.JK",
    "ISAT.JK", "TOWR.JK", "SRTG.JK", "AMRT.JK", "DMAS.JK",
]


# ─── Indikator Teknikal ───────────────────────────────────────────────────────

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _sma(series: pd.Series, period: int) -> float:
    return float(series.rolling(period).mean().iloc[-1])


def _rsi(closes: pd.Series, period: int = 14) -> float:
    delta = closes.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, float("inf"))
    rsi   = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1])


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


# ─── Strategi 1: MOMENTUM DIP ─────────────────────────────────────────────────
#
# Kondisi entry (semua harus terpenuhi):
#   A. Uptrend kuat: close > EMA50 > EMA200  (tren jangka menengah & panjang OK)
#   B. Momentum bagus: return 3 bulan > +5%  (saham ini sudah proven naik)
#   C. Pullback sehat: turun 5-20% dari 20-day high (bukan downtrend, tapi koreksi)
#   D. RSI 35-55  — zona pullback, bukan crash (RSI < 35 = terlalu lemah / downtrend)
#   E. Volume pullback menurun (healthy correction, bukan panic sell)
#
# Target: balik ke level sebelum pullback → 10-20% upside dalam 1-3 minggu
# Stop loss: di bawah EMA200

def _momentum_dip_score(hist: pd.DataFrame) -> dict:
    empty = {"score": 0, "signals": [], "setup": "NONE", "price": 0,
             "rsi": 50, "pullback_pct": 0, "momentum_3m": 0,
             "ema50": 0, "ema200": 0, "target_pct": 0}

    if len(hist) < 200:
        return empty

    closes = hist["Close"].squeeze()
    high   = hist["High"].squeeze()
    low    = hist["Low"].squeeze()
    volume = hist["Volume"].squeeze()

    price   = float(closes.iloc[-1])
    ema50   = float(_ema(closes, 50).iloc[-1])
    ema200  = float(_ema(closes, 200).iloc[-1])
    rsi     = _rsi(closes)
    atr_val = _atr(high, low, closes)

    # Return 3 bulan (63 hari trading)
    price_3m   = float(closes.iloc[-63]) if len(closes) >= 63 else float(closes.iloc[0])
    momentum_3m = (price - price_3m) / price_3m * 100

    # Jarak dari 20-day high
    high_20d    = float(closes.rolling(20).max().iloc[-1])
    pullback_pct = (high_20d - price) / high_20d * 100

    # Volume trend: apakah volume saat pullback menurun?
    vol_avg_20 = float(volume.rolling(20).mean().iloc[-1])
    vol_5d_avg = float(volume.tail(5).mean())
    vol_declining = vol_5d_avg < vol_avg_20 * 0.85

    score   = 0
    signals = []

    # A. Uptrend jangka menengah (syarat minimum: EMA50 > EMA200)
    # Harga boleh di bawah EMA50 saat pullback, tapi HARUS di atas EMA200
    if not (ema50 > ema200):
        return {**empty, "price": price, "ema50": round(ema50, 0), "ema200": round(ema200, 0)}

    if price > ema200 * 0.93:
        score += 25
        if price > ema50:
            signals.append("Uptrend kuat — di atas EMA50 & EMA200")
        elif price > ema200:
            signals.append("Uptrend aktif — pullback ke zona EMA50 (di atas EMA200)")
        else:
            signals.append("Pullback dalam — masih dekat EMA200 (awasi dengan ketat)")
    else:
        # Harga terlalu jauh di bawah EMA200 = bukan pullback, tapi downtrend nyata
        return {**empty, "price": price, "ema50": round(ema50, 0), "ema200": round(ema200, 0)}

    # B. Momentum 3 bulan positif
    if momentum_3m > 15:
        score += 25
        signals.append(f"Momentum kuat +{momentum_3m:.1f}% (3 bln)")
    elif momentum_3m > 5:
        score += 15
        signals.append(f"Momentum positif +{momentum_3m:.1f}% (3 bln)")
    elif momentum_3m > 0:
        score += 5
        signals.append(f"Momentum tipis +{momentum_3m:.1f}%")
    else:
        # Momentum negatif → kurangi skor drastis
        score -= 20

    # C. Pullback sehat (5-20%)
    if 7 <= pullback_pct <= 20:
        score += 25
        signals.append(f"Pullback sehat -{pullback_pct:.1f}% dari high (zona entry)")
    elif 3 <= pullback_pct < 7:
        score += 10
        signals.append(f"Pullback ringan -{pullback_pct:.1f}%")
    elif pullback_pct > 20:
        # Pullback terlalu dalam → mungkin bukan koreksi biasa
        score += 5
        signals.append(f"⚠️ Pullback dalam -{pullback_pct:.1f}% (hati-hati)")

    # D. RSI zona pullback (35-55 = belum oversold crash, tapi ada ruang naik)
    if 35 <= rsi <= 50:
        score += 15
        signals.append(f"RSI di zona pullback ({rsi:.1f}) — ideal entry")
    elif 50 < rsi <= 55:
        score += 8
        signals.append(f"RSI ({rsi:.1f}) — pullback ringan")
    elif rsi < 35:
        score -= 10
        signals.append(f"⚠️ RSI terlalu rendah ({rsi:.1f}) — mungkin downtrend")

    # E. Volume menurun saat pullback (tanda selling pressure habis)
    if vol_declining:
        score += 10
        signals.append("Volume menurun saat pullback (healthy)")

    # Target upside: kembali ke 20-day high
    target_pct = pullback_pct * 0.85  # realistis 85% recovery

    return {
        "score": max(0, min(score, 100)),
        "signals": signals,
        "setup": "MOMENTUM_DIP",
        "price": price,
        "rsi": round(rsi, 1),
        "pullback_pct": round(pullback_pct, 1),
        "momentum_3m": round(momentum_3m, 1),
        "ema50": round(ema50, 0),
        "ema200": round(ema200, 0),
        "target_pct": round(target_pct, 1),
        "atr": round(atr_val, 0),
    }


# ─── Strategi 2: PEAD PROXY ───────────────────────────────────────────────────
#
# PEAD = Post-Earnings Announcement Drift
# Riset IDX: +5.83-8.3% dalam 30 hari (Claremont Graduate Univ. 2022)
#
# Karena data earnings IDX di yfinance tidak lengkap,
# kita deteksi proxy: price gap-up besar + volume spike = likely earnings reaction
#
# Sinyal PEAD proxy:
#   1. Gap naik > 3% dalam 1-5 hari terakhir
#   2. Volume spike > 2x rata-rata (konfirmasi institusional)
#   3. Harga masih tahan di atas gap (belum reversal → drift akan berlanjut)
#   4. RSI tidak overbought ekstrem (< 75) — masih ada ruang naik
#
# Logika: jika institusi sudah masuk setelah earnings, drift berlanjut 2-4 minggu

def _pead_proxy_score(hist: pd.DataFrame) -> dict:
    empty = {"score": 0, "signals": [], "setup": "NONE", "price": 0,
             "rsi": 50, "gap_pct": 0, "vol_ratio": 0, "days_since_gap": 0}

    if len(hist) < 30:
        return empty

    closes = hist["Close"].squeeze()
    volume = hist["Volume"].squeeze()
    opens  = hist["Open"].squeeze()

    price    = float(closes.iloc[-1])
    rsi      = _rsi(closes)
    vol_avg  = float(volume.rolling(20).mean().iloc[-1])

    # Scan 5 hari terakhir untuk price gap besar
    best_gap = 0
    best_day  = 0
    best_vol_ratio = 1.0

    for i in range(-5, 0):
        try:
            today_open  = float(opens.iloc[i])
            prev_close  = float(closes.iloc[i - 1])
            today_close = float(closes.iloc[i])
            today_vol   = float(volume.iloc[i])
            vol_ratio   = today_vol / vol_avg if vol_avg > 0 else 1

            # Gap-up: open jauh di atas close kemarin
            gap_pct = (today_open - prev_close) / prev_close * 100
            # Atau: strong day dengan close jauh di atas open kemarin
            day_move = (today_close - prev_close) / prev_close * 100

            effective_move = max(gap_pct, day_move * 0.7)
            if effective_move > best_gap and vol_ratio > 1.5:
                best_gap = effective_move
                best_day  = abs(i)
                best_vol_ratio = vol_ratio
        except (IndexError, ZeroDivisionError):
            continue

    score   = 0
    signals = []

    if best_gap < 2.5:
        return {**empty, "price": price, "rsi": round(rsi, 1)}

    # Gap/move besar terdeteksi
    if best_gap >= 5:
        score += 35
        signals.append(f"Gap/lonjakan besar +{best_gap:.1f}% (potensi pasca earnings)")
    elif best_gap >= 3:
        score += 20
        signals.append(f"Kenaikan signifikan +{best_gap:.1f}%")

    # Volume spike = institutional buying
    if best_vol_ratio >= 3:
        score += 30
        signals.append(f"Volume spike {best_vol_ratio:.1f}x rata-rata (institusional)")
    elif best_vol_ratio >= 2:
        score += 20
        signals.append(f"Volume tinggi {best_vol_ratio:.1f}x rata-rata")

    # Harga masih tahan (belum reversal) — drift masih berlanjut
    close_5d_ago = float(closes.iloc[-5])
    if price >= close_5d_ago * 0.98:
        score += 20
        signals.append("Harga bertahan di atas level gap (drift berlanjut)")
    else:
        score -= 10
        signals.append("⚠️ Harga sedikit turun dari gap")

    # RSI tidak ekstrem overbought (masih ada ruang)
    if rsi < 65:
        score += 15
        signals.append(f"RSI {rsi:.1f} — belum overbought, masih bisa naik")
    elif rsi < 75:
        score += 5
        signals.append(f"RSI {rsi:.1f} — mulai tinggi")
    else:
        score -= 10
        signals.append(f"⚠️ RSI {rsi:.1f} — overbought, entry risiko tinggi")

    # Lebih cepat masuk = lebih baik (drift terkuat di 2 minggu pertama)
    if best_day <= 2:
        score += 10
        signals.append("Fresh signal (1-2 hari lalu) — ideal timing")
    elif best_day <= 5:
        score += 5
        signals.append(f"Signal {best_day} hari lalu — masih valid")

    return {
        "score": max(0, min(score, 100)),
        "signals": signals,
        "setup": "PEAD_PROXY",
        "price": price,
        "rsi": round(rsi, 1),
        "gap_pct": round(best_gap, 1),
        "vol_ratio": round(best_vol_ratio, 1),
        "days_since_gap": best_day,
    }


# ─── Main Screener ────────────────────────────────────────────────────────────

def run_screen(watchlist: list[str] | None = None) -> dict:
    """
    Jalankan kedua strategi pada watchlist.
    Return: {"momentum_dip": [...], "pead": [...]}
    """
    tickers = watchlist or IDX_WATCHLIST
    md_results   = []
    pead_results = []

    end_date   = datetime.now()
    start_date = end_date - timedelta(days=420)

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
            name = info.get("longName") or info.get("shortName") or ticker

            # --- Momentum Dip ---
            md = _momentum_dip_score(hist)
            if md["score"] >= 40:
                pe  = round(info.get("trailingPE") or 0, 1)
                roe = round((info.get("returnOnEquity") or 0) * 100, 1)
                md_results.append({
                    "ticker": ticker,
                    "name": name,
                    "pe": pe,
                    "roe": roe,
                    **md,
                })

            # --- PEAD Proxy ---
            pead = _pead_proxy_score(hist)
            if pead["score"] >= 40:
                pe  = round(info.get("trailingPE") or 0, 1)
                roe = round((info.get("returnOnEquity") or 0) * 100, 1)
                pead_results.append({
                    "ticker": ticker,
                    "name": name,
                    "pe": pe,
                    "roe": roe,
                    **pead,
                })

        except Exception as e:
            print(f"[Screener] Skip {ticker}: {e}")

    md_results.sort(key=lambda x: x["score"], reverse=True)
    pead_results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "momentum_dip": md_results[:5],
        "pead": pead_results[:5],
    }


# ─── Formatter WhatsApp ───────────────────────────────────────────────────────

def format_screen_report(results: dict) -> str:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    md_list   = results.get("momentum_dip", [])
    pead_list = results.get("pead", [])

    if not md_list and not pead_list:
        return (
            f"📊 *Screener IDX — {now}*\n\n"
            "⚠️ Tidak ada setup yang memenuhi kriteria hari ini.\n"
            "_Market mungkin sideways. Coba besok._"
        )

    lines = [
        f"📊 *Short-Term Screener IDX — {now}*",
        "_Hold: 1-3 minggu | Target: beat market_",
        "",
    ]

    # ── Strategi 1: Momentum Dip ──────────────────────────────
    if md_list:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━",
            "🚀 *MOMENTUM DIP* _(win rate ~67%)_",
            "_Uptrend kuat + pullback sementara → beli dip_",
            "",
        ]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, r in enumerate(md_list[:5]):
            m     = medals[i] if i < len(medals) else f"{i+1}."
            code  = r["ticker"].replace(".JK", "")
            nama  = r["name"][:25]
            sigs  = " | ".join(r["signals"][:2])

            lines += [
                f"{m} *{code}* — _{nama}_",
                f"   💰 Rp{r['price']:,.0f}  |  PE:{r['pe']}x  |  ROE:{r['roe']}%",
                f"   📊 Skor: {r['score']}/100  |  RSI: {r['rsi']}",
                f"   📉 Pullback: -{r['pullback_pct']}%  |  Momentum 3bln: {r['momentum_3m']:+.1f}%",
                f"   🎯 Target upside: ~+{r['target_pct']}%  |  SL: bawah EMA200",
                f"   ✅ _{sigs}_",
                "",
            ]
    else:
        lines += [
            "🚀 *MOMENTUM DIP*: _Tidak ada setup hari ini_", ""
        ]

    # ── Strategi 2: PEAD Proxy ───────────────────────────────
    if pead_list:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━",
            "⚡ *PEAD PROXY* _(+5.8-8.3% dalam 30 hari, riset IDX)_",
            "_Lonjakan pasca earnings → drift masih berlanjut_",
            "",
        ]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, r in enumerate(pead_list[:5]):
            m     = medals[i] if i < len(medals) else f"{i+1}."
            code  = r["ticker"].replace(".JK", "")
            nama  = r["name"][:25]
            sigs  = " | ".join(r["signals"][:2])

            lines += [
                f"{m} *{code}* — _{nama}_",
                f"   💰 Rp{r['price']:,.0f}  |  PE:{r['pe']}x  |  ROE:{r['roe']}%",
                f"   📊 Skor: {r['score']}/100  |  RSI: {r['rsi']}",
                f"   📈 Gap/naik: +{r['gap_pct']}%  |  Volume: {r['vol_ratio']}x",
                f"   ⏱️ Signal: {r['days_since_gap']} hari lalu  |  Hold: 2-4 minggu",
                f"   ✅ _{sigs}_",
                "",
            ]
    else:
        lines += [
            "⚡ *PEAD PROXY*: _Tidak ada signal baru minggu ini_", ""
        ]

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📌 *Panduan Entry:*",
        "  • Momentum Dip: entry saat harga mulai balik (candle hijau + volume naik)",
        "  • PEAD: entry secepatnya, selambatnya H+5 dari signal",
        "  • Stop Loss selalu di bawah EMA200",
        "  • Profit taking: 80% dari target, sisanya trailing",
        "",
        "⚠️ _Bukan rekomendasi investasi. Selalu DYOR sebelum beli._",
    ]

    return "\n".join(lines)

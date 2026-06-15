"""
Technical indicators for FCAAK analysis.

FCAAK chart components:
- i59  : RSI Composite — weighted multi-period RSI
- o5   : Bollinger Bands overlay
- HL Fibo: High-Low Fibonacci retracement (auto-calculated)
- i106 : Frequency Analyzer — normalized volume, detects spikes
"""
import numpy as np
import pandas as pd
from typing import Optional


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_rsi_composite(df: pd.DataFrame, periods: list = None) -> pd.Series:
    """
    RSI Composite (i59): weighted average of RSI across multiple periods.
    Shorter periods get higher weight.
    """
    if periods is None:
        periods = [9, 14, 21]
    weights = list(range(len(periods), 0, -1))
    total_weight = sum(weights)
    composite = sum(
        calculate_rsi(df["Close"], p) * w
        for p, w in zip(periods, weights)
    ) / total_weight
    return composite


def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> dict:
    """Bollinger Bands (o5)."""
    ma = df["Close"].rolling(period).mean()
    std = df["Close"].rolling(period).std()
    return {
        "middle": ma,
        "upper": ma + std_dev * std,
        "lower": ma - std_dev * std,
        "bandwidth": (std_dev * 2 * std) / ma * 100,
    }


def calculate_hl_fibonacci(df: pd.DataFrame, lookback: int = 252) -> dict:
    """HL Fibonacci levels from the significant high and low in lookback window."""
    recent = df.tail(lookback)
    high = float(recent["High"].max())
    low = float(recent["Low"].min())
    diff = high - low
    levels = {
        "0":     low,
        "0.236": low + 0.236 * diff,
        "0.382": low + 0.382 * diff,
        "0.5":   low + 0.500 * diff,
        "0.618": low + 0.618 * diff,
        "0.786": low + 0.786 * diff,
        "1":     high,
    }
    return {"high": high, "low": low, "levels": levels}


def calculate_frequency(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Frequency Analyzer (i106): z-score of volume against rolling mean.
    Values > 2 indicate a spike (unusual accumulation/distribution activity).
    """
    vol = df["Volume"].fillna(0).astype(float)
    vol_ma = vol.rolling(period).mean()
    vol_std = vol.rolling(period).std().replace(0, np.nan)
    return (vol - vol_ma) / vol_std


def detect_bullish_divergence(price: pd.Series, rsi: pd.Series, lookback: int = 40) -> bool:
    """
    Bullish divergence: price making lower low while RSI makes higher low.
    Checks the most recent two troughs within the lookback window.
    """
    p = price.dropna().tail(lookback)
    r = rsi.dropna().reindex(p.index).dropna()
    if len(p) < 15 or len(r) < 15:
        return False

    mid = len(p) // 2
    p1_slice = p.iloc[:mid]
    p2_slice = p.iloc[mid:]
    r1_slice = r.iloc[:mid]
    r2_slice = r.iloc[mid:]

    p1_low_idx = p1_slice.idxmin()
    p2_low_idx = p2_slice.idxmin()

    try:
        p1_low = float(p.loc[p1_low_idx])
        p2_low = float(p.loc[p2_low_idx])
        r1_low = float(r.loc[p1_low_idx]) if p1_low_idx in r.index else float(r1_slice.min())
        r2_low = float(r.loc[p2_low_idx]) if p2_low_idx in r.index else float(r2_slice.min())
        return p2_low < p1_low and r2_low > r1_low
    except Exception:
        return False


def detect_volume_spike(df: pd.DataFrame, period: int = 20, threshold: float = 2.0) -> bool:
    """True if any of the last 3 bars shows a frequency spike above threshold."""
    freq = calculate_frequency(df, period)
    return bool(freq.tail(3).max() >= threshold)


def nearest_fib_level(price: float, fib: dict) -> tuple[str, float]:
    """Return (level_name, fib_price) of the closest fibonacci level to price."""
    return min(fib["levels"].items(), key=lambda x: abs(x[1] - price))

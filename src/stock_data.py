"""
IDX (Bursa Efek Indonesia) stock data fetcher.
Uses Yahoo Finance with .JK suffix for Indonesian stocks.
Caches data in data/stock_cache/ to reduce API calls.
"""
import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

CACHE_DIR = "data/stock_cache"
CACHE_TTL_HOURS = 1


def _ticker_yf(ticker: str) -> str:
    t = ticker.upper().strip()
    return t if t.endswith(".JK") else f"{t}.JK"


def _cache_path(ticker: str, period: str, interval: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe = ticker.replace(".", "_")
    return os.path.join(CACHE_DIR, f"{safe}_{period}_{interval}.json")


def _cache_valid(path: str) -> bool:
    if not os.path.exists(path):
        return False
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    return age < timedelta(hours=CACHE_TTL_HOURS)


def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV data for an Indonesian stock. Returns empty DataFrame on failure."""
    yf_ticker = _ticker_yf(ticker)
    cache = _cache_path(ticker, period, interval)

    if _cache_valid(cache):
        try:
            df = pd.read_json(cache)
            df.index = pd.to_datetime(df.index)
            return df
        except Exception:
            pass

    try:
        df = yf.download(yf_ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.to_json(cache)
        return df
    except Exception as e:
        print(f"[StockData] Error fetching {ticker}: {e}")
        return pd.DataFrame()


# Major IDX stocks for screening universe
IDX_UNIVERSE = [
    "BBCA", "BBRI", "BMRI", "TLKM", "ASII", "BYAN", "UNVR", "ICBP", "KLBF",
    "SMGR", "GGRM", "INDF", "PTBA", "ADRO", "INCO", "ANTM", "MDKA", "EXCL",
    "ISAT", "PGAS", "AKRA", "CTRA", "LPKR", "MAPI", "SMRA", "BSDE", "PWON",
    "CPIN", "JPFA", "MAIN", "BRPT", "TPIA", "LSIP", "AALI", "TBIG", "LINK",
    "HEAL", "MIKA", "SIDO", "ACES", "LPPF", "MNCN", "SCMA", "EMTK", "BUKA",
    "BRIS", "PNLF", "WIKA", "WSKT", "ADHI", "PTPP", "JSMR", "INTP", "WTON",
    "TINS", "MEDC", "ELSA", "BSSR", "HRUM", "ITMG", "BUMI", "DSSA", "BOSS",
    "ENRG", "ESSA", "BIPI", "RAJA", "TOPS", "MPXL", "GHON", "RIGS", "NCKL",
    "ADMR", "MAPA", "RANC", "ARNA", "MYOR", "WIIM", "ROTI", "AISA", "FAST",
    "CAMP", "ULTJ", "ADES", "DLTA", "SKBM", "STTP", "GOOD", "HOKI", "KEJU",
    "FOOD", "CEKA", "ALTO", "MLBI", "CMRY", "PSDN", "IKAN", "MGRO", "SMAR",
    "DSNG", "PALM", "SSMS", "BWPT", "TBLA", "SIMP", "UNSP", "CSRA", "TAPG",
    "SGRO", "GZCO", "JAWA", "ASPI", "BESS", "NICK", "POLU", "MCAS", "BCAP",
    "BHAT", "BNII", "BDMN", "BBTN", "MEGA", "NISP", "BNGA", "BJBR", "AGRO",
    "BNBA", "BJTM", "BTPS", "NOBU", "BCIC", "DNAR", "AMAR", "BACA", "INPC",
    "MCOR", "PNBN", "SDRA", "AMRT", "MIDI", "HERO", "CSAP", "MPPA", "RALS",
    "KINO", "UNIC", "PZZA", "MSIN", "PTSP", "DMAS", "KIJA", "MDLN", "SSIA",
    "DILD", "BIPP", "FORZ", "FREN", "HAIS", "SMKM", "SMIL", "MTEL", "TOWR",
]


def get_screener_universe() -> list[str]:
    return list(IDX_UNIVERSE)

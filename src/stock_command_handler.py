"""
Handler untuk perintah analisa saham (FCAAK methodology).
Integrates with the existing WhatsApp bot.

Commands handled:
  /C {ticker} [params]     — FCAAK chart & analysis
  /Score {cmd}             — Stock screening
  /mfqhis {ticker}         — Multi-frequency history (TF kecil)
  /fq {ticker} [months]    — Frequency analysis (+proyeksi jika ada months)
"""
import re
from typing import Optional


def handle_stock_command(text: str) -> Optional[tuple]:
    """
    Parse a message and execute if it's a stock command.
    Returns (reply_text, image_bytes_or_None) or None if not a stock command.
    """
    text = text.strip()

    # /C {ticker} {params}
    m = re.match(r"^/[Cc]\s+([A-Za-z]{2,6})\s*([\w,]+)?$", text)
    if m:
        ticker = m.group(1).upper()
        params = m.group(2) or "p1,o5,i59,i106"
        return _chart(ticker, params)

    # /Score {cmd}
    m = re.match(r"^/[Ss]core\s+(.+)$", text, re.IGNORECASE)
    if m:
        return _score(m.group(1).strip()), None

    # /mfqhis {ticker}
    m = re.match(r"^/mfqhis\s+([A-Za-z]{2,6})$", text, re.IGNORECASE)
    if m:
        return _mfqhis(m.group(1).upper()), None

    # /fq {ticker} [months]
    m = re.match(r"^/fq\s+([A-Za-z]{2,6})(?:\s+(\d+))?$", text, re.IGNORECASE)
    if m:
        ticker = m.group(1).upper()
        months = int(m.group(2)) if m.group(2) else 0
        return _fq(ticker, months), None

    return None


def _chart(ticker: str, params: str):
    from src.fcaak_chart import generate_fcaak_chart, format_fcaak_analysis
    img_bytes, analysis = generate_fcaak_chart(ticker, params)
    return format_fcaak_analysis(ticker, analysis), img_bytes


def _score(cmd: str) -> str:
    from src.stock_screener import run_score_command
    return run_score_command(cmd)


def _mfqhis(ticker: str) -> str:
    from src.fcaak_chart import get_mfqhis_analysis
    return get_mfqhis_analysis(ticker)


def _fq(ticker: str, months: int) -> str:
    from src.fcaak_chart import get_fq_analysis
    return get_fq_analysis(ticker, months)

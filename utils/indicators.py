# utils/indicator_tools.py
"""
Universal wrapper around the OANDA Labs *technical-indicator* endpoints.

• Remote URL pattern (as of 2025-06):  
  https://labs.oanda.com/api/technicals/{indicator}

• Indicators currently provided by Labs
  (add/remove from INDICATORS as OANDA updates the catalogue):

    SMA  EMA  WMA  DEMA  TEMA  HMA
    BBANDS
    ATR  ADX
    RSI  STOCH  STOCHRSI  WILLR
    CCI  ROC  MOM  TRIX
    MACD  MACDEXT
    OBV  VWAP  VOL
    PSAR  DONCH  KELTNER
    ICHIMOKU  SAR

Usage
-----
>>> from utils.indicator_tools import get_indicator
>>> rsi_val = get_indicator("RSI",
...                         instrument="EUR_USD",
...                         length=14,
...                         price="close",
...                         granularity="H1")

The call tries Labs first → falls back to pandas_ta if needed.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pandas_ta as ta
import requests

# ------------------------ config -------------------------------------------------
CACHE_DIR = Path(".cache") / "labs_indicators"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_TTL_S = 15 * 60  # 15-minute freshness
LABS_URL = "https://labs.oanda.com/api/technicals/{ind}"
INDICATORS = {
    "SMA",
    "EMA",
    "WMA",
    "DEMA",
    "TEMA",
    "HMA",
    "BBANDS",
    "ATR",
    "ADX",
    "RSI",
    "STOCH",
    "STOCHRSI",
    "WILLR",
    "CCI",
    "ROC",
    "MOM",
    "TRIX",
    "MACD",
    "MACDEXT",
    "OBV",
    "VWAP",
    "VOL",
    "PSAR",
    "DONCH",
    "KELTNER",
    "ICHIMOKU",
    "SAR",
}
# ---------------------------------------------------------------------------------


class LabsError(RuntimeError):
    """Raised when a Labs request fails and no local fallback is possible."""


# ------------------------ public helper ------------------------------------------
def get_indicator(indicator: str, **params) -> Dict[str, Any]:
    """
    Fetch <indicator> values from OANDA Labs – OR compute locally on fallback.

    Parameters
    ----------
    indicator : str
        One of the names in INDICATORS (case-insensitive).
    **params  : key/value
        Whatever the Labs endpoint expects (instrument, length, price …)

    Returns
    -------
    dict
        The JSON payload returned by Labs *or* a
        {"indicator": <name>, "series": [...] } structure when computed locally.
    """

    ind = indicator.upper()
    if ind not in INDICATORS:
        raise ValueError(f"{indicator} not in supported list {sorted(INDICATORS)}")

    cache_f = _cache_file(ind, params)
    if cache_f.exists() and (time.time() - cache_f.stat().st_mtime) < CACHE_TTL_S:
        return json.loads(cache_f.read_text())

    # ---------- try Labs first ---------------------------------------------------
    try:
        payload = _fetch_from_labs(ind, params)
        cache_f.write_text(json.dumps(payload))
        return payload
    except Exception as exc:
        # ---------- fallback -----------------------------------------------------
        try:
            payload = _compute_locally(ind, params)
            cache_f.write_text(json.dumps(payload))
            return payload
        except Exception as fallback_exc:
            raise LabsError(
                f"Labs call failed ({exc!s}) and local fallback errored "
                f"({fallback_exc!s})."
            ) from fallback_exc


# ======================== internal helpers =======================================


def _cache_file(ind: str, params: Dict[str, Any]) -> Path:
    key = f"{ind}:{json.dumps(params, sort_keys=True)}"
    digest = hashlib.sha1(key.encode()).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _fetch_from_labs(ind: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = LABS_URL.format(ind=ind.lower())
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _compute_locally(ind: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very small local implementation set based on pandas_ta.
    Extend this dispatcher as needed.
    """
    instrument = params.get("instrument")
    gran = params.get("granularity", "D")
    length = int(params.get("length", 14))
    price_fld = params.get("price", "close").lower()

    # --- you would normally fetch candles from OANDA REST here ------------------
    from utils.price_tools import fetch_candle_data, get_pip_value  # lazy import

    # Dummy token/env/account_id are irrelevant – price_tools handles auth.
    # Fill these with real values in your app-context.
    candles = fetch_candle_data(
        client=None,  # sentinel – price_tools will build its own
        instrument=instrument,
        count=500,  # enough look-back for most studies
        granularity=gran,
    )

    series = pd.Series(candles.values, name=price_fld)

    dispatch = {
        "SMA": lambda: ta.sma(series, length=length),
        "EMA": lambda: ta.ema(series, length=length),
        "WMA": lambda: ta.wma(series, length=length),
        "RSI": lambda: ta.rsi(series, length=length),
        "ATR": lambda: ta.atr(high=series, low=series, close=series, length=length),
        "MACD": lambda: ta.macd(series).iloc[:, 0],  # MACD line
        "STOCH": lambda: ta.stoch(high=series, low=series, close=series).iloc[:, 0],
        # add more local fall-backs here …
    }

    if ind not in dispatch:
        raise NotImplementedError(
            f"Local fallback for {ind} not implemented – request Labs instead."
        )

    values = dispatch[ind]().dropna().tolist()
    return {"indicator": ind, "series": values, "source": "local"}


__all__ = ["get_indicator", "INDICATORS", "LabsError"]

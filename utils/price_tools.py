# utils/price_tools.py

import pandas as pd
from oandapyV20.endpoints.instruments import InstrumentsCandles
from oandapyV20 import API
from PySide6.QtWidgets import QMessageBox
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.pricing import PricingInfo
import sys


def get_pip_value(pair):
    return 0.01 if "JPY" in pair else 0.0001


def fetch_candle_data(
    client: API, instrument: str, count: int = 100, granularity: str = "M5"
):
    params = {"granularity": granularity, "count": count, "price": "M"}
    r = InstrumentsCandles(instrument=instrument, params=params)
    response = client.request(r)
    if not response["candles"]:
        raise RuntimeError(
            f"No candle data returned for {instrument}. "
            "Check instrument code or network connectivity."
        )

    closes = [
        float(candle["mid"]["c"])
        for candle in response["candles"]
        if candle["complete"]
    ]
    return pd.Series(closes)


def calculate_ema(series: pd.Series, period: int):
    return series.ewm(span=period).mean().iloc[-1]


def calculate_trailing_stop(
    direction: str, current_price: float, pip_distance: float, pip_value: float
):
    """
    Adjust the SL only in the profit direction
    """
    if direction == "Buy":
        return round(current_price - pip_distance * pip_value, 5)
    elif direction == "Sell":
        return round(current_price + pip_distance * pip_value, 5)
    else:
        raise ValueError("[Trailing SL] Invalid direction provided.")


# Feth current price
def fetch_current_price(token, account_id, environment, instrument):
    try:
        client = API(access_token=token, environment=environment)
        params = {"instruments": instrument}
        r = PricingInfo(accountID=account_id, params=params)
        # utils/price_tools.py  – replace the bottom of fetch_current_price()

        response = client.request(r)
        prices = response.get("prices", [])

        if not prices:  # ✨ <- ADD THIS
            raise RuntimeError(
                f"No price data returned for {instrument}. "
                "Check instrument code or network connectivity."
            )

        bid = float(prices[0]["bids"][0]["price"])
        ask = float(prices[0]["asks"][0]["price"])
        return round((bid + ask) / 2, 5)

    except V20Error as e:
        if "PySide6" in sys.modules:
            QMessageBox.critical(
                None, "Price Fetch Error", f"Could not fetch instrument price:\n{e}"
            )
            print(f"[ERROR] Could not fetch price: {e}")
        else:
            print(f"[ERROR] Could not fetch price: {e}")


def is_market_open(client, account_id, instrument):
    try:
        params = {"instruments": instrument}
        r = PricingInfo(accountID=account_id, params=params)
        response = client.request(r)

        prices = response.get("prices", [])
        if prices and "bids" in prices[0] and "asks" in prices[0]:
            return True  # Prices available = market open
        return False
    except V20Error as e:
        print(f"[Market Check] V20Error: {e}")
        return False

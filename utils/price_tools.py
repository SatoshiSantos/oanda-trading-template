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
    if direction == "buy":
        return round(current_price - pip_distance * pip_value, 5)
    elif direction == "sell":
        return round(current_price + pip_distance * pip_value, 5)
    else:
        raise ValueError("[Trailing SL] Invalid direction provided.")


# Feth current price
def fetch_current_price(token, account_id, environment, instrument):
    try:
        client = API(access_token=token, environment=environment)
        params = {"instruments": instrument}
        r = PricingInfo(accountID=account_id, params=params)
        response = client.request(r)
        prices = response["prices"][0]
        # Return the average of bid and ask as current price
        bid = float(prices["bids"][0]["price"])
        ask = float(prices["asks"][0]["price"])
        return round((bid + ask) / 2, 5)

    except V20Error as e:
        if "PySide6" in sys.modules:
            QMessageBox.critical(
                None, "Price Fetch Error", f"Could not fetch instrument price:\n{e}"
            )
            print(f"[ERROR] Could not fetch price: {e}")
        else:
            print(f"[ERROR] Could not fetch price: {e}")

# core/sl_strategies.py

from utils.price_tools import (
    get_pip_value,
    fetch_candle_data,
    calculate_ema,
    calculate_trailing_stop,
)
from oandapyV20 import API
from oandapyV20.exceptions import V20Error

"""
TODO: Add logging inside each method (especially ema_based_sl) so you can inspect values during live runs or debugging.

Cache EMA results inside the class or with memoization, if you're calling it repeatedly for the same candle data.

"""


class StopLossStrategy:
    def __init__(self, config):
        self.config = config

    def get_stop_loss(self, current_price, direction):
        strategy = self.config.get("sl_strategy", "Fixed SL (pips)")

        if strategy == "Fixed SL (pips)":
            return self.fixed_sl(current_price, direction)
        elif strategy == "Trailing SL":
            return self.trailing_sl(current_price, direction)
        elif strategy == "EMA-Based SL":
            return self.ema_based_sl(current_price, direction)
        else:
            raise ValueError(f"[SL Strategy] Unknown stop loss strategy: {strategy}")

    def fixed_sl(self, current_price, direction):
        try:
            pips = float(self.config.get("sl_pips", 10))
        except ValueError:
            raise ValueError("[SL Strategy] Invalid 'sl_pips' value in config.")

        pip_value = get_pip_value(self.config.get("pair", ""))
        if direction == "buy":
            return round(current_price - (pips * pip_value), 5)
        else:
            return round(current_price + (pips * pip_value), 5)

    def trailing_sl(self, current_price, direction):
        try:
            distance = float(self.config.get("trailing_distance", 10))
        except ValueError:
            raise ValueError(
                "[SL Strategy] Invalid 'trailing_distance' value in config."
            )

        pip_value = get_pip_value(self.config.get("pair", ""))
        return calculate_trailing_stop(direction, current_price, distance, pip_value)

    def ema_based_sl(self, current_price, direction):
        try:
            ema_period = int(self.config.get("ema_period", 21))
        except ValueError:
            raise ValueError("[SL Strategy] Invalid EMA period provided.")

        pair = self.config.get("pair", "")
        granularity = self.config.get("timeframe", "M5")
        token = self.config.get("token", "")
        environment = self.config.get("environment", "")
        account_id = self.config.get("account_id", "")

        try:
            client = API(access_token=token, environment=environment)
            price_series = fetch_candle_data(
                client, pair, count=ema_period * 2, granularity=granularity
            )
            ema_value = calculate_ema(price_series, period=ema_period)
        except V20Error as e:
            raise RuntimeError(f"[SL Strategy] Failed to fetch data for EMA SL: {e}")

        # SL follows the EMA only on the profit side
        if direction == "buy":
            return round(min(current_price, ema_value), 5)
        else:
            return round(max(current_price, ema_value), 5)

# backtest/backtester.py
"""
Light-weight historical simulator for strategies that implement   backtest_step(candle) → str
----------------------------------------------------------------
• action strings accepted from backtest_step():
    "buy"   – open long if flat
    "sell"  – open short if flat
    "exit"  – close any open position
    None    – do nothing
• One position at a time (you can extend to multiple later).
• Uses close price for fills; latency/slippage ignored for now.
----------------------------------------------------------------
"""

from datetime import datetime
import uuid
import importlib
import pandas as pd
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles


class Backtester:
    def __init__(self, config: dict):
        self.cfg = config.copy()
        self.instrument = self.cfg["pair"]
        self.granularity = self.cfg["timeframe"]  # e.g. "M15"
        self.initial_balance = float(self.cfg.get("starting_balance", 100_000))
        self.balance = self.initial_balance
        self.equity_curve = []  # list[dict(time, equity)]
        self.trades = []  # list[dict(...)]

        # ----- basic validation before we touch OANDA ----------
        if not self.cfg.get("token"):
            raise RuntimeError("Back-test requires a valid OANDA token.")
        if self.cfg.get("environment") != "practice":
            raise RuntimeError("Back-test must run against the 'practice' environment.")
        # load Strategy
        self._load_strategy()
        # build API client only *after* the checks above
        self.client = API(
            access_token=self.cfg["token"], environment=self.cfg["environment"]
        )

    # -------------------------------- private helpers --------------
    def _load_strategy(self):
        mod = importlib.import_module(f"strategies.{self.cfg['strategy']}")
        Strategy = getattr(mod, "Strategy")
        # news_filter=None because it doesn't matter in backtest right now
        self.strategy = Strategy(
            config=self.cfg,
            news_filter=None,
            direction=self.cfg.get("direction", "Both"),
            current_price=None,
            pair=self.instrument,
            chart_timeframe=self.granularity,
        )
        if not hasattr(self.strategy, "backtest_step"):
            raise AttributeError(
                f"{self.cfg['strategy']} must implement backtest_step() "
                "to be used in backtest mode."
            )

    # backtest/backtester.py
    def _fetch_candles(self, count: int = 1000) -> pd.DataFrame:
        """Return *exactly* `count` completed candles."""
        params = {"granularity": self.granularity, "count": count + 1, "price": "M"}

        rows = []
        while len(rows) < count:
            r = InstrumentsCandles(instrument=self.instrument, params=params)
            raw = self.client.request(r)["candles"]
            filled = [c for c in raw if c["complete"]]

            rows.extend(filled)
            # stop if we have enough, otherwise ask further back in time
            if len(rows) >= count:
                rows = rows[-count:]  # keep last `count`
                break
            # move the `to` parameter back for next fetch
            params["to"] = filled[0]["time"]

        return pd.DataFrame(
            dict(
                time=c["time"],
                open=float(c["mid"]["o"]),
                high=float(c["mid"]["h"]),
                low=float(c["mid"]["l"]),
                close=float(c["mid"]["c"]),
            )
            for c in rows
        )

    # -------------------------------- public API -------------------
    def run(self, candle_count: int = 1000) -> dict:
        df = self._fetch_candles(candle_count)
        position = None  # None or dict(entry_price, dir, entry_time, multiplier)

        for _, candle in df.iterrows():
            px = candle["close"]
            self.strategy.current_price = px
            action = self.strategy.backtest_step(candle)

            # ---- exit logic
            if position and action in ("exit", "buy", "sell"):
                pl = (px - position["entry_price"]) * position["multiplier"]
                self.balance += pl
                self.trades.append(
                    {
                        "id": str(uuid.uuid4())[:8],
                        "direction": position["dir"],
                        "entry_price": position["entry_price"],
                        "exit_price": px,
                        "pl": pl,
                        "entry_time": position["entry_time"],
                        "exit_time": candle["time"],
                    }
                )
                position = None
                action = (
                    action if action == "exit" else action
                )  # continue to possible flip

            # ---- entry logic
            if not position and action in ("buy", "sell"):
                position = dict(
                    dir=action,
                    entry_price=px,
                    entry_time=candle["time"],
                    multiplier=1 if action == "buy" else -1,
                )

            # ---- equity snap
            eq = self.balance
            if position:
                eq += (px - position["entry_price"]) * position["multiplier"]
            self.equity_curve.append(
                {
                    "ts": pd.to_datetime(
                        candle["time"]
                    ),  # ↩ could be first, but fine as-is
                    "time": candle["time"],
                    "equity": eq,
                }
            )

        # force-close any last open position at final candle
        if position:
            px = df.iloc[-1]["close"]
            pl = (px - position["entry_price"]) * position["multiplier"]
            self.balance += pl
            self.trades.append(
                {
                    "id": str(uuid.uuid4())[:8],
                    "direction": position["dir"],
                    "entry_price": position["entry_price"],
                    "exit_price": px,
                    "pl": pl,
                    "entry_time": position["entry_time"],
                    "exit_time": df.iloc[-1]["time"],
                }
            )

        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "profit": self.balance - self.initial_balance,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }


def run_backtest(config: dict, candle_count: int = 1000):
    return Backtester(config).run(candle_count)

# strategies/ExampleStrategy.py

import time
from strategies.base_strategy import StrategyBase
from core.risk_manager import RiskManager
from core.sl_strategies import StopLossStrategy
from core.tp_strategies import TakeProfitStrategy
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
import oandapyV20.types as oanda_types
import random  # For random position size to avoid FIFO untill full order management


class Strategy(StrategyBase):
    def run(self, stop_flag=False):
        self.stop_flag = stop_flag
        print(f"[{self.__class__.__name__}] Strategy initiated.")
        print(f"Pair: {self.pair}, Timeframe: {self.chart_timeframe}")
        print(f"News Filter Active: {self.news_filter is not None}")

        # --- Set trade direction ---
        if self.direction == "Both":
            self.direction = random.choice(["Buy", "Sell"])

        if "current_price" not in self.config:
            raise ValueError("[Config] Missing current_price in config.")

        while not (self.stop_flag and self.stop_flag()):
            # run trading logic here (fetch candles, check signals, execute trades)
            # time.sleep(10)  # or suitable interval

            # --- Calculate SL and TP ---
            sl_handler = StopLossStrategy(self.config)
            tp_handler = TakeProfitStrategy(self.config)

            stop_loss_price = sl_handler.get_stop_loss(
                self.current_price, self.direction
            )
            take_profit_price = tp_handler.get_take_profit(
                self.current_price, self.direction, stop_loss_price
            )

            # --- Risk Management ---
            risk_manager = RiskManager(self.config)
            position_size = risk_manager.calculate_position_size(
                entry_price=self.current_price, stop_loss_price=stop_loss_price
            )
            # --- Add randomness to satisfy FIFO (±1~5 units)
            position_size += random.randint(1, 5)  # Add a tiny random offset

            print(f"Entry Price: {self.current_price}")
            print(f"Stop Loss: {stop_loss_price}")
            print(f"Take Profit: {take_profit_price}")
            print(f"Computed Position Size: {position_size}")

            # --- Execute Trade ---
            order_data = {
                "order": {
                    "instrument": self.pair,
                    "units": str(
                        position_size if self.direction == "Buy" else -position_size
                    ),
                    "type": "MARKET",
                    "positionFill": "DEFAULT",
                    "stopLossOnFill": {"price": str(round(stop_loss_price, 5))},
                    "takeProfitOnFill": {"price": str(round(take_profit_price, 5))},
                }
            }

            try:
                client = API(
                    access_token=self.config["token"],
                    environment=self.config["environment"],
                )
                r = OrderCreate(accountID=self.config["account_id"], data=order_data)
                response = client.request(r)
                print(f"[ORDER PLACED] Trade executed successfully: {response}")
            except Exception as e:
                print(f"[ERROR] Failed to place order: {e}")

            time.sleep(10)  # sleep seconds per interval

# strategies/ExampleStrategy.py

import time
from time import datetime
from strategies.base_strategy import StrategyBase
from core.risk_manager import RiskManager
from core.sl_strategies import StopLossStrategy
from core.tp_strategies import TakeProfitStrategy
from core.trade_manager import TradeManager
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate


class Strategy(StrategyBase):
    def run(self, stop_flag=False):
        self.stop_flag = stop_flag
        print(f"[{self.__class__.__name__}] Strategy initiated.")
        print(f"Pair: {self.pair}, Timeframe: {self.chart_timeframe}")
        print(f"News Filter Active: {self.news_filter is not None}")

        self.config["direction"] = self.config.get("direction", "Buy")
        direction = self.config["direction"]
        client = API(
            access_token=self.config["token"], environment=self.config["environment"]
        )
        trade_manager = TradeManager(
            client, self.config["account_id"]
        )  # ✅ Init TradeManager

        while not (self.stop_flag and self.stop_flag()):
            sl_handler = StopLossStrategy(self.config)
            tp_handler = TakeProfitStrategy(self.config)

            stop_loss_price = sl_handler.get_stop_loss(self.current_price, direction)
            take_profit_price = tp_handler.get_take_profit(
                self.current_price, direction, stop_loss_price
            )

            risk_manager = RiskManager(self.config)
            position_size = risk_manager.calculate_position_size(
                entry_price=self.current_price, stop_loss_price=stop_loss_price
            )

            print(f"Entry Price: {self.current_price}")
            print(f"Stop Loss: {stop_loss_price}")
            print(f"Take Profit: {take_profit_price}")
            print(f"Computed Position Size: {position_size}")

            order_data = {
                "order": {
                    "instrument": self.pair,
                    "units": str(
                        position_size if direction == "Buy" else -position_size
                    ),
                    "type": "MARKET",
                    "positionFill": "DEFAULT",
                    "stopLossOnFill": {"price": str(round(stop_loss_price, 5))},
                    "takeProfitOnFill": {"price": str(round(take_profit_price, 5))},
                }
            }

            try:
                r = OrderCreate(accountID=self.config["account_id"], data=order_data)
                response = client.request(r)
                print(f"[ORDER PLACED] Trade executed successfully: {response}")

                trade_id = response["orderCreateTransaction"]["id"]
                timestamp = response["orderCreateTransaction"]["time"]

                trade_manager.register_trade(
                    trade_id=trade_id,
                    trade_info={
                        "timestamp": timestamp,
                        "instrument": self.pair,
                        "units": position_size,
                        "direction": direction,
                        "entry_price": self.current_price,
                        "stop_loss": stop_loss_price,
                        "take_profit": take_profit_price,
                    },
                )

            except Exception as e:
                print(f"[ERROR] Failed to place order: {e}")

            time.sleep(30)

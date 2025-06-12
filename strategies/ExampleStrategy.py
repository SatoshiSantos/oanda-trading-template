# strategies/ExampleStrategy.py

import time
from strategies.base_strategy import StrategyBase
from core.risk_manager import RiskManager
from core.sl_strategies import StopLossStrategy
from core.tp_strategies import TakeProfitStrategy
from core.trade_manager import TradeManager
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from utils.price_tools import is_market_open


class Strategy(StrategyBase):
    def run(self, stop_flag=False):
        self.stop_flag = stop_flag
        print(f"[{self.__class__.__name__}] Strategy initiated.")
        print(f"Pair: {self.pair}, Timeframe: {self.chart_timeframe}")
        print(f"News Filter Active: {self.news_filter is not None}")

        self.config["direction"] = self.config.get("direction")
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

            if direction == "Both" or direction == "Buy":
                ...  # TODO: BUY conditions
            if direction == "Both" or direction == "Sell":
                ...  # TODO: SELL conditions

            # check if maret open
            if is_market_open(client, self.config["account_id"], self.pair):

                try:
                    r = OrderCreate(
                        accountID=self.config["account_id"], data=order_data
                    )

                    response = client.request(r)

                    # Check if order was created
                    if "orderCreateTransaction" in response:
                        trade_id = response["orderCreateTransaction"]["id"]
                        print(f"[ORDER PLACED] Order created successfully: {trade_id}")
                    timestamp = response["orderCreateTransaction"].get("time", "")
                    order_type = response["orderCreateTransaction"].get("type", "")
                    reason = response["orderCreateTransaction"].get("reason", "")
                    timeInForce = response["orderCreateTransaction"].get(
                        "timeInForce", ""
                    )
                    relatedTransactionIDs = response.get("relatedTransactionIDs", [])

                    # Default to 'filled' unless explicitly canceled
                    status = "filled"
                    if "orderCancelTransaction" in response:
                        cancel_reason = response["orderCancelTransaction"].get(
                            "reason", ""
                        )
                        status = f"canceled ({cancel_reason})"
                        print(f"[ORDER CANCELED] {trade_id} ({cancel_reason})")

                    trade_manager.register_trade(
                        trade_id=trade_id,
                        trade_info={
                            "type": order_type,
                            "reason": reason,
                            "timestamp": timestamp,
                            "instrument": self.pair,
                            "units": position_size,
                            "direction": direction,
                            "entry_price": self.current_price,
                            "stop_loss": stop_loss_price,
                            "take_profit": take_profit_price,
                            "timeInForce": timeInForce,
                            "relatedTransactionIDs": relatedTransactionIDs,
                            "status": status,
                        },
                    )

                except Exception as e:
                    print(f"[ERROR] Failed to place order: {e}")
            else:
                print("[Market Closed] Trading skipped due to market closure.")

            time.sleep(30)

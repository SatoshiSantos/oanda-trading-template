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
from utils.indicators import get_indicator  # generic helper


class Strategy(StrategyBase):
    def run(self, stop_flag=False):
        self.stop_flag = stop_flag
        print(f"[{self.__class__.__name__}] Strategy initiated.")
        print(f"Pair: {self.pair}, Timeframe: {self.chart_timeframe}")
        token = self.config["token"]
        env = self.config["environment"]
        id = self.config["account_id"]
        # print(f"News Filter Active: {self.news_filter is not None}")

        self.config["direction"] = self.config.get("direction")
        direction = self.config["direction"]

        # Init API client
        client = API(access_token=token, environment=env)

        # Init TradeManager
        trade_manager = TradeManager(client, id)

        # Run strategy logic while stop flag (Stop button pressed) is false
        while not (self.stop_flag and self.stop_flag()):

            # Calculate Stop loss
            sl_handler = StopLossStrategy(self.config)
            tp_handler = TakeProfitStrategy(self.config)

            stop_loss_price = sl_handler.get_stop_loss(self.current_price, direction)
            take_profit_price = tp_handler.get_take_profit(
                self.current_price, direction, stop_loss_price
            )

            # Calculate position size per risk input
            risk_manager = RiskManager(self.config)
            position_size = risk_manager.calculate_position_size(
                entry_price=self.current_price, stop_loss_price=stop_loss_price
            )

            # Print check trade param prior to order
            print(f"Entry Price: {self.current_price}")
            print(f"Stop Loss: {stop_loss_price}")
            print(f"Take Profit: {take_profit_price}")
            print(f"Computed Position Size: {position_size}")
            # Order Data
            order_data = {
                "order": {
                    "instrument": self.pair,
                    "units": str(
                        # positive = Buy, Negative = Sell
                        position_size
                        if direction == "Buy"
                        else -position_size
                    ),
                    "type": "MARKET",
                    "positionFill": "DEFAULT",
                    "stopLossOnFill": {"price": str(round(stop_loss_price, 5))},
                    "takeProfitOnFill": {"price": str(round(take_profit_price, 5))},
                }
            }

            # ------------------------------------------------------------------
            # EMA-cross signal engine via get_indicator()
            # Tries OANDA-Labs first; falls back to pandas_ta if Labs doesn’t
            # support the request or is rate-limited.
            # ------------------------------------------------------------------

            FAST_LEN = 5
            SLOW_LEN = 20

            # --- pull fast & slow EMA values ----------------------------------
            fast_ema = get_indicator(
                "EMA",
                instrument=self.pair,
                length=FAST_LEN,
                price="close",
                granularity=self.chart_timeframe,  # e.g. "M15"
            )

            slow_ema = get_indicator(
                "EMA",
                instrument=self.pair,
                length=SLOW_LEN,
                price="close",
                granularity=self.chart_timeframe,
            )

            # get_indicator returns **None** if data are still warming up
            if fast_ema is None or slow_ema is None:
                print("[EMA-CROSS] waiting for sufficient history …")
                time.sleep(5)
                continue

            print(f"[EMA-CROSS] fast {fast_ema:.5f}   slow {slow_ema:.5f}")

            signal = None
            if fast_ema > slow_ema:
                signal = "Buy"
            elif fast_ema < slow_ema:
                signal = "Sell"

            # ------------- act on the signal ----------------------------------
            if signal == "Buy" and direction in ("Both", "Buy"):
                # keep everything already prepared (order_data, SL/TP, position_size …)
                # simply let execution continue to the market-open check ↓
                pass

            elif signal == "Sell" and direction in ("Both", "Sell"):
                # flip the units sign (negative = short) and update order_data
                order_data["order"]["units"] = str(-abs(position_size))
            else:
                # no actionable signal → skip this loop iteration
                time.sleep(10)  # small back-off
                continue
            # ------------------------------------------------------------------

            # check if market open
            if is_market_open(client, self.config["account_id"], self.pair):

                try:
                    # Create the order
                    r = OrderCreate(
                        accountID=self.config["account_id"], data=order_data
                    )
                    # Store the response
                    response = client.request(r)

                    # Check if order was created store the order information
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
                    # Check if order was canceled
                    if "orderCancelTransaction" in response:
                        cancel_reason = response["orderCancelTransaction"].get(
                            "reason", ""
                        )
                        # Update status print error
                        status = f"canceled ({cancel_reason})"
                        print(f"[ORDER CANCELED] {trade_id} ({cancel_reason})")

                    # Register the trade to the trade manager
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
                    print(f"[REGISTER TRADE ERROR] Failed to place order: {e}")
            else:
                print("[Market Closed] Trading skipped due to market closure.")

            time.sleep(30)

    def backtest_step(self, candle):
        """
        Very naive example:
        • Buy when candle closes green
        • Sell when candle closes red
        • Exit when opposite signal appears
        """
        close_above_open = candle["close"] > candle["open"]
        close_below_open = candle["close"] < candle["open"]

        if close_above_open:
            return "buy"
        if close_below_open:
            return "sell"
        return None  # do nothing

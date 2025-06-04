# strategies/ExampleStrategy.py

from strategies.base_strategy import StrategyBase
from core.risk_manager import RiskManager
from core.sl_strategies import StopLossStrategy
from core.tp_strategies import TakeProfitStrategy


class Strategy(StrategyBase):
    def run(self):
        print(f"[{self.__class__.__name__}] Strategy is now running.")
        print(f"Pair: {self.pair}, Timeframe: {self.chart_timeframe}")
        print(f"News Filter Active: {self.news_filter is not None}")

        # TODO: Trade direction logic

        # Hard code direction for now to avoid Return None error [Trailing SL] Invalid direction provided.

        self.config["direction"] = "Buy"

        # Compute SL and TP
        if "current_price" not in self.config:  # or "direction" not in self.config:
            raise ValueError("[Config] Missing current_price or direction in config.")

        sl_handler = StopLossStrategy(self.config)
        tp_handler = TakeProfitStrategy(self.config)

        stop_loss_price = sl_handler.get_stop_loss(self.current_price, self.direction)
        take_profit_price = tp_handler.get_take_profit(
            self.current_price, self.direction, stop_loss_price
        )

        # Compute position size dynamically based on SL distance
        risk_manager = RiskManager(self.config)
        position_size = risk_manager.calculate_position_size(
            entry_price=self.current_price, stop_loss_price=stop_loss_price
        )

        # Log results
        print(f"Entry Price: {self.current_price}")
        print(f"Stop Loss: {stop_loss_price}")
        print(f"Take Profit: {take_profit_price}")
        print(f"Computed Position Size: {position_size}")

        # Placeholder for trade execution
        print(f"[{self.__class__.__name__}] Trade logic not implemented.")

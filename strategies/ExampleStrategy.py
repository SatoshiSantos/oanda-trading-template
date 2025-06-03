# strategies/strategy_template.py

from abc import ABC, abstractmethod


class StrategyBase(ABC):
    def __init__(
        self,
        config,
        position_size=None,
        risk_manager=None,
        take_profit=None,
        stop_loss=None,
        pair=None,
        chart_timeframe=None,
    ):
        self.config = config
        self.position_size = position_size
        self.risk_manager = risk_manager
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.pair = pair
        self.chart_timeframe = chart_timeframe

    @abstractmethod
    def run(self):
        """Execute the strategy logic."""
        pass


class Strategy(StrategyBase):
    def run(self):
        print("[STRATEGY] Running example strategy...")

        # Use news filter if enabled
        if self.news_filter and not self.news_filter.is_trade_time():
            print("[STRATEGY] Skipping trade due to nearby news event.")
            return

        # Dummy trade logic
        print(
            f"[STRATEGY] Placing dummy trade for {self.pair} on {self.chart_timeframe} timeframe"
        )

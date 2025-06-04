# strategies/base_strategy.py


class StrategyBase:
    def __init__(
        self, config, news_filter, direction, current_price, pair, chart_timeframe
    ):
        self.config = config
        self.news_filter = news_filter
        self.pair = pair
        self.chart_timeframe = chart_timeframe
        self.direction = direction
        self.current_price = current_price

    def run(self):
        raise NotImplementedError("Subclasses must implement the run() method")

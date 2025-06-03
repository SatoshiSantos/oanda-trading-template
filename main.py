# main.py
import importlib
from strategies.ExampleStrategy import StrategyBase
from core.news_filter import NewsFilter
from core.risk_manager import RiskManager
from core.sl_strategies import StopLossStrategy
from core.tp_strategies import TakeProfitStrategy


def run_strategy(config):
    """Main entry point for running a strategy."""
    print("[INFO] Running strategy with config:", config)

    # --- Step 1: Validate config ---
    required_keys = ["account_id", "token", "environment", "strategy"]
    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required config key: {key}")

    # --- Step 2: Initialize shared components ---
    news_filter = NewsFilter(config)
    # print(f"News Filter: {news_filter}")
    risk_manager = RiskManager(config)
    position_size = risk_manager.calculate_position_size()
    # print(f"[STRATEGY] Position size calculated: {position_size}")
    # print(f"Calculated Risk Per trade: {risk_manager}")

    # SL logic
    sl_handler = StopLossStrategy(config)
    current_price = 1.1000  # dummy price
    direction = "buy"  # or "sell"
    stop_loss_price = sl_handler.get_stop_loss(current_price, direction)
    # print(f"Calculated Stop Loss: {stop_loss_price}")

    # TP logic
    tp_handler = TakeProfitStrategy(config)
    take_profit_price = tp_handler.get_take_profit(
        current_price, direction, stop_loss_price
    )
    # print(f"Calculated Take Profit: {take_profit_price}")

    # Access config
    pair = config["pair"]
    chart_timeframe = config["timeframe"]
    # print(f"[STRATEGY] Trading pair: {pair}, Timeframe: {timeframe}")

    # --- Step 3: Dynamically load the selected strategy ---
    strategy_name = config["strategy"]
    try:
        strategy_module = importlib.import_module(f"strategies.{strategy_name}")
        StrategyClass = getattr(strategy_module, "Strategy")
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not load strategy '{strategy_name}': {e}")

    # --- Step 4: Instantiate and validate strategy class ---
    strategy = StrategyClass(
        config,
        news_filter=news_filter,
        position_size=position_size,
        take_profit=take_profit_price,
        stop_loss=stop_loss_price,
        pair=pair,
        chart_timeframe=chart_timeframe,
    )
    if not isinstance(strategy, StrategyBase):
        raise TypeError("Strategy must inherit from StrategyBase")

    # --- Step 5: Run the strategy ---
    strategy.run()

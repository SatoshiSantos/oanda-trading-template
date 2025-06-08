# main.py

import importlib
from strategies.base_strategy import StrategyBase
from core.news_filter import NewsFilter
from core.max_drawdown import MaxDrawdownChecker
from oandapyV20 import API
from core.trading_time import is_within_trading_window
from utils.account_tools import account_balance


def run_strategy(config, gui_parent=None):
    """Main entry point for running a strategy."""
    print("[INFO] Strategy Launch Details:")
    print(f"  Account ID: {config.get('account_id')}")
    print(f"  Environment: {config.get('environment')}")
    print(f"  Pair: {config.get('pair')}")
    print(f"  Timeframe: {config.get('timeframe')}")
    print(f"  Strategy: {config.get('strategy')}")
    print(f"  Direction: {config.get('direction')}")
    print(
        f"  SL Strategy: {config.get('sl_strategy')}, TP Strategy: {config.get('tp_strategy')}"
    )
    print(
        f"  Risk per Trade: {config.get('risk_per_trade')}%, Max Drawdown: {config.get('max_drawdown')}%"
    )
    print(f"  News Filter Active: {any(config.get('news_impact', {}).values())}")

    # --- Step 1: Validate config ---
    required_keys = ["account_id", "token", "environment", "strategy"]
    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required config key: {key}")

    config["account_balance"] = account_balance(
        token=config["token"],
        account_id=config["account_id"],
        environment=config["environment"],
    )
    # Step 1.5: OANDA API client setup
    client = API(access_token=config["token"], environment=config["environment"])

    # Step 1.6: Max drawdown check (only if value is provided)
    max_dd_str = config.get("max_drawdown")
    if max_dd_str:
        try:
            max_dd = float(max_dd_str)
            if max_dd > 0:
                drawdown_checker = MaxDrawdownChecker(config, client)
                print(f"Current Account Balance {config['account_balance']}")
                print(f"Max Drawdown input {drawdown_checker.max_drawdown_amount}")
                print(f"Draw Down exceed {drawdown_checker.is_drawdown_exceeded()}")

                # check daily drawdown
                if drawdown_checker.is_drawdown_exceeded():
                    msg = "[HALT] Max drawdown amount reached. Trading suspended for today."
                    print(msg)
                    if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
                        gui_parent.strategy_error_signal.emit(msg)
                    return
        except ValueError:
            print("[WARNING] Invalid max_drawdown value, skipping drawdown check.")

    # Step 1.7: Trading Time check (only if both start and end times are provided)
    if config.get("start_time") and config.get("end_time"):
        if not is_within_trading_window(config):
            msg = "[HALT] Time Outside of Trading Window. Trading suspended."
            print(msg)
            if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
                gui_parent.strategy_error_signal.emit("Outside of Trading Time Frame")
            return

    # --- Step 2: News Filter Check ---
    try:
        if any(config.get("news_impact", {}).values()):
            news_filter = NewsFilter(config, gui_parent=gui_parent)
            if news_filter.is_trade_blocked_by_news():
                msg = (
                    "[HALT] Trading suspended due to upcoming impactful economic news."
                )
                print(msg)
                if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
                    gui_parent.strategy_error_signal.emit(
                        f" News Filter Error: {str(e)}"
                    )
                return
        else:
            news_filter = None
    except Exception as e:
        print(f"[WARN] News filter failed: {e}")
        news_filter = None

    # current price
    # Validate critical runtime values
    if "current_price" not in config:
        raise ValueError("[Config] 'unable to fetch current_price'.")
    current_price = config["current_price"]

    # Trade Direction
    # Validate critical runtime values
    if "direction" not in config:
        raise ValueError("[Config] 'direction' must be specified in the config.")
    direction = config["direction"]

    # --- Step 3: Load and validate strategy class dynamically ---
    strategy_name = config["strategy"]
    try:
        strategy_module = importlib.import_module(f"strategies.{strategy_name}")
        StrategyClass = getattr(strategy_module, "Strategy")
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not load strategy '{strategy_name}': {e}")

    strategy = StrategyClass(
        config=config,
        news_filter=news_filter,
        direction=direction,
        current_price=current_price,
        pair=config["pair"],
        chart_timeframe=config["timeframe"],
    )

    if not isinstance(strategy, StrategyBase):
        raise TypeError(f"{strategy_name} must inherit from StrategyBase")

    # --- Step 4: Run strategy ---
    try:
        strategy.run(stop_flag=config.get("stop_flag"))
        print(f"[INFO] Strategy '{strategy_name}' launched successfully.")
        if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
            gui_parent.strategy_error_signal.emit(
                f"Strategy '{strategy_name}' is now running."
            )
    except Exception as e:
        print(f"[ERROR] Strategy '{strategy_name}' failed to execute: {e}")
        if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
            gui_parent.strategy_error_signal.emit(f"Error: {str(e)}")

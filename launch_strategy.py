# launch_strategy.py
import os
import glob
import threading
from threading import Event
from PySide6.QtCore import Qt
from main import run_strategy
from utils.price_tools import fetch_current_price
from backtest import run_backtest

stop_flag = Event()


def load_strategies(self):
    strategy_path = os.path.join(os.path.dirname(__file__), "strategies")
    if not os.path.isdir(strategy_path):
        strategy_path = os.path.join(os.path.dirname(__file__), "strategies")

    pattern = os.path.join(strategy_path, "*.py")
    files = glob.glob(pattern)

    strategies = [
        os.path.splitext(os.path.basename(f))[0]
        for f in files
        if not os.path.basename(f).startswith("__")
        and os.path.basename(f).lower() != "base_strategy.py"
    ]

    self.strategy_dropdown.clear()
    self.strategy_dropdown.addItems(strategies)


def launch_strategy(self, stop_flag=None, gui_parent=None):
    token = self.token_input.text().strip()
    account_id = self.account_id_input.text().strip()
    environment = self.env_dropdown.currentText()
    instrument = self.pair_dropdown.currentText()

    try:
        current_price = fetch_current_price(token, account_id, environment, instrument)
    except Exception as e:
        if gui_parent and hasattr(gui_parent, "strategy_error_signal"):
            gui_parent.strategy_error_signal.emit(
                f"[PRICE ERROR] Could Not Fetch Current Price {e}"
            )
        return

    trade_direction = self.direction_dropdown.currentText()
    if trade_direction.startswith("Buy"):
        direction = "Buy"
    elif trade_direction.startswith("Sell"):
        direction = "Sell"
    else:
        direction = "Both"  # Strategy decides at runtime

    config = {
        "account_id": account_id,
        "token": token,
        "environment": environment,
        "strategy": self.strategy_dropdown.currentText(),
        "risk_per_trade": self.risk_input.text(),
        "max_drawdown": self.drawdown_input.text(),
        "trade_direction": trade_direction,
        "start_time": self.start_input.dateTime().toString(Qt.ISODate),
        "end_time": self.end_input.dateTime().toString(Qt.ISODate),
        "news_buffer": self.news_buffer_input.text(),
        "news_impact": {
            "high": self.news_high.isChecked(),
            "medium": self.news_med.isChecked(),
            "low": self.news_low.isChecked(),
        },
        "finnhub_api_key": self.finnhub_api_input.text().strip(),
        "news_filter_quote_currency": self.news_quote_checkbox.isChecked(),
        "pair": instrument,
        "timeframe": self.timeframe_dropdown.currentText(),
        "stop_flag": stop_flag,
        "sl_strategy": self.sl_strategy_combo.currentText(),
        "tp_strategy": self.tp_strategy_combo.currentText(),
        "sl_pips": self.sl_pips_input.text(),
        "trailing_distance": self.trailing_distance_input.text(),
        "ema_period": self.ema_period_input.text(),
        "tp_pips": self.tp_pips_input.text(),
        "rr_ratio": self.rr_ratio_input.text(),
        "run_mode": self.run_mode_dropdown.currentText(),
        "current_price": current_price,
        "direction": direction,
    }

    def run_in_thread():
        try:
            if config["run_mode"] == "Live":
                run_strategy(config, gui_parent=None)
            else:  # --- NEW ---
                results = run_backtest(config, candle_count=1000)

                # 👉 emit a Qt signal with `results`
                if hasattr(self, "backtest_results_signal"):
                    self.backtest_results_signal.emit(results)
        except Exception as e:
            if hasattr(self, "strategy_error_signal"):
                self.strategy_error_signal.emit(str(e))

    threading.Thread(target=run_in_thread, daemon=True).start()

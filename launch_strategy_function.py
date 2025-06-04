import os
import glob
import importlib
from PySide6.QtWidgets import QMessageBox
from main import run_strategy
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.pricing import PricingInfo
from PySide6.QtCore import Qt
from utils.price_tools import fetch_current_price


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


def launch_strategy(self):
    token = self.token_input.text().strip()
    account_id = self.account_id_input.text().strip()
    environment = self.env_dropdown.currentText()
    instrument = self.pair_dropdown.currentText()

    try:
        current_price = fetch_current_price(token, account_id, environment, instrument)
    except Exception as e:
        QMessageBox.critical(
            self, "Price Fetch Error", f"Failed to get current price: {e}"
        )
        return

    trade_direction = self.direction_dropdown.currentText().lower()
    if trade_direction.startswith("buy"):
        direction = "buy"
    elif trade_direction.startswith("sell"):
        direction = "sell"
    else:
        direction = None  # Strategy decides at runtime

    config = {
        "account_id": account_id,
        "token": token,
        "environment": environment,
        "strategy": self.strategy_dropdown.currentText(),
        # Add additional parameters from your GUI
        "risk_per_trade": self.risk_input.text(),
        "max_drawdown": self.drawdown_input.text(),
        "trade_direction": self.direction_dropdown.currentText(),
        "start_time": self.start_input.dateTime().toString(Qt.ISODate),
        "end_time": self.end_input.dateTime().toString(Qt.ISODate),
        "news_buffer": self.news_buffer_input.text(),
        "news_impact": {
            "high": self.news_high.isChecked(),
            "medium": self.news_med.isChecked(),
            "low": self.news_low.isChecked(),
        },
        "pair": instrument,
        "timeframe": self.timeframe_dropdown.currentText(),
        # SL and TP strategy selections
        "sl_strategy": self.sl_strategy_combo.currentText(),
        "tp_strategy": self.tp_strategy_combo.currentText(),
        "sl_pips": self.sl_pips_input.text(),
        "trailing_distance": self.trailing_distance_input.text(),
        "ema_period": self.ema_period_input.text(),
        "tp_pips": self.tp_pips_input.text(),
        "rr_ratio": self.rr_ratio_input.text(),
        "run_mode": self.run_mode_dropdown.currentText(),
        # Real-time price info
        "current_price": current_price,
        "direction": direction,  # May be None if "Both" selected
    }

    try:
        if config["run_mode"] == "Live":
            run_strategy(config)
        else:
            QMessageBox.information(self, "Backtest", "Backtest not implemented yet.")
    except Exception as e:
        QMessageBox.critical(self, "Strategy Error", str(e))

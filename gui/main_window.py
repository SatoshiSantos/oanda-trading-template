# gui/main_window.py

from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails, AccountInstruments
from oandapyV20.exceptions import V20Error
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QMessageBox,
    QDateTimeEdit,
    QCheckBox,
    QGridLayout,
)
from PySide6.QtCore import QDateTime, Qt
import sys
from launch_strategy import load_strategies, launch_strategy
from utils.trade_tools import close_all_positions
import json
import os
from threading import Thread


# Load user_config.json file for persistance
CONFIG_PATH = os.path.join("config", "user_config.json")


def load_config_from_file():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


# Save user_config.json file for persistance
def save_config_to_file(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.start_requested = False
        self.stop_requested = False
        self.API_connected = False

        self.setWindowTitle("OANDA Trading App")

        main_layout = QVBoxLayout()

        # --- Group 1: API & Connection ---
        api_group = QGroupBox("OANDA API Credentials")
        api_layout = QGridLayout()
        self.token_label = QLabel("API Token:")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.account_id_label = QLabel("Account ID:")
        self.account_id_input = QLineEdit()
        self.env_label = QLabel("Environment:")
        self.env_dropdown = QComboBox()
        self.env_dropdown.addItems(["practice", "live"])
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_oanda)
        api_layout.addWidget(self.token_label, 0, 0)
        api_layout.addWidget(self.token_input, 0, 1)
        api_layout.addWidget(self.account_id_label, 1, 0)
        api_layout.addWidget(self.account_id_input, 1, 1)
        api_layout.addWidget(self.env_label, 2, 0)
        api_layout.addWidget(self.env_dropdown, 2, 1)
        api_layout.addWidget(self.connect_button, 3, 0, 1, 2)
        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)

        # --- Group 2: Trade Configuration ---
        trade_group = QGroupBox("Trade Configuration")
        trade_layout = QGridLayout()
        self.pair_label = QLabel("Trading Pair:")
        self.pair_dropdown = QComboBox()
        self.pair_dropdown.setEnabled(False)
        self.timeframe_label = QLabel("Time Frame:")
        self.timeframe_dropdown = QComboBox()
        self.timeframe_dropdown.addItems(
            ["M1", "M5", "M15", "M30", "H1", "H4", "D", "W", "M"]
        )
        self.strategy_label = QLabel("Select Strategy:")
        self.strategy_dropdown = QComboBox()
        load_strategies(self)
        self.run_mode_label = QLabel("Run Mode:")
        self.run_mode_dropdown = QComboBox()
        self.run_mode_dropdown.addItems(["Live", "Backtest"])
        trade_layout.addWidget(self.pair_label, 0, 0)
        trade_layout.addWidget(self.pair_dropdown, 0, 1)
        trade_layout.addWidget(self.timeframe_label, 1, 0)
        trade_layout.addWidget(self.timeframe_dropdown, 1, 1)
        trade_layout.addWidget(self.strategy_label, 2, 0)
        trade_layout.addWidget(self.strategy_dropdown, 2, 1)
        trade_layout.addWidget(self.run_mode_label, 3, 0)
        trade_layout.addWidget(self.run_mode_dropdown, 3, 1)
        trade_group.setLayout(trade_layout)
        main_layout.addWidget(trade_group)

        # --- Group 3: Risk Settings ---
        risk_group = QGroupBox("Risk Management")
        risk_layout = QGridLayout()
        self.risk_label = QLabel("Risk per Trade (%):")
        self.risk_input = QLineEdit()
        self.risk_input.setPlaceholderText("e.g., 1.0")
        self.drawdown_label = QLabel("Max Daily Drawdown (%):")
        self.drawdown_input = QLineEdit()
        self.drawdown_input.setPlaceholderText("e.g., 5.0")
        self.direction_label = QLabel("Trade Direction:")
        self.direction_dropdown = QComboBox()
        self.direction_dropdown.addItems(["Buy only", "Sell only", "Both"])
        risk_layout.addWidget(self.risk_label, 0, 0)
        risk_layout.addWidget(self.risk_input, 0, 1)
        risk_layout.addWidget(self.drawdown_label, 1, 0)
        risk_layout.addWidget(self.drawdown_input, 1, 1)
        risk_layout.addWidget(self.direction_label, 2, 0)
        risk_layout.addWidget(self.direction_dropdown, 2, 1)
        risk_group.setLayout(risk_layout)
        main_layout.addWidget(risk_group)

        # --- Group 4: Trading Schedule & News ---
        schedule_group = QGroupBox("Trading Schedule & News Filters")
        schedule_layout = QGridLayout()
        self.start_label = QLabel("Trading Start Time:")
        self.start_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_label = QLabel("Trading End Time:")
        self.end_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.news_buffer_label = QLabel("Minutes to Avoid Before/After News:")
        self.news_buffer_input = QLineEdit()
        self.news_buffer_input.setPlaceholderText("e.g., 15")
        self.news_impact_label = QLabel("News Impact Filter:")
        self.news_high = QCheckBox("High")
        self.news_med = QCheckBox("Medium")
        self.news_low = QCheckBox("Low")
        self.news_high.stateChanged.connect(self.update_news_inputs_visibility)
        self.news_med.stateChanged.connect(self.update_news_inputs_visibility)
        self.news_low.stateChanged.connect(self.update_news_inputs_visibility)
        self.finnhub_api_label = QLabel("Finnhub API Key:")
        self.finnhub_api_input = QLineEdit()
        self.news_quote_checkbox = QCheckBox("Filter by Quote Currency Too")
        self.finnhub_api_label.setVisible(False)
        self.finnhub_api_input.setVisible(False)
        self.news_quote_checkbox.setVisible(False)
        news_impact_row = QHBoxLayout()
        news_impact_row.addWidget(self.news_high)
        news_impact_row.addWidget(self.news_med)
        news_impact_row.addWidget(self.news_low)
        schedule_layout.addWidget(self.finnhub_api_label, 4, 0)
        schedule_layout.addWidget(self.finnhub_api_input, 4, 1)
        schedule_layout.addWidget(self.news_quote_checkbox, 5, 1)
        schedule_layout.addWidget(self.start_label, 0, 0)
        schedule_layout.addWidget(self.start_input, 0, 1)
        schedule_layout.addWidget(self.end_label, 1, 0)
        schedule_layout.addWidget(self.end_input, 1, 1)
        schedule_layout.addWidget(self.news_buffer_label, 2, 0)
        schedule_layout.addWidget(self.news_buffer_input, 2, 1)
        schedule_layout.addWidget(self.news_impact_label, 3, 0)
        schedule_layout.addLayout(news_impact_row, 3, 1)
        schedule_group.setLayout(schedule_layout)
        main_layout.addWidget(schedule_group)

        # --- Group 5: SL/TP Settings ---
        sltp_group = QGroupBox("Stop Loss & Take Profit Settings")
        sltp_layout = QGridLayout()
        self.sl_strategy_label = QLabel("Stop Loss Strategy:")
        self.sl_strategy_combo = QComboBox()
        self.sl_strategy_combo.addItems(
            ["Fixed SL (pips)", "Trailing SL", "EMA-Based SL"]
        )
        self.sl_strategy_combo.currentTextChanged.connect(self.update_sl_inputs)
        self.sl_pips_input = QLineEdit()
        self.sl_pips_input.setPlaceholderText("SL (pips)")
        self.trailing_distance_input = QLineEdit()
        self.trailing_distance_input.setPlaceholderText("Trailing SL Distance (pips)")
        self.ema_period_input = QLineEdit()
        self.ema_period_input.setPlaceholderText("EMA Period")
        self.tp_strategy_label = QLabel("Take Profit Strategy:")
        self.tp_strategy_combo = QComboBox()
        self.tp_strategy_combo.addItems(["Fixed TP (pips)", "Risk:Reward Ratio"])
        self.tp_strategy_combo.currentTextChanged.connect(self.update_tp_inputs)
        self.tp_pips_input = QLineEdit()
        self.tp_pips_input.setPlaceholderText("TP (pips)")
        self.rr_ratio_input = QLineEdit()
        self.rr_ratio_input.setPlaceholderText("Risk:Reward Ratio (e.g., 1:2)")
        sltp_layout.addWidget(self.sl_strategy_label, 0, 0)
        sltp_layout.addWidget(self.sl_strategy_combo, 0, 1)
        sltp_layout.addWidget(self.sl_pips_input, 1, 0, 1, 2)
        sltp_layout.addWidget(self.trailing_distance_input, 2, 0, 1, 2)
        sltp_layout.addWidget(self.ema_period_input, 3, 0, 1, 2)
        sltp_layout.addWidget(self.tp_strategy_label, 4, 0)
        sltp_layout.addWidget(self.tp_strategy_combo, 4, 1)
        sltp_layout.addWidget(self.tp_pips_input, 5, 0, 1, 2)
        sltp_layout.addWidget(self.rr_ratio_input, 6, 0, 1, 2)
        sltp_group.setLayout(sltp_layout)
        main_layout.addWidget(sltp_group)

        # --- Launch Button ---
        self.launch_button = QPushButton("Start")
        self.launch_button.clicked.connect(self.handle_launch)
        main_layout.addWidget(self.launch_button)
        # --- Stop Button ---
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.handle_stop)
        main_layout.addWidget(self.stop_button)
        # --- Close All Trades Button ---
        self.close_all_trades_button = QPushButton("close all trades")
        self.close_all_trades_button.clicked.connect(self.handle_close_all_trades)
        main_layout.addWidget(self.close_all_trades_button)

        # Load saved config data
        self.load_user_config()

        # Set main window layout
        self.setLayout(main_layout)

        # update inputs
        self.update_sl_inputs()
        self.update_tp_inputs()
        self.update_news_inputs_visibility()

    def update_news_inputs_visibility(self):
        any_checked = (
            self.news_high.isChecked()
            or self.news_med.isChecked()
            or self.news_low.isChecked()
        )
        self.finnhub_api_label.setVisible(any_checked)
        self.finnhub_api_input.setVisible(any_checked)
        self.news_quote_checkbox.setVisible(any_checked)

    def update_sl_inputs(self):
        self.sl_pips_input.setVisible(False)
        self.trailing_distance_input.setVisible(False)
        self.ema_period_input.setVisible(False)
        choice = self.sl_strategy_combo.currentText()
        if choice == "Fixed SL (pips)":
            self.sl_pips_input.setVisible(True)
        elif choice == "Trailing SL":
            self.trailing_distance_input.setVisible(True)
        elif choice == "EMA-Based SL":
            self.ema_period_input.setVisible(True)

    def update_tp_inputs(self):
        self.tp_pips_input.setVisible(False)
        self.rr_ratio_input.setVisible(False)
        choice = self.tp_strategy_combo.currentText()
        if choice == "Fixed TP (pips)":
            self.tp_pips_input.setVisible(True)
        elif choice == "Risk:Reward Ratio":
            self.rr_ratio_input.setVisible(True)

    def connect_to_oanda(self):
        token = self.token_input.text().strip()
        account_id = self.account_id_input.text().strip()
        environment = self.env_dropdown.currentText()
        if not token or not account_id:
            QMessageBox.warning(
                self, "Missing Info", "Please enter both token and account ID."
            )
            return
        try:
            client = API(access_token=token, environment=environment)
            response = client.request(AccountDetails(accountID=account_id))
            instruments = client.request(AccountInstruments(accountID=account_id))
            self.pair_dropdown.clear()
            for inst in instruments["instruments"]:
                self.pair_dropdown.addItem(inst["name"])
            self.pair_dropdown.setEnabled(True)
            QMessageBox.information(
                self,
                "Connected",
                f"Connected to OANDA. Balance: {response['account']['balance']}",
            )
            self.API_connected = True
        except V20Error as e:
            QMessageBox.critical(self, "Connection Error", str(e))

    # load saved user config from json file to the gui
    def load_user_config(self):
        config = load_config_from_file()

        self.token_input.setText(config.get("token", ""))
        self.account_id_input.setText(config.get("account_id", ""))
        self.env_dropdown.setCurrentText(config.get("environment", "practice"))
        self.pair_dropdown.setCurrentText(config.get("pair", "EUR_USD"))
        self.timeframe_dropdown.setCurrentText(config.get("timeframe", "M15"))
        self.strategy_dropdown.setCurrentText(config.get("strategy", "ExampleStrategy"))
        self.run_mode_dropdown.setCurrentText(config.get("run_mode", "Live"))

        self.risk_input.setText(str(config.get("risk_per_trade", "")))
        self.drawdown_input.setText(str(config.get("max_drawdown", "")))
        self.direction_dropdown.setCurrentText(config.get("trade_direction"))

        self.start_input.setDateTime(
            QDateTime.fromString(
                config.get("start_time", QDateTime.currentDateTime().toString())
            )
        )
        self.end_input.setDateTime(
            QDateTime.fromString(
                config.get("end_time", QDateTime.currentDateTime().toString())
            )
        )
        self.news_buffer_input.setText(str(config.get("news_buffer_minutes", "")))

        self.news_high.setChecked(config.get("news_impact", {}).get("high", False))
        self.news_med.setChecked(config.get("news_impact", {}).get("medium", False))
        self.news_low.setChecked(config.get("news_impact", {}).get("low", False))

        self.sl_strategy_combo.setCurrentText(
            config.get("sl_strategy", "Fixed SL (pips)")
        )

        self.sl_pips_input.setText(config.get("sl_pips", ""))
        self.trailing_distance_input.setText(config.get("trailing_distance", ""))
        self.ema_period_input.setText(config.get("ema_period", ""))
        self.tp_strategy_combo.setCurrentText(
            config.get("tp_strategy", "Fixed TP (pips)")
        )
        self.tp_pips_input.setText(config.get("tp_pips", ""))
        self.rr_ratio_input.setText(config.get("rr_ratio", ""))

        self.finnhub_api_input.setText(config.get("finnhub_api_key", ""))
        self.news_quote_checkbox.setChecked(
            config.get("news_filter_quote_currency", False)
        )

        self.update_news_inputs_visibility()
        self.update_sl_inputs()
        self.update_tp_inputs()

    """
    handle_launch(self): & save_user_config(self): save user config at 
    
    launch When the GUI opens, the users previous settings auto-populate.

    When the user clicks "Start", the current settings are saved.

    No manual user interaction is needed to load or save.
    """

    def handle_launch(self):
        self.stop_requested = False  # Reset stop flag
        self.start_requested = True  # Set start flag
        self.save_user_config()  # save user config

        # Run strategy in a new thread so GUI doesn't freeze
        def background_launch():
            launch_strategy(self, stop_flag=lambda: self.stop_requested)

        Thread(target=background_launch).start()

    def handle_stop(self):
        if self.start_requested:  # Check if strategy launched
            self.stop_requested = True  # set stop flag
            QMessageBox.information(
                self, "Strategy Halt", "Stop requested. Strategy terminate."
            )
            self.start_requested = False  # Reset start flag
        else:
            QMessageBox.information(
                self, "Stop Requested: Error", "Strategy has not been launched."
            )

    def save_user_config(self):
        config = {
            "token": self.token_input.text().strip(),
            "account_id": self.account_id_input.text().strip(),
            "environment": self.env_dropdown.currentText(),
            "pair": self.pair_dropdown.currentText(),
            "timeframe": self.timeframe_dropdown.currentText(),
            "strategy": self.strategy_dropdown.currentText(),
            "run_mode": self.run_mode_dropdown.currentText(),
            "risk_per_trade": self.risk_input.text().strip(),
            "max_drawdown": self.drawdown_input.text().strip(),
            "trade_direction": self.direction_dropdown.currentText(),
            "start_time": self.start_input.dateTime().toString(),
            "end_time": self.end_input.dateTime().toString(),
            "news_buffer_minutes": self.news_buffer_input.text().strip(),
            "news_impact": {
                "high": self.news_high.isChecked(),
                "medium": self.news_med.isChecked(),
                "low": self.news_low.isChecked(),
            },
            "finnhub_api_key": self.finnhub_api_input.text().strip(),
            "news_filter_quote_currency": self.news_quote_checkbox.isChecked(),
            "sl_strategy": self.sl_strategy_combo.currentText(),
            "sl_pips": self.sl_pips_input.text().strip(),
            "trailing_distance": self.trailing_distance_input.text().strip(),
            "ema_period": self.ema_period_input.text().strip(),
            "tp_strategy": self.tp_strategy_combo.currentText(),
            "tp_pips": self.tp_pips_input.text().strip(),
            "rr_ratio": self.rr_ratio_input.text().strip(),
        }

        save_config_to_file(config)

    def handle_close_all_trades(self):
        if self.API_connected:
            token = self.token_input.text().strip()
            account_id = self.account_id_input.text().strip()
            environment = self.env_dropdown.currentText()

            if not token or not account_id:
                QMessageBox.warning(
                    self, "Missing Info", "Please enter API token and account ID."
                )
                return

            closed = close_all_positions(token, account_id, environment)

            if closed:
                QMessageBox.information(
                    self, "Success", f"Closed {len(closed)} open position(s)."
                )
            else:
                QMessageBox.information(
                    self, "No Positions", "No open positions were found."
                )
        else:
            QMessageBox.information(
                self, "Close All Trades: Error", "API not connected."
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

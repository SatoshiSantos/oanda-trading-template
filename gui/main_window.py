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
from launch_strategy_function import load_strategies, launch_strategy


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
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
        self.news_high.setChecked(True)
        news_impact_row = QHBoxLayout()
        news_impact_row.addWidget(self.news_high)
        news_impact_row.addWidget(self.news_med)
        news_impact_row.addWidget(self.news_low)
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
        self.launch_button.clicked.connect(lambda: launch_strategy(self))
        main_layout.addWidget(self.launch_button)

        self.setLayout(main_layout)
        self.update_sl_inputs()
        self.update_tp_inputs()

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
        except V20Error as e:
            QMessageBox.critical(self, "Connection Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

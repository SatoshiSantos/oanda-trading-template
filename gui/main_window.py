# gui/main_window.py
from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails
from oandapyV20.exceptions import V20Error
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QMessageBox,
    QDateTimeEdit,
    QCheckBox,
    QHBoxLayout,
)
from PySide6.QtCore import QDateTime  # , Qt
import sys

# import requests


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OANDA Login")

        # --- Widgets ---
        # Account API Toen
        self.token_label = QLabel("API Token:")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        # account ID
        self.account_id_label = QLabel("Account ID:")
        self.account_id_input = QLineEdit()
        # Account Env
        self.env_label = QLabel("Environment:")
        self.env_dropdown = QComboBox()
        self.env_dropdown.addItems(["practice", "live"])
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_oanda)
        # Max risk per trade
        self.risk_label = QLabel("Risk per Trade (%):")
        self.risk_input = QLineEdit()
        self.risk_input.setPlaceholderText("e.g., 1.0")
        # Max daily drawdown
        self.drawdown_label = QLabel("Max Daily Drawdown (%):")
        self.drawdown_input = QLineEdit()
        self.drawdown_input.setPlaceholderText("e.g., 5.0")
        # Trade Long/Short
        self.direction_label = QLabel("Trade Direction:")
        self.direction_dropdown = QComboBox()
        self.direction_dropdown.addItems(["Buy only", "Sell only", "Both"])
        # Trading start time
        self.start_label = QLabel("Trading Start Time:")
        self.start_input = QDateTimeEdit()
        self.start_input.setDateTime(QDateTime.currentDateTime())
        # Trading end time
        self.end_label = QLabel("Trading End Time:")
        self.end_input = QDateTimeEdit()
        self.end_input.setDateTime(QDateTime.currentDateTime())
        # News time buffer
        self.news_buffer_label = QLabel("Minutes to Avoid Before/After News:")
        self.news_buffer_input = QLineEdit()
        self.news_buffer_input.setPlaceholderText("e.g., 15")
        # News Impact filter
        self.news_impact_label = QLabel("News Impact Filter:")
        self.news_high = QCheckBox("High")
        self.news_med = QCheckBox("Medium")
        self.news_low = QCheckBox("Low")
        self.news_high.setChecked(True)
        self.news_med.setChecked(False)
        self.news_low.setChecked(False)

        # Horizontal layout for checkboxes
        self.news_impact_layout = QHBoxLayout()
        self.news_impact_layout.addWidget(self.news_high)
        self.news_impact_layout.addWidget(self.news_med)
        self.news_impact_layout.addWidget(self.news_low)

        # Stop Loss Selector
        self.sl_strategy_label = QLabel("Stop Loss Strategy:")
        self.sl_strategy_combo = QComboBox()
        self.sl_strategy_combo.addItems(
            ["Fixed SL (pips)", "Trailing SL", "EMA-Based SL"]
        )

        # Take Profit Selector
        self.tp_strategy_label = QLabel("Take Profit Strategy:")
        self.tp_strategy_combo = QComboBox()
        self.tp_strategy_combo.addItems(["Fixed TP (pips)", "Risk:Reward Ratio"])

        # Connect strategy dropdowns to handlers
        self.sl_strategy_combo.currentTextChanged.connect(self.update_sl_inputs)
        self.tp_strategy_combo.currentTextChanged.connect(self.update_tp_inputs)

        # SL inputs
        self.sl_pips_input = QLineEdit()
        self.sl_pips_input.setPlaceholderText("SL (pips)")

        self.trailing_distance_input = QLineEdit()
        self.trailing_distance_input.setPlaceholderText("Trailing SL Distance (pips)")

        self.ema_period_input = QLineEdit()
        self.ema_period_input.setPlaceholderText("EMA Period")

        # TP inputs
        self.tp_pips_input = QLineEdit()
        self.tp_pips_input.setPlaceholderText("TP (pips)")

        self.rr_ratio_input = QLineEdit()
        self.rr_ratio_input.setPlaceholderText("Risk:Reward Ratio (e.g., 1:2)")

        # --- Layout ---
        layout = QVBoxLayout()
        # API Input
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_input)
        # Account Id Input
        layout.addWidget(self.account_id_label)
        layout.addWidget(self.account_id_input)
        # Envinronemt dropdown(real, practice)
        layout.addWidget(self.env_label)
        layout.addWidget(self.env_dropdown)
        # connect button
        layout.addWidget(self.connect_button)
        # Risk & Trade Config
        layout.addWidget(self.risk_label)
        layout.addWidget(self.risk_input)
        layout.addWidget(self.drawdown_label)
        layout.addWidget(self.drawdown_input)
        layout.addWidget(self.direction_label)
        layout.addWidget(self.direction_dropdown)
        # Date range
        layout.addWidget(self.start_label)
        layout.addWidget(self.start_input)
        layout.addWidget(self.end_label)
        layout.addWidget(self.end_input)
        # News Event Filter
        layout.addWidget(self.news_buffer_label)
        layout.addWidget(self.news_buffer_input)
        layout.addWidget(self.news_impact_label)
        layout.addLayout(self.news_impact_layout)
        # TP/SL strategy
        layout.addWidget(self.sl_strategy_label)
        layout.addWidget(self.sl_strategy_combo)
        layout.addWidget(self.tp_strategy_label)
        layout.addWidget(self.tp_strategy_combo)
        # SL strategy inputs
        layout.addWidget(self.sl_pips_input)
        layout.addWidget(self.trailing_distance_input)
        layout.addWidget(self.ema_period_input)
        # TP strategy inputs
        layout.addWidget(self.tp_pips_input)
        layout.addWidget(self.rr_ratio_input)

        # Initialize with correct SL/TP visibility
        self.update_sl_inputs()
        self.update_tp_inputs()

        self.setLayout(layout)

    # Function to handle SL strategy change (Class Mehod)
    def update_sl_inputs(self):
        sl_choice = self.sl_strategy_combo.currentText()

        self.sl_pips_input.setVisible(False)
        self.trailing_distance_input.setVisible(False)
        self.ema_period_input.setVisible(False)

        if sl_choice == "Fixed SL (pips)":
            self.sl_pips_input.setVisible(True)
        elif sl_choice == "Trailing SL":
            self.trailing_distance_input.setVisible(True)
        elif sl_choice == "EMA-Based SL":
            self.ema_period_input.setVisible(True)

    # Function to handle TP strategy change (Class Method)
    def update_tp_inputs(self):
        tp_choice = self.tp_strategy_combo.currentText()

        self.tp_pips_input.setVisible(False)
        self.rr_ratio_input.setVisible(False)

        if tp_choice == "Fixed TP (pips)":
            self.tp_pips_input.setVisible(True)
        elif tp_choice == "Risk:Reward Ratio":
            self.rr_ratio_input.setVisible(True)

    # Oanda API Connection (Class Method)
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
            request = AccountDetails(accountID=account_id)
            response = client.request(request)

            # You can extract info like balance here if needed
            balance = response["account"]["balance"]
            id = response["account"]["id"]
            currency = response["account"]["currency"]
            marginAvailable = response["account"]["marginAvailable"]

            QMessageBox.information(
                self,
                "Connected",
                f"Connection successful!\nBalance: {balance}"
                f"\nAccount ID: {id}\nCurrency: {currency}"
                f"\nAvailable Margin: {marginAvailable}",
            )
        except V20Error as e:
            QMessageBox.critical(self, "Connection Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

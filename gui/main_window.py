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
)
from PySide6.QtWidgets import QDateTimeEdit, QCheckBox, QHBoxLayout
from PySide6.QtCore import QDateTime
import sys

# import requests


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OANDA Login")

        # --- Widgets ---
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

        self.risk_label = QLabel("Risk per Trade (%):")
        self.risk_input = QLineEdit()
        self.risk_input.setPlaceholderText("e.g., 1.0")

        self.drawdown_label = QLabel("Max Daily Drawdown (%):")
        self.drawdown_input = QLineEdit()
        self.drawdown_input.setPlaceholderText("e.g., 5.0")

        self.direction_label = QLabel("Trade Direction:")
        self.direction_dropdown = QComboBox()
        self.direction_dropdown.addItems(["Buy only", "Sell only", "Both"])

        self.start_label = QLabel("Trading Start Time:")
        self.start_input = QDateTimeEdit()
        self.start_input.setDateTime(QDateTime.currentDateTime())

        self.end_label = QLabel("Trading End Time:")
        self.end_input = QDateTimeEdit()
        self.end_input.setDateTime(QDateTime.currentDateTime())

        self.news_buffer_label = QLabel("Minutes to Avoid Before/After News:")
        self.news_buffer_input = QLineEdit()
        self.news_buffer_input.setPlaceholderText("e.g., 15")

        self.news_impact_label = QLabel("News Impact Filter:")
        self.news_high = QCheckBox("High")
        self.news_med = QCheckBox("Medium")
        self.news_low = QCheckBox("Low")
        self.news_high.setChecked(True)
        self.news_med.setChecked(True)
        self.news_low.setChecked(False)

        # Horizontal layout for checkboxes
        self.news_impact_layout = QHBoxLayout()
        self.news_impact_layout.addWidget(self.news_high)
        self.news_impact_layout.addWidget(self.news_med)
        self.news_impact_layout.addWidget(self.news_low)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_input)
        layout.addWidget(self.account_id_label)
        layout.addWidget(self.account_id_input)
        layout.addWidget(self.env_label)
        layout.addWidget(self.env_dropdown)
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

        self.setLayout(layout)

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
                f"Account ID: {id}\nCurrency: {currency}"
                f"Available Margin: {marginAvailable}",
            )
        except V20Error as e:
            QMessageBox.critical(self, "Connection Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

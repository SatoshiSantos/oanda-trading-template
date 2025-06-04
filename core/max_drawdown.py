import os
import json
from datetime import date
from oandapyV20.endpoints.accounts import AccountSummary


class MaxDrawdownChecker:
    def __init__(self, config, client):
        self.account_id = config["account_id"]
        self.max_drawdown_amount = float(config.get("max_drawdown"))
        self.client = client
        self.storage_path = "config/daily_balances.json"
        self.today = str(date.today())
        self._load_or_initialize_day_balance()

    def _load_or_initialize_day_balance(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                self.daily_data = json.load(f)
        else:
            self.daily_data = {}

        if self.today not in self.daily_data:
            current_balance = self._fetch_account_balance()
            self.daily_data[self.today] = current_balance
            self._save_data()

    def _fetch_account_balance(self):
        request = AccountSummary(accountID=self.account_id)
        response = self.client.request(request)
        return float(response["account"]["balance"])

    def _save_data(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.daily_data, f, indent=2)

    def is_drawdown_exceeded(self):
        current_balance = self._fetch_account_balance()
        starting_balance = self.daily_data[self.today]
        drawdown = starting_balance - current_balance
        return drawdown >= self.max_drawdown_amount

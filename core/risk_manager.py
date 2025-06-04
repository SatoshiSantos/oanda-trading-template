from utils.price_tools import get_pip_value
from utils.account_tools import get_account_details

"""
Use dynamic stop loss distance: by computing pip distance between entry_price and stop_loss_price.

Raise detailed errors for missing or invalid config keys like account_balance and risk_per_trade.

Return position size in units as expected by OANDA (not lots or fractional values).
"""


class RiskManager:
    def __init__(self, config):
        self.config = config

        try:
            self.account_balance = float(self.config["account_balance"])
        except KeyError:
            raise ValueError("[RiskManager] 'account_balance' is required in config.")
        except ValueError:
            raise ValueError("[RiskManager] 'account_balance' must be a valid number.")

        try:
            self.risk_per_trade = (
                float(config["risk_per_trade"]) / 100.0
            )  # Convert % to decimal
        except KeyError:
            raise ValueError("[RiskManager] 'risk_per_trade' is required in config.")
        except ValueError:
            raise ValueError("[RiskManager] 'risk_per_trade' must be a Percentage.")

    def calculate_position_size(self, entry_price, stop_loss_price):
        if entry_price is None or stop_loss_price is None:
            raise ValueError(
                "[RiskManager] Entry price and stop loss price must be provided."
            )

        pip_value = get_pip_value(self.config.get("pair", ""))
        pip_distance = abs(entry_price - stop_loss_price) / pip_value

        if pip_distance == 0:
            raise ValueError(
                "[RiskManager] Stop loss pip distance is zero. Cannot calculate position size."
            )

        risk_amount = self.account_balance * self.risk_per_trade
        units = risk_amount / (pip_distance * pip_value)

        return int(units)  # OANDA expects trade size in units

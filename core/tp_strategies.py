# core/tp_strategies.py

from utils.price_tools import get_pip_value


class TakeProfitStrategy:
    def __init__(self, config):
        self.config = config

    def get_take_profit(self, entry_price, direction, stop_loss_price=None):
        strategy = self.config.get("tp_strategy", "Fixed TP (pips)")

        if strategy == "Fixed TP (pips)":
            return self.fixed_tp(entry_price, direction)
        elif strategy == "Risk:Reward Ratio":
            return self.risk_reward_tp(entry_price, direction, stop_loss_price)
        else:
            raise ValueError(f"[TP Strategy] Unknown take profit strategy: {strategy}")

    def fixed_tp(self, entry_price, direction):
        try:
            pips = float(self.config.get("tp_pips", 20))
        except ValueError:
            raise ValueError("[TP Strategy] Invalid 'tp_pips' value in config.")

        pip_value = get_pip_value(self.config.get("pair", ""))
        if direction == "buy":
            return round(entry_price + pips * pip_value, 5)
        else:
            return round(entry_price - pips * pip_value, 5)

    def risk_reward_tp(self, entry_price, direction, stop_loss_price):
        if stop_loss_price is None:
            raise ValueError(
                "[TP Strategy] Stop loss price is required for risk:reward TP."
            )

        ratio_str = self.config.get("rr_ratio", "1:2")
        try:
            risk, reward = map(float, ratio_str.split(":"))
        except Exception:
            raise ValueError(
                "[TP Strategy] Invalid Risk:Reward Ratio format (e.g., '1:2')"
            )

        pip_value = get_pip_value(self.config.get("pair", ""))
        risk_pips = abs(entry_price - stop_loss_price) / pip_value
        reward_pips = (reward / risk) * risk_pips

        if direction == "buy":
            return round(entry_price + reward_pips * pip_value, 5)
        else:
            return round(entry_price - reward_pips * pip_value, 5)

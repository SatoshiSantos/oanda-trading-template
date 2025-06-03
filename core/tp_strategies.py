# core/tp_strategies.py


class TakeProfitStrategy:
    def __init__(self, config):
        self.config = config

    def get_take_profit(self, entry_price, direction, stop_loss_price=None):
        tp_type = self.config.get("tp_strategy", "Fixed TP (pips)")

        if tp_type == "Fixed TP (pips)":
            tp_pips = float(self.config.get("tp_pips", 20))
            if direction == "buy":
                return entry_price + tp_pips * 0.0001
            else:
                return entry_price - tp_pips * 0.0001

        elif tp_type == "Risk:Reward Ratio":
            ratio_str = self.config.get("rr_ratio", "1:2")
            try:
                risk, reward = map(float, ratio_str.split(":"))
                risk_pips = abs(entry_price - stop_loss_price) / 0.0001
                reward_pips = (reward / risk) * risk_pips
                if direction == "buy":
                    return entry_price + reward_pips * 0.0001
                else:
                    return entry_price - reward_pips * 0.0001
            except Exception:
                raise ValueError("Invalid Risk:Reward Ratio format")

        else:
            raise ValueError(f"Unknown TP strategy: {tp_type}")

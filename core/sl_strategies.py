# core/sl_strategies.py


class StopLossStrategy:
    def __init__(self, config):
        self.config = config

    def get_stop_loss(self, current_price, direction):
        strategy = self.config.get("sl_strategy", "Fixed SL (pips)")

        if strategy == "Fixed SL (pips)":
            return self.fixed_sl(current_price, direction)
        elif strategy == "Trailing SL":
            return self.trailing_sl(current_price, direction)
        elif strategy == "EMA-Based SL":
            return self.ema_based_sl(current_price, direction)
        else:
            raise ValueError(f"Unknown SL strategy: {strategy}")

    def fixed_sl(self, current_price, direction):
        pips = float(self.config.get("sl_pips", 10))
        pip_value = 0.0001  # adjust for JPY pairs later if needed
        if direction == "buy":
            return current_price - (pips * pip_value)
        else:
            return current_price + (pips * pip_value)

    def trailing_sl(self, current_price, direction):
        distance = float(self.config.get("trailing_distance", 10))
        pip_value = 0.0001
        if direction == "buy":
            return current_price - (distance * pip_value)
        else:
            return current_price + (distance * pip_value)

    def ema_based_sl(self, current_price, direction):
        # Placeholder: actual implementation should use historical data to compute EMA
        ema_price = (
            current_price - 0.001 if direction == "buy" else current_price + 0.001
        )
        return ema_price

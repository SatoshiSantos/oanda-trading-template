class RiskManager:
    def __init__(self, config):
        self.config = config
        self.account_balance = config.get("account_balance", 10000.0)  # fallback
        self.risk_per_trade = (
            float(config.get("risk_per_trade", 1.0)) / 100.0
        )  # percent to decimal
        self.stop_loss_pips = float(config.get("stop_loss_pips", 10))  # fallback

    def calculate_position_size(self):
        pip_value = 0.0001  # For most USD pairs
        risk_amount = self.account_balance * self.risk_per_trade
        position_size = risk_amount / (self.stop_loss_pips * pip_value)

        return round(position_size, 2)

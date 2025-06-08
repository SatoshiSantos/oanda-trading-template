# trade_manager.py
# Create TradeManager base class and utility function to update stop loss

from oandapyV20 import API
from oandapyV20.endpoints.trades import TradeCRCDO
from typing import Optional, Dict
from logs.trade_logger import log_trade


class TradeManager:
    def __init__(self, client: API, account_id: str):
        self.client = client
        self.account_id = account_id
        self.active_trades: Dict[str, Dict] = {}  # key: trade_id, value: trade details

    def register_trade(self, trade_id: str, trade_info: Dict):
        self.active_trades[trade_id] = trade_info
        print(f"[TradeManager] Registered trade: {trade_id}")

        # Log to trade logger
        def register_trade(self, trade_id: str, trade_info: Dict):
            self.active_trades[trade_id] = trade_info
            print(f"[TradeManager] Registered trade: {trade_id}")
            log_trade(
                {
                    "trade_id": trade_id,
                    "instrument": trade_info["instrument"],
                    "direction": trade_info["direction"],
                    "units": trade_info["units"],
                    "entry_price": trade_info["entry_price"],
                    "stop_loss": trade_info["sl"],
                    "take_profit": trade_info["tp"],
                }
            )

    def update_stop_loss(
        self, trade_id: str, new_sl_price: float = None, new_tp_price: float = None
    ) -> bool:
        if not new_sl_price and not new_tp_price:
            print("[TradeManager] No SL or TP update provided.")
            return False

        data = {}
        if new_sl_price:
            data["stopLoss"] = {"price": str(round(new_sl_price, 5))}
        if new_tp_price:
            data["takeProfit"] = {"price": str(round(new_tp_price, 5))}

        try:
            r = TradeCRCDO(accountID=self.account_id, tradeID=trade_id, data=data)
            response = self.client.request(r)
            print(f"[TradeManager] Updated SL/TP for trade {trade_id}: {response}")
            return True
        except Exception as e:
            print(
                f"[TradeManager][ERROR] Failed to update SL/TP for trade {trade_id}: {e}"
            )
            return False

    def close_trade(self, trade_id: str) -> bool:
        # Placeholder: Will add logic with TradeClose endpoint if needed
        return False

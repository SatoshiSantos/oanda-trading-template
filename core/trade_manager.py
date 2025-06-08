from oandapyV20 import API
from oandapyV20.endpoints.trades import TradeCRCDO, TradeClose
from typing import Optional, Dict
from logs.trade_logger import log_trade
from datetime import datetime


class TradeManager:
    def __init__(self, client: API, account_id: str):
        self.client = client
        self.account_id = account_id
        self.active_trades: Dict[str, Dict] = {}  # key: trade_id, value: trade details

    def register_trade(self, trade_id: str, trade_info: Dict):
        self.active_trades[trade_id] = trade_info
        print(f"[TradeManager] Registered trade: {trade_id}")
        log_trade(
            {
                "trade_id": trade_id,
                "instrument": trade_info.get("instrument", ""),
                "direction": trade_info.get("direction", ""),
                "units": trade_info.get("units", ""),
                "entry_price": trade_info.get("entry_price", ""),
                "stop_loss": trade_info.get("stop_loss", ""),
                "take_profit": trade_info.get("take_profit", ""),
                "timestamp": trade_info.get("timestamp", datetime.utcnow().isoformat()),
                "type": trade_info.get("type", ""),
                "reason": trade_info.get("reason", ""),
                "timeInForce": trade_info.get("timeInForce", ""),
                "relatedTransactionIDs": str(
                    trade_info.get("relatedTransactionIDs", "")
                ),
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
        try:
            r = TradeClose(accountID=self.account_id, tradeID=trade_id)
            response = self.client.request(r)
            closed_info = self.active_trades.pop(trade_id, {})
            print(f"[TradeManager] Closed trade {trade_id}: {response}")

            if closed_info:
                closed_info["exit_time"] = datetime.utcnow().isoformat()
                closed_info["closed"] = True
                log_trade(closed_info)  # Re-log with closed status (optional)

            return True
        except Exception as e:
            print(f"[TradeManager][ERROR] Failed to close trade {trade_id}: {e}")
            return False

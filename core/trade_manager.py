# trade_manager.py

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
        trade_info["trade_id"] = trade_id  # Ensure ID is attached

        # Default values
        trade_info.setdefault("timestamp", datetime.utcnow().isoformat())
        trade_info.setdefault("exit_time", "")
        trade_info.setdefault("status", "")
        trade_info.setdefault("closed", False)
        trade_info.setdefault("log_type", "entry")

        log_trade(
            {
                "log_type": trade_info["log_type"],
                "timestamp": trade_info["timestamp"],
                "trade_id": trade_id,
                "instrument": trade_info.get("instrument", ""),
                "direction": trade_info.get("direction", ""),
                "units": trade_info.get("units", ""),
                "entry_price": trade_info.get("entry_price", ""),
                "stop_loss": trade_info.get("stop_loss", ""),
                "take_profit": trade_info.get("take_profit", ""),
                "type": trade_info.get("type", ""),
                "reason": trade_info.get("reason", ""),
                "timeInForce": trade_info.get("timeInForce", ""),
                "relatedTransactionIDs": ", ".join(
                    map(str, trade_info.get("relatedTransactionIDs", []))
                ),
                "status": trade_info["status"],
                "exit_time": trade_info["exit_time"],
                "closed": trade_info["closed"],
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
                # Ensure essential fields exist
                closed_info.setdefault("trade_id", trade_id)
                closed_info.setdefault("timestamp", datetime.utcnow().isoformat())
                closed_info.setdefault("instrument", "")
                closed_info.setdefault("direction", "")
                closed_info.setdefault("units", "")
                closed_info.setdefault("entry_price", "")
                closed_info.setdefault("stop_loss", "")
                closed_info.setdefault("take_profit", "")
                closed_info.setdefault("type", "MANUAL")
                closed_info.setdefault("reason", "MANUAL_CLOSE")
                closed_info.setdefault("timeInForce", "")
                closed_info["relatedTransactionIDs"] = ", ".join(
                    map(str, closed_info.get("relatedTransactionIDs", []))
                )
                closed_info["status"] = "manual_close_executed"
                closed_info["exit_time"] = datetime.utcnow().isoformat()
                closed_info["closed"] = True
                closed_info["log_type"] = "closed"

                log_trade(closed_info)

            return True
        except Exception as e:
            print(f"[TradeManager][ERROR] Failed to close trade {trade_id}: {e}")
            return False

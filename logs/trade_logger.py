# trade_logger.py

import csv
import os
from datetime import datetime

TRADE_LOG_PATH = os.path.join("logs", "trade_log.csv")


def log_trade(trade_info):
    # Set default fallback values
    trade_info.setdefault("timestamp", datetime.utcnow().isoformat())
    trade_info.setdefault("exit_time", "")
    trade_info.setdefault("status", "")
    trade_info.setdefault("closed", False)
    trade_info.setdefault("trade_id", "")

    # Ensure missing values don't break row
    fieldnames = [
        "log_type",
        "timestamp",
        "trade_id",
        "instrument",
        "direction",
        "units",
        "entry_price",
        "stop_loss",
        "take_profit",
        "type",
        "reason",
        "timeInForce",
        "relatedTransactionIDs",
        "status",
        "exit_time",
        "closed",
    ]

    file_exists = os.path.exists(TRADE_LOG_PATH)
    write_header = not file_exists or os.path.getsize(TRADE_LOG_PATH) == 0

    with open(TRADE_LOG_PATH, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        writer.writerow(trade_info)

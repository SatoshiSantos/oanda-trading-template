import csv
import os
from datetime import datetime

TRADE_LOG_PATH = os.path.join("logs", "trade_log.csv")


def log_trade(trade_data):
    fieldnames = [
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
    ]

    file_exists = os.path.exists(TRADE_LOG_PATH)
    write_header = not file_exists or os.path.getsize(TRADE_LOG_PATH) == 0

    with open(TRADE_LOG_PATH, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        writer.writerow(trade_data)

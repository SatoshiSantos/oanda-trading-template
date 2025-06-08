# logs/trade_logger.py

import csv
import os
from datetime import datetime

TRADE_LOG_PATH = os.path.join("logs", "trade_log.csv")


def log_trade(trade_data):
    file_exists = os.path.exists(TRADE_LOG_PATH)
    with open(TRADE_LOG_PATH, mode="a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "trade_id",
                "instrument",
                "direction",
                "units",
                "entry_price",
                "stop_loss",
                "take_profit",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow({"timestamp": datetime.utcnow().isoformat(), **trade_data})

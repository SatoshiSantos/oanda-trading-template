# core/news_filter.py

import requests
import json
import os
import time
from datetime import datetime, timedelta, timezone
from PySide6.QtWidgets import QMessageBox


class NewsFilter:
    def __init__(self, config, gui_parent=None):
        self.api_key = config.get("finnhub_api_key")
        if not self.api_key:
            raise ValueError("[NewsFilter] Finnhub API key not provided in config.")

        self.impact_filter = {
            "high": config.get("news_impact", {}).get("high", True),
            "medium": config.get("news_impact", {}).get("medium", True),
            "low": config.get("news_impact", {}).get("low", False),
        }

        self.symbol = config.get("pair")
        self.base_currency, self.quote_currency = self.symbol.split("_")
        self.include_quote_currency = config.get("news_filter_quote_currency", False)

        # Limit to USD only
        self.relevant_currencies = set()
        if "USD" in [self.base_currency, self.quote_currency]:
            self.relevant_currencies.add("USD")
        else:
            msg = f"Only US financial news can be filtered at this time. Financial news filtering is disabled for pair {self.symbol}"
            print(f"[NewsFilter] {msg}")
            if gui_parent:
                QMessageBox.warning(gui_parent, "News Filter Notice", msg)
            self.disabled = True
            return

        self.cache_file = f"news_cache_USD.json"
        self.cache_duration = 1800  # 30 minutes
        self.disabled = False

    def is_trade_blocked_by_news(self):
        if self.disabled:
            return False

        upcoming_events = self.load_cached_events()
        now = datetime.utcnow()

        for event in upcoming_events:
            event_time = self.parse_event_time(event.get("datetime"))
            if not event_time:
                continue

            if now <= event_time <= now + timedelta(minutes=60):
                impact = event.get("impact", "").lower()
                if self.impact_filter.get(impact, False):
                    return True

        return False

    def load_cached_events(self):
        if os.path.exists(self.cache_file):
            cache_mtime = os.path.getmtime(self.cache_file)
            if time.time() - cache_mtime < self.cache_duration:
                with open(self.cache_file, "r") as f:
                    return json.load(f)

        events = self.fetch_events()
        with open(self.cache_file, "w") as f:
            json.dump(events, f)
        return events

    def fetch_events(self):
        url = "https://finnhub.io/api/v1/calendar/economic"
        today = datetime.utcnow().strftime("%Y-%m-%d")
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        params = {
            "from": today,
            "to": tomorrow,
            "token": self.api_key,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            all_events = response.json().get("economicCalendar", [])
        except Exception as e:
            print((f"[NewsFilter] Failed to fetch events from Finnhub: {e}"))
            raise RuntimeError(f"[NewsFilter] Failed to fetch events from Finnhub: {e}")

        return [
            event
            for event in all_events
            if event.get("currency") == "USD"
            and event.get("impact", "").lower() in self.impact_filter
        ]

    @staticmethod
    def parse_event_time(event_time_str):
        try:
            return datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=timezone.utc
            )
        except Exception:
            return None

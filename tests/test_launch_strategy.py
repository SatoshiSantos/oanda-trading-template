# tests/test_launch_strategy.py
import sys
import os
import pytest
from unittest.mock import patch, MagicMock


# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from launch_strategy import load_strategies, launch_strategy


class DummyGUI:
    def __init__(self):
        self.strategy_dropdown = MagicMock()
        self.token_input = MagicMock()
        self.account_id_input = MagicMock()
        self.env_dropdown = MagicMock()
        self.pair_dropdown = MagicMock()
        self.risk_input = MagicMock()
        self.drawdown_input = MagicMock()
        self.direction_dropdown = MagicMock()
        self.start_input = MagicMock()
        self.end_input = MagicMock()
        self.news_buffer_input = MagicMock()
        self.news_high = MagicMock()
        self.news_med = MagicMock()
        self.news_low = MagicMock()
        self.finnhub_api_input = MagicMock()
        self.news_quote_checkbox = MagicMock()
        self.timeframe_dropdown = MagicMock()
        self.sl_strategy_combo = MagicMock()
        self.tp_strategy_combo = MagicMock()
        self.sl_pips_input = MagicMock()
        self.trailing_distance_input = MagicMock()
        self.ema_period_input = MagicMock()
        self.tp_pips_input = MagicMock()
        self.rr_ratio_input = MagicMock()
        self.run_mode_dropdown = MagicMock()

        # return values
        self.token_input.text.return_value = "fake-token"
        self.account_id_input.text.return_value = "fake-account"
        self.env_dropdown.currentText.return_value = "practice"
        self.pair_dropdown.currentText.return_value = "EUR_USD"
        self.risk_input.text.return_value = "1"
        self.drawdown_input.text.return_value = "2"
        self.direction_dropdown.currentText.return_value = "Buy"
        self.start_input.dateTime.return_value.toString.return_value = (
            "2025-06-06T00:00:00"
        )
        self.end_input.dateTime.return_value.toString.return_value = (
            "2025-06-07T00:00:00"
        )
        self.news_buffer_input.text.return_value = "10"
        self.news_high.isChecked.return_value = True
        self.news_med.isChecked.return_value = False
        self.news_low.isChecked.return_value = False
        self.finnhub_api_input.text.return_value = "finnhub-key"
        self.news_quote_checkbox.isChecked.return_value = True
        self.timeframe_dropdown.currentText.return_value = "M5"
        self.sl_strategy_combo.currentText.return_value = "Fixed SL (pips)"
        self.tp_strategy_combo.currentText.return_value = "Fixed TP (pips)"
        self.sl_pips_input.text.return_value = "10"
        self.trailing_distance_input.text.return_value = "5"
        self.ema_period_input.text.return_value = "20"
        self.tp_pips_input.text.return_value = "20"
        self.rr_ratio_input.text.return_value = "2"
        self.run_mode_dropdown.currentText.return_value = "Live"


def test_load_strategies_adds_items(tmp_path):
    # Simulate a dummy strategies directory
    strategy_dir = tmp_path / "strategies"
    strategy_dir.mkdir()
    (strategy_dir / "TestStrategy.py").write_text("class Strategy: pass")
    (strategy_dir / "__init__.py").write_text("")

    # Patch directory path
    with patch("launch_strategy.os.path.dirname", return_value=str(tmp_path)):
        gui = DummyGUI()
        load_strategies(gui)
        assert gui.strategy_dropdown.clear.called
        assert gui.strategy_dropdown.addItems.called


@patch("launch_strategy.fetch_current_price", return_value=1.2345)
@patch("launch_strategy.run_strategy")
def test_launch_strategy_prepares_config_and_runs(run_mock, price_mock):
    gui = DummyGUI()

    # Run function
    launch_strategy(gui, stop_flag=lambda: False)

    # Check fetch_current_price was called
    price_mock.assert_called_once()

    # Check run_strategy was eventually called in thread
    run_mock.assert_called()

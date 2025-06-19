# tests/test_backtester.py
"""
Unit-tests for backtest/backtester.Backtester
Run:  pytest -q
"""

import json
from pathlib import Path
import pytest

# ----------------------------------------------------------------------
# locate config/user_config.json **relative to the project root**
# ----------------------------------------------------------------------
HERE = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in HERE.parents if (p / "config").exists())
USER_CFG_PATH = PROJECT_ROOT / "config" / "user_config.json"


# ----------------------------------------------------------------------
# Test fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def live_config():
    """
    Minimal configuration for the Backtester.
    Reads token/account from config/user_config.json so
    credentials stay outside the test code.
    """
    if not USER_CFG_PATH.exists():
        pytest.skip(f"{USER_CFG_PATH} not found – cannot run back-test unit-tests.")

    with USER_CFG_PATH.open(encoding="utf-8") as fh:
        cfg = json.load(fh)

    # keep only the essentials
    return {
        "token": cfg["token"],
        "account_id": cfg["account_id"],
        "environment": cfg.get("environment", "practice"),
        "pair": cfg.get("pair", "EUR_USD"),
        "timeframe": cfg.get("timeframe", "M15"),
        "strategy": cfg.get("strategy", "ExampleStrategy"),
        # back-test only params
        "starting_balance": 100_000,
        "direction": "Both",
    }


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_equity_curve_has_ts(live_config):
    from backtest.backtester import run_backtest

    results = run_backtest(live_config, candle_count=50)

    assert results["equity_curve"], "equity_curve list is empty"
    snap0 = results["equity_curve"][0]
    assert "ts" in snap0, '"ts" key missing from equity snapshot'
    # make sure it’s a pandas/NumPy timestamp-like object
    assert snap0["ts"].__class__.__name__.endswith("Timestamp")


def test_final_balance_matches_equity(live_config):
    from backtest.backtester import run_backtest

    results = run_backtest(live_config, candle_count=50)
    last_equity = results["equity_curve"][-1]["equity"]
    assert last_equity == pytest.approx(results["final_balance"])


@pytest.mark.parametrize("candle_count", [10, 25, 75])
def test_various_history_lengths(live_config, candle_count):
    from backtest.backtester import run_backtest

    results = run_backtest(live_config, candle_count=candle_count)
    assert len(results["equity_curve"]) == candle_count

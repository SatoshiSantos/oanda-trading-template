# utils/trade_tools.py

from oandapyV20 import API
from oandapyV20.endpoints.positions import OpenPositions, PositionClose
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.trades import TradeCRCDO


def close_all_positions(token: str, account_id: str, environment: str = "practice"):
    """
    Closes all open positions (long and short) across all instruments.
    """
    try:
        client = API(access_token=token, environment=environment)

        # Get open positions
        request = OpenPositions(accountID=account_id)
        response = client.request(request)

        closed = []

        for pos in response.get("positions", []):
            instrument = pos["instrument"]
            data = {}

            if float(pos.get("long", {}).get("units", "0")) != 0:
                data["longUnits"] = "ALL"

            if float(pos.get("short", {}).get("units", "0")) != 0:
                data["shortUnits"] = "ALL"

            if data:
                close_req = PositionClose(
                    accountID=account_id, instrument=instrument, data=data
                )
                close_resp = client.request(close_req)
                closed.append({instrument: close_resp})

        return closed

    except V20Error as e:
        print(f"[Error] Failed to close positions: {e}")
        return []


def update_trade_stop_loss(
    api_client, account_id, trade_id, new_sl_price=None, new_tp_price=None
):
    data = {
        "tradeID": trade_id,
        "stopLoss": {"price": str(new_sl_price)} if new_sl_price else None,
        "takeProfit": {"price": str(new_tp_price)} if new_tp_price else None,
    }
    # Remove None fields
    data = {k: v for k, v in data.items() if v}
    r = TradeCRCDO(accountID=account_id, tradeID=trade_id, data=data)
    return api_client.request(r)

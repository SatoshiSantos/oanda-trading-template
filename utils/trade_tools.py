# utils/trade_tools.py

from oandapyV20 import API
from oandapyV20.endpoints.positions import OpenPositions, PositionClose
from oandapyV20.endpoints.trades import TradeCRCDO
from oandapyV20.exceptions import V20Error


def close_all_positions(token: str, account_id: str, environment: str = "practice"):
    """
    Closes all open positions (long and short) across all instruments.
    Returns a list of closed positions with details.
    """
    try:
        client = API(access_token=token, environment=environment)

        # Fetch all open positions
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
        print(f"[ERROR] Failed to close positions: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error during position closure: {e}")
        return []


def update_trade_stop_loss(
    api_client, account_id, trade_id, new_sl_price=None, new_tp_price=None
):
    """
    Updates the stop loss and/or take profit for a given trade.
    """
    data = {}
    if new_sl_price:
        data["stopLoss"] = {"price": str(round(float(new_sl_price), 5))}
    if new_tp_price:
        data["takeProfit"] = {"price": str(round(float(new_tp_price), 5))}

    if not data:
        raise ValueError(
            "At least one of new_sl_price or new_tp_price must be provided."
        )

    r = TradeCRCDO(accountID=account_id, tradeID=trade_id, data=data)
    return api_client.request(r)

# utils/account_tools.py

from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails, AccountSummary
from oandapyV20.exceptions import V20Error


def get_account_details(
    token: str, account_id: str, environment: str = "practice"
) -> dict:
    """
    Fetch detailed account information including margin, NAV, balance, etc.
    """
    try:
        client = API(access_token=token, environment=environment)
        request = AccountDetails(accountID=account_id)
        response = client.request(request)
        return response.get("account", {})
    except V20Error as e:
        print(f"[AccountTools] Failed to fetch account details: {e}")
        return {}


def get_account_summary(
    token: str, account_id: str, environment: str = "practice"
) -> dict:
    """
    Fetch summary of the account: balance, NAV, margin info.
    """
    try:
        client = API(access_token=token, environment=environment)
        request = AccountSummary(accountID=account_id)
        response = client.request(request)
        return response.get("account", {})
    except V20Error as e:
        print(f"[AccountTools] Failed to fetch account summary: {e}")
        return {}


def account_balance(token: str, account_id: str, environment: str):
    client = API(access_token=token, environment=environment)
    r = AccountDetails(accountID=account_id)
    response = client.request(r)
    return float(response["account"]["balance"])

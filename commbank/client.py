import logging
from typing import List, Dict, Union

import requests

from .const import DEFAULT_USERAGENT, LOGIN_URL, ACCOUNTS_URL, DEFAULT_TIMEOUT
from .exceptions import LoginFailedException, BadResponseException
from .models import Account
from .parser import parse_form, parse_api_transactions

_LOGGER = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        timeout=DEFAULT_TIMEOUT,
        useragent=DEFAULT_USERAGENT,
    ):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})
        self._timeout = timeout

        self._accounts: List[Account] = []

    def login(self, client_number, password):
        """Login to netbank using client number and password."""
        try:
            # get login page.
            response = self._session.get(LOGIN_URL, timeout=self._timeout)

            data = parse_form(response.text)["data"]

            data.update(
                {
                    "txtMyClientNumber$field": str(client_number),
                    "txtMyPassword$field": password,
                    "btnLogon$field": "Log on",
                    "chkRemember$field": "on",
                    "JS": "E",
                }
            )

            response = self._session.post(LOGIN_URL, data=data, timeout=self._timeout)

            form = parse_form(response.text)

            if form["action"].startswith("/netbank/Logon/Logon.aspx"):
                raise LoginFailedException("Credentials were likely invalid")

            # response =
            self._session.post(
                form["action"],
                data=form["data"],
                timeout=self._timeout,
            )

            # nbid cookie only exists when logged in.
            if self._session.cookies.get("nbid"):
                _LOGGER.info("Login Successful!")

                # self.load_accounts(response.text)
                return

        except Exception as ex:
            _LOGGER.exception("Login Failed!")
            raise LoginFailedException(ex)

        raise LoginFailedException("Credentials were likely invalid")

    def accounts(self) -> List[Account]:
        """Returns a list of the users accounts."""
        response = self._session.get(ACCOUNTS_URL, timeout=self._timeout)

        try:
            accounts: List = response.json()["accounts"]
            self._accounts = [Account(self, account) for account in accounts]
        except ValueError as ex:
            _LOGGER.exception("Failed to parse accounts")
            raise BadResponseException(ex)

        return self._accounts

    def account(self, account_number: Union[str, int]) -> Account:
        """Returns a single account by its account number."""
        account_number = str(account_number)

        # fetch accounts
        if not self._accounts:
            self.accounts()

        for account in self._accounts:
            if account.number == account_number:
                return account

    # def fetch_accounts(self, html):
    #     """Fetch a list of accounts."""
    #
    #     try:
    #         self.accounts = [
    #             self.Account(account, account)
    #             for account in parser.parse_accounts_table(html)
    #         ]
    #         _LOGGER.debug("ACCOUNTS: %s", self.accounts)
    #         return self.accounts
    #     except:
    #         _LOGGER.exception("Updating accounts, failed to parse accounts.")
    #         return None

    def transactions(self, account: Account) -> List[Dict]:
        """Retrieve recent transactions for an account."""

        url = "https://www.commbank.com.au" + account.link.replace(
            "/retail/netbank/accounts/", "/retail/netbank/accounts/api/transactions"
        )

        response = self._session.get(url, timeout=self._timeout)

        # if "retail/digitalidentityprovider/connect/authorize" in response.url:
        #     # we need to submit a form to continue
        #     form = parser.parse_form(response.text)
        #     print(f"ACTION: {form['action']}")
        #     response = self._session.post(
        #         "https://www.my.commbank.com.au" + form["action"],
        #         data=form["data"],
        #         timeout=self._timeout,
        #     )

        try:
            return parse_api_transactions(response.json())
        except ValueError as ex:
            _LOGGER.exception("Failed to parse transactions")
            raise BadResponseException(ex)

    # def to_dict(self) -> List[dict]:
    #     """Retrieve a dictionary of the users accounts."""
    #     return [dict(account) for account in self._accounts]

    # def __str__(self):
    #     """Returns a string representation of the users accounts."""
    #     return json.dumps([dict(account) for account in self._accounts], indent=4)

    # def __iter__(self):
    #     for account in self._accounts:
    #         yield account

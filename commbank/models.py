from typing import TYPE_CHECKING, Dict, List

from .parser import parse_account

if TYPE_CHECKING:
    from . import Client


class Account:
    def __init__(self, client: "Client", raw):
        """Representation of an account."""
        self._client = client
        self.raw = raw  # the raw account data from the commbank api.

        data = parse_account(raw)
        self.data = data

        self.name = data["name"]
        self.bsb = data["bsb"]
        self.number = data["number"]
        self.balance = data["balance"]
        self.available_balance = data["available_balance"]
        self.link = data["link"]

    def transactions(self) -> List[Dict]:
        return self._client.transactions(self)

    def __iter__(self):
        for key, value in self.data.items():
            yield (key, value)

    def __repr__(self) -> str:
        """Return the representation of the accounts."""
        return f"<Account '{self.name}' {self.bsb} {self.number}: ${self.available_balance}/{self.balance}>"

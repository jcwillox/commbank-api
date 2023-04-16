import json
import re
from datetime import datetime
from typing import List, Tuple, Dict

from bs4 import BeautifulSoup

from .utils import strip_spaces, capitalize


def parse_form(html):
    soup = BeautifulSoup(html, "html.parser")

    form_element = soup.find("form")

    form = {"action": form_element["action"], "data": {}}

    for el in form_element.find_all("input", attrs={"type": "hidden"}):
        if el.has_attr("name") and el.has_attr("value"):
            form["data"][el["name"]] = el["value"]

    return form


# def parse_accounts_table(html):
#     accounts = []
#
#     soup = BeautifulSoup(html, "html.parser")
#     for row in soup.select(".account-row"):
#         bsb_acc = row.select_one(".account-number").replace("-", "").replace(" ", "")
#         account = {
#             "name": row.select_one(".account-name").text.strip(),
#             "bsb": bsb_acc[:6],
#             "number": bsb_acc[6:],
#             "balance": parse_currency_html(row.select_one(".balance.balance__item")),
#             "available_balance": parse_currency_html(
#                 row.select_one(".balance.balance__item.is-bold")
#             ),
#             "link": row.select_one(".account-link")["href"],
#         }
#         print(account)
#         accounts.append(account)
#     return accounts


def parse_account(data):
    """Helper method to return a simplified dictionary for an account's data."""
    return {
        "name": data["displayName"],
        "bsb": data["number"][:6],  # first 6 digits are the bsb.
        "number": data["number"][6:],  # rest are the account number.
        "balance": data["balance"][0]["amount"],
        "available_balance": data["availableFunds"][0]["amount"] if len(data["availableFunds"]) == 1 else 0,
        "link": data["link"]["url"],
    }


def parse_api_transactions(data) -> List[Dict]:
    transactions = []
    for transaction in data["transactions"]:
        payee, desc = parse_transaction_description(transaction["description"])

        transactions.append(
            {
                "timestamp": datetime.fromisoformat(
                    transaction["createdDate"]
                ).timestamp(),
                "date": transaction["createdDate"],
                "payee": payee,
                "description": desc,
                "raw_description": transaction["description"],
                "amount": transaction["amount"],
                "balance": transaction["runningTotal"],
                "trancode": transaction["transactionId"],
                "receipt_number": transaction["receiptNumber"],
                # "link": transaction["Description"]["Url"],
            }
        )
    return transactions


def parse_transactions(html) -> List[Dict]:
    x = re.findall(r'({"Transactions":(?:.+)})\);', html)
    history = json.loads(x[0])

    transactions = []

    all_transactions = []

    if history["OutstandingAuthorizations"]:
        all_transactions.extend(history["OutstandingAuthorizations"])

    all_transactions.extend(history["Transactions"])

    for transaction in all_transactions:
        payee, desc = parse_transaction_description(transaction["Description"]["Text"])

        date = transaction["Date"]["Sort"][1]
        if date:
            date = datetime.strptime(
                transaction["Date"]["Sort"][1][:14] + "+0000", "%Y%m%d%H%M%S%z"
            )
        else:
            date = datetime.strptime(transaction["Date"]["Text"], "%d %b %Y")

        transactions.append(
            {
                "timestamp": int(date.timestamp()),
                "date": str(date),
                "payee": payee,
                "description": desc,
                "raw_description": transaction["Description"]["Text"],
                "amount": parse_sortable_currency(transaction["SortableAmount"]),
                "balance": parse_sortable_currency(
                    transaction["SortableCurrencyAmount"]
                ),
                "trancode": transaction["TranCode"]["Text"],
                "receipt_number": transaction["ReceiptNumber"]["Text"],
                "link": transaction["Description"]["Url"],
            }
        )

    return transactions


def parse_currency_html(text):
    return float(re.sub(r"[^\d.-]", "", text))


def parse_sortable_currency(sortable):
    currency = sortable["Sort"][1]
    if sortable["Text"].endswith("DR"):
        return -currency
    return currency


def parse_transaction_description(description: str) -> Tuple[str, str]:
    """Extracts the relevant sections from the raw description."""
    if "\n" not in description:
        return description, ""

    lines: List[str] = strip_spaces(description).split("\n")

    if len(lines) == 3:
        if lines[2].startswith("Value Date"):
            return capitalize(lines[0]), ""

        if lines[0].lower().startswith("transfer to"):
            lines[0] = re.sub(r"Transfer [tT]o ", "", lines[0])
            return capitalize(lines[0]), lines[2]

    if len(lines) == 2:
        if lines[1].startswith("Value Date") or lines[0].startswith("PENDING"):
            return capitalize(lines[0]), ""

        lines[0] = re.sub(r"Transfer (?:[fF]rom|[tT]o) ", "", lines[0])
        lines[0] = re.sub(r"Direct (?:Credit|Debit) \d+ ", "", lines[0])
        lines[0] = re.sub(r" for collection", "", lines[0])
        lines[1] = re.sub(r"^CommBank App ", "", lines[1])
        return strip_spaces(capitalize(lines[0])), lines[1]

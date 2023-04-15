# CommBank API

Unofficial API client for the Commonwealth Bank of Australia (CommBank) NetBank.

> NOTE ⚠️: This project is not being maintained, I do not actively use commbank at the moment, but I may fixup this project if I have time. This project is based on some old code I wrote just for personal use and is not the best, but hopefully the code here can help others make API clients for commbank.

## Usage

```python
from commbank import CommBank

client = CommBank(timeout=10)

client.login(USERNAME, PASSWORD)
```

### Accounts

```python
account = client.get_account(12345678)

print(account)
```

For each account, there are following properties:

- `name`: Account name;
- `bsb`: BSB number;
- `number`: Account number (without BSB part);
- `balance`: Current account balance.
- `available_balance`: Current available funds of the account.
- `link`: Transaction page for the account, it will be different everytime you login;

### Transactions

```python
transactions = client.get_transactions(account)

print(json.dumps(transactions, indent=4))
```

For each transaction object, there are following properties:

- `timestamp`: Timestamp of given transaction, it's milliseconds since epoch. Although, it might be pretty accurate for some accounts (non-credit card account), it might just be accurate at date level.
- `date`: It's human readable date format.
- `payee`: The payee parsed from the transaction (this is far from perfect at the moment).
- `description`: Transaction description with the payee removed.
- `raw_description`: The raw description from the transaction (before we attempt to split it into the payee and description).
- `amount`: Transaction amount, negative value is DR, positive value is CR.
- `balance`: The balance of the account after the transaction happened, however, the field might be empty for some accounts, such as credit card account.
- `trancode`: It's a category code for the transaction, such as ATM, EFTPOS, cash out might be different code.
- `receiptnumber`: The receipt number for the transaction. However, I cannot found it on my real paper receipt, and the field might be missing for some accounts, such as credit card account.
- `link`: Transactions using the new payments platform will have a link for retrieving extended information on the transaction.

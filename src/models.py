from __future__ import annotations
from enum import Enum
import abc
import uuid
from datetime import datetime, time, timedelta
import json

class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

class CurrencyType(Enum):
    RUB = "rub"
    USD = "usd"
    EUR = "eur"
    KZT = "kzt"
    CNY = "cny"

class AccountFrozenError(Exception):
    pass

class AccountClosedError(Exception):
    pass

class InvalidOperationError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class AbstractAccount(abc.ABC):
    _balance: float = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: float = 0
    ):
        self.account_id = account_id
        self.name = name
        self.status = status

        if account_id is None:
            self.account_id = str(uuid.uuid4())

        if balance < 0:
            raise InvalidOperationError('Initial balance cannot be negative')
        else:
            self._balance = balance

    @abc.abstractmethod
    def deposit(self, amount: float): pass

    @abc.abstractmethod
    def withdraw(self, amount: float): pass

    @abc.abstractmethod
    def get_account_info(self): pass

class BankAccount(AbstractAccount):
    currency: CurrencyType = CurrencyType.RUB

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: float = 0,
        currency: CurrencyType = CurrencyType.RUB
    ):
        super().__init__(account_id, name, status, balance)
        self.currency = currency

    def deposit(self, amount: float):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float):
        self.check_status()
        self.check_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError('Amount is insufficient')

        self._balance -= amount

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "name": self.name,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
        }

    def check_status(self):
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError('Account is frozen')

        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError('Account is closed')

    def check_amount(self, amount: float):
        if amount <= 0:
            raise InvalidOperationError('Amount must be positive')

    def __str__(self):
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balance}{self.currency.value}"

class SavingsAccount(BankAccount):
    _min_balance: float = 0
    interest_rate: float = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: float = 0,
        currency: CurrencyType = CurrencyType.RUB,
        min_balance: float = 0,
        interest_rate: float = 0
    ):
        super().__init__(account_id, name, status, balance, currency)

        if min_balance < 0:
            raise InvalidOperationError('Initial minimum balance cannot be negative')
        else:
            self._min_balance = min_balance

        if min_balance > balance:
            raise InvalidOperationError('Balance cannot be less than the minimum balance')

        if interest_rate < 0:
            raise InvalidOperationError('Interest rate cannot be negative')
        else:
            self.interest_rate = interest_rate

    def withdraw(self, amount: float):
        self.check_status()
        self.check_amount(amount)

        if self._balance - amount < self._min_balance:
            raise InsufficientFundsError('Withdrawal would violate the minimum balance')

        self._balance -= amount

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "name": self.name,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
            "min_balance": self._min_balance,
            "interest_rate": self.interest_rate,
        }

    def __str__(self):
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balance}{self.currency.value} {self._min_balance} {self.interest_rate}"

    def apply_monthly_interest(self):
        self._balance = self._balance * (1 + self.interest_rate / 100)

class PremiumAccount(BankAccount):
    commission: float = 0
    overdraft: float = 0
    limit: float = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: float = 0,
        currency: CurrencyType = CurrencyType.RUB,
        commission: float = 0,
        overdraft: float = 0,
        limit: float = 0
    ):
        super().__init__(account_id, name, status, balance, currency)

        if commission < 0:
            raise InvalidOperationError('Commission cannot be negative')
        else:
            self.commission = commission

        if overdraft < 0:
            raise InvalidOperationError('Overdraft cannot be negative')
        else:
            self.overdraft = overdraft

        if limit < 0:
            raise InvalidOperationError('Limit cannot be negative')
        else:
            self.limit = limit

    def withdraw(self, amount: float):
        self.check_status()
        self.check_amount(amount)

        total_amount = amount + self.commission

        if total_amount > self.limit:
            raise InvalidOperationError(
                'Withdrawal amount including commission exceeds limit'
            )

        if self._balance - total_amount < -self.overdraft:
            raise InsufficientFundsError(
                'Amount including commission exceeds overdraft'
            )

        self._balance -= total_amount

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "name": self.name,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
            "commission": self.commission,
            "overdraft": self.overdraft,
            "limit": self.limit,
        }

    def __str__(self):
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balance}{self.currency.value} {self.commission} {self.overdraft} {self.limit}"

class Asset(abc.ABC):
    id: str
    name: str
    price: float
    quantity: int

    def __init__(
        self,
        id: str | None,
        name: str,
        price: float,
        quantity: int
    ):
        self.id = id
        self.name = name

        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

        if price <= 0:
            raise InvalidOperationError('Price cannot be negative or zero')
        else:
            self.price = price

        if quantity <= 0:
            raise InvalidOperationError('Quantity cannot be negative or zero')
        else:
            self.quantity = quantity

class Stock(Asset):
    def __init__(
        self,
        id: str | None,
        name: str,
        price: float,
        quantity: int
    ):
        super().__init__(id, name, price, quantity)

class Bond(Asset):
    def __init__(
        self,
        id: str | None,
        name: str,
        price: float,
        quantity: int
    ):
        super().__init__(id, name, price, quantity)

class Etf(Asset):
    def __init__(
        self,
        id: str | None,
        name: str,
        price: float,
        quantity: int
    ):
        super().__init__(id, name, price, quantity)

class InvestmentAccount(BankAccount):
    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: float = 0,
        currency: CurrencyType = CurrencyType.RUB,
        stocks: list[Stock] | None = None,
        bonds: list[Bond] | None = None,
        etf: list[Etf] | None = None
    ):
        super().__init__(account_id, name, status, balance, currency)

        self._stocks: list[Stock] = [] if stocks is None else stocks
        self._bonds: list[Bond] = [] if bonds is None else bonds
        self._etf: list[Etf] = [] if etf is None else etf

    def withdraw(self, amount: float):
        self.check_status()
        self.check_amount(amount)

        if amount <= self._balance:
            self._balance -= amount
            return

        original_balance = self._balance
        original_stocks = [(asset, asset.quantity) for asset in self._stocks]
        original_bonds = [(asset, asset.quantity) for asset in self._bonds]
        original_etf = [(asset, asset.quantity) for asset in self._etf]

        try:
            needed = amount - self._balance

            for asset_list in [self._etf, self._bonds, self._stocks]:
                if self._balance >= amount:
                    break

                for asset in asset_list[:]:
                    if self._balance >= amount:
                        break

                    sell_quantity = int(needed // asset.price)
                    if needed % asset.price != 0:
                        sell_quantity += 1

                    if sell_quantity <= 0:
                        sell_quantity = 1

                    if sell_quantity > asset.quantity:
                        sell_quantity = asset.quantity

                    sold_value = sell_quantity * asset.price
                    asset.quantity -= sell_quantity
                    self._balance += sold_value
                    needed = amount - self._balance

                    if asset.quantity == 0:
                        asset_list.remove(asset)

            if amount > self._balance:
                raise InsufficientFundsError('Insufficient funds even after selling assets')

            self._balance -= amount

        except Exception:
            self._balance = original_balance
            self._stocks = [asset for asset, _ in original_stocks]
            self._bonds = [asset for asset, _ in original_bonds]
            self._etf = [asset for asset, _ in original_etf]

            for asset, quantity in original_stocks:
                asset.quantity = quantity
            for asset, quantity in original_bonds:
                asset.quantity = quantity
            for asset, quantity in original_etf:
                asset.quantity = quantity

            raise

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "name": self.name,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
            "stocks": [
                {
                    "id": stock.id,
                    "name": stock.name,
                    "price": stock.price,
                    "quantity": stock.quantity,
                }
                for stock in self._stocks
            ],
            "bonds": [
                {
                    "id": bond.id,
                    "name": bond.name,
                    "price": bond.price,
                    "quantity": bond.quantity,
                }
                for bond in self._bonds
            ],
            "etf": [
                {
                    "id": etf.id,
                    "name": etf.name,
                    "price": etf.price,
                    "quantity": etf.quantity,
                }
                for etf in self._etf
            ],
        }

    def __str__(self):
        return (
            f"{self.account_id[-4:]} {self.name} {self.status.value} "
            f"{self._balance} {self.currency.value} "
            f"stocks={len(self._stocks)} bonds={len(self._bonds)} etf={len(self._etf)}"
        )

    def project_yearly_growth(self, annual_rate: float):
        if annual_rate < 0:
            raise InvalidOperationError('Annual rate cannot be negative')

        total_value = self._balance
        total_value += sum(stock.price * stock.quantity for stock in self._stocks)
        total_value += sum(bond.price * bond.quantity for bond in self._bonds)
        total_value += sum(etf.price * etf.quantity for etf in self._etf)

        projected_value = total_value * (1 + annual_rate / 100)

        return {
            "current_value": total_value,
            "annual_rate": annual_rate,
            "projected_value": projected_value,
            "projected_growth": projected_value - total_value,
        }

class ClientStatus(Enum):
    ACTIVE = 'active'
    BLOCKED = 'blocked'

class Client:
    def __init__(
        self,
        client_id: str | None,
        name: str,
        phone_number: str,
        email: str,
        age: int,
        password: str,
    ):
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.status = ClientStatus.ACTIVE
        self.accounts: list[str] = []
        self.failed_login_attempts = 0
        self.password = password
        self.is_suspicious = False

        if client_id is None:
            self.client_id = str(uuid.uuid4())
        else:
            self.client_id = client_id

        if age < 18:
            raise InvalidOperationError('Age cannot be less than 18')
        else:
            self.age = age

class TransactionType(Enum):
    INTERNAL_TRANSACTION = 1
    EXTERNAL_TRANSACTION = 2
    EXCHANGE_TRANSACTION = 3

class TransactionStatus(Enum):
    PENDING = 1
    PROCESSING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELED = 5
    BLOCKED = 6

class TransactionPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class Transaction:
    def __init__(
        self,
        transaction_id: str | None,
        amount: float,
        currency: CurrencyType,
        commission: float,
        sender_account_id: str,
        receiver_account_id: str,
        transaction_type: TransactionType,
        priority: TransactionPriority,
        available_at: datetime | None
    ):
        if transaction_id is None:
            self.transaction_id = str(uuid.uuid4())
        else:
            self.transaction_id = transaction_id

        self.amount = amount
        self.currency = currency
        self.commission = commission
        self.sender_account_id = sender_account_id
        self.receiver_account_id = receiver_account_id
        self.transaction_type = transaction_type
        self.status = TransactionStatus.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.priority = priority
        self.failure_reason = None
        self.available_at = available_at
        self.attempts = 0
        self.max_attempts = 3

class TransactionQueue:
    def __init__(self):
        self.transactions: list[Transaction] = []

    def add_transaction(self, transaction: Transaction):
        if transaction is None:
            raise InvalidOperationError('Transaction cannot be None')
        if transaction.status is not TransactionStatus.PENDING:
            raise InvalidOperationError('It is impossible to add not pending transaction')

        self.transactions.append(transaction)

    def cancel_transaction(self, transaction_id: str):
        transaction = next(
            (t for t in self.transactions if t.transaction_id == transaction_id),
            None
        )

        if transaction is None:
            raise InvalidOperationError('Transaction does not exist')

        if transaction.status is not TransactionStatus.PENDING:
            raise InvalidOperationError('It is impossible to cancel not pending transaction')

        transaction.status = TransactionStatus.CANCELED

    def get_next_transaction(self):
        now = datetime.now()

        pending_transactions = [
            t for t in self.transactions
            if t.status is TransactionStatus.PENDING
            and (t.available_at is None or t.available_at <= now)
        ]

        if not pending_transactions:
            raise InvalidOperationError('There are no available pending transactions')

        return min(
            pending_transactions,
            key=lambda t: (t.priority.value, t.created_at)
        )

    def has_available_transactions(self) -> bool:
        now = datetime.now()

        return any(
            t.status is TransactionStatus.PENDING
            and (t.available_at is None or t.available_at <= now)
            for t in self.transactions
        )

_EXCHANGE_RATES = {
    # from RUB
    (CurrencyType.RUB, CurrencyType.USD): 0.012,
    (CurrencyType.RUB, CurrencyType.EUR): 0.011,
    (CurrencyType.RUB, CurrencyType.KZT): 5.0,
    (CurrencyType.RUB, CurrencyType.CNY): 0.085,

    # from USD
    (CurrencyType.USD, CurrencyType.RUB): 83.0,
    (CurrencyType.USD, CurrencyType.EUR): 0.92,
    (CurrencyType.USD, CurrencyType.KZT): 420.0,
    (CurrencyType.USD, CurrencyType.CNY): 7.2,

    # from EUR
    (CurrencyType.EUR, CurrencyType.RUB): 90.0,
    (CurrencyType.EUR, CurrencyType.USD): 1.09,
    (CurrencyType.EUR, CurrencyType.KZT): 460.0,
    (CurrencyType.EUR, CurrencyType.CNY): 7.8,

    # from KZT
    (CurrencyType.KZT, CurrencyType.RUB): 0.2,
    (CurrencyType.KZT, CurrencyType.USD): 0.0024,
    (CurrencyType.KZT, CurrencyType.EUR): 0.0022,
    (CurrencyType.KZT, CurrencyType.CNY): 0.017,

    # from CNY
    (CurrencyType.CNY, CurrencyType.RUB): 11.5,
    (CurrencyType.CNY, CurrencyType.USD): 0.14,
    (CurrencyType.CNY, CurrencyType.EUR): 0.13,
    (CurrencyType.CNY, CurrencyType.KZT): 58.0,
}

class AccountType(Enum):
    BANK = "bank"
    SAVINGS = "savings"
    PREMIUM = "premium"
    INVESTMENT = "investment"

class Bank:
    def __init__(self):
        self.clients: dict[str, Client] = {}
        self.accounts: dict[str, BankAccount] = {}
        self.transactions: list[Transaction] = []

    def add_client(
        self,
        name,
        phone_number,
        email,
        age,
        password: str,
        client_id=None,
    ):
        client = Client(client_id, name, phone_number, email, age, password)

        if client.client_id in self.clients:
            raise InvalidOperationError('Client already exists')

        self.clients[client.client_id] = client

    def check_time(self):
        current_time = datetime.now().time()

        if time(0, 0) <= current_time < time(5, 0):
            raise InvalidOperationError('Operations are not allowed from 00:00 to 05:00')

    def open_account(
        self,
        client_id: str,
        account_type: AccountType,
        name: str,
        balance: float,
        currency: CurrencyType,
        *,
        min_balance: float = 0,
        interest_rate: float = 0,
        commission: float = 0,
        overdraft: float = 0,
        limit: float = 0,
        stocks: list[Stock] | None = None,
        bonds: list[Bond] | None = None,
        etf: list[Etf] | None = None
    ):
        if client_id not in self.clients:
            raise InvalidOperationError('Client does not exist')

        self.check_time()

        client = self.clients[client_id]

        if client.status is ClientStatus.BLOCKED:
            raise InvalidOperationError('Client is blocked')

        account = None

        if account_type is AccountType.BANK:
            account = BankAccount(name=name, balance=balance, currency=currency)
        elif account_type is AccountType.SAVINGS:
            account = SavingsAccount(name=name, balance=balance, currency=currency, min_balance=min_balance, interest_rate=interest_rate)
        elif account_type is AccountType.PREMIUM:
            account = PremiumAccount(name=name, balance=balance, currency=currency, commission=commission, overdraft=overdraft, limit=limit)
        elif account_type is AccountType.INVESTMENT:
            account = InvestmentAccount(name=name, balance=balance, currency=currency, stocks=stocks, bonds=bonds, etf=etf)
        else:
            raise InvalidOperationError('Invalid account type')

        self.accounts[account.account_id] = account
        client.accounts.append(account.account_id)

        return account

    def close_account(self, account_id: str):
        if account_id not in self.accounts:
            raise InvalidOperationError('Account does not exist')

        self.check_time()

        account = self.accounts[account_id]

        if account.status is AccountStatus.CLOSED:
            raise InvalidOperationError('Account is already closed')

        account.status = AccountStatus.CLOSED

    def freeze_account(self, account_id: str):
        if account_id not in self.accounts:
            raise InvalidOperationError('Account does not exist')

        self.check_time()

        account = self.accounts[account_id]

        if account.status is AccountStatus.CLOSED:
            raise InvalidOperationError('Account is closed and cannot be frozen')

        if account.status is AccountStatus.FROZEN:
            raise InvalidOperationError('Account is already frozen')

        account.status = AccountStatus.FROZEN

    def unfreeze_account(self, account_id: str):
        if account_id not in self.accounts:
            raise InvalidOperationError('Account does not exist')

        self.check_time()

        account = self.accounts[account_id]

        if account.status is AccountStatus.CLOSED:
            raise InvalidOperationError('Account is closed and cannot be unfrozen')

        if account.status is not AccountStatus.FROZEN:
            raise InvalidOperationError('Account is not frozen')

        account.status = AccountStatus.ACTIVE

    def authenticate_client(self, client_id: str, password: str):
        if client_id not in self.clients:
            raise InvalidOperationError('Client does not exist')

        self.check_time()

        client = self.clients[client_id]

        if client.status is ClientStatus.BLOCKED:
            raise InvalidOperationError('Client is blocked')

        if client.password != password:
            client.failed_login_attempts += 1

            if client.failed_login_attempts >= 3:
                client.status = ClientStatus.BLOCKED
                raise InvalidOperationError('Client is blocked after 3 failed login attempts')

            raise InvalidOperationError('Password is incorrect')

        client.failed_login_attempts = 0

        return client

    def search_accounts(
        self,
        account_id: str | None = None,
        client_id: str | None = None,
        name: str | None = None,
        status=None,
        currency=None,
    ) -> list[BankAccount]:
        results = list(self.accounts.values())

        if account_id is not None:
            results = [
                account for account in results
                if account.account_id == account_id
            ]

        if client_id is not None:
            if client_id not in self.clients:
                raise InvalidOperationError("Client does not exist")

            client_account_ids = set(self.clients[client_id].accounts)
            results = [
                account for account in results
                if account.account_id in client_account_ids
            ]

        if name is not None:
            name_lower = name.lower()
            results = [
                account for account in results
                if name_lower in account.name.lower()
            ]

        if status is not None:
            results = [
                account for account in results
                if account.status is status
            ]

        if currency is not None:
            results = [
                account for account in results
                if account.currency is currency
            ]

        return results

    def register_transaction(self, transaction: Transaction):
        if transaction is None:
            raise InvalidOperationError('Transaction cannot be None')

        self.transactions.append(transaction)

    def get_total_balance(self):
        totals = {
            currency.value: 0.0
            for currency in CurrencyType
        }

        for account in self.accounts.values():
            if account.status is AccountStatus.CLOSED:
                continue

            totals[account.currency.value] += account._balance

        return totals

    def _convert_amount(
        self,
        amount: float,
        from_currency: CurrencyType,
        to_currency: CurrencyType
    ) -> float:
        if from_currency == to_currency:
            return amount

        key = (from_currency, to_currency)
        if key not in _EXCHANGE_RATES:
            raise InvalidOperationError('Exchange rate not available for this currency pair')

        return amount * _EXCHANGE_RATES[key]

    def get_clients_ranking(self, base_currency: CurrencyType = CurrencyType.RUB):
        ranking = []

        for client in self.clients.values():
            total_balance = 0.0

            for account_id in client.accounts:
                account = self.accounts[account_id]

                if account.status is AccountStatus.CLOSED:
                    continue

                total_balance += self._convert_amount(
                    account._balance,
                    account.currency,
                    base_currency
                )

            ranking.append({
                "client_id": client.client_id,
                "name": client.name,
                "total_balance": total_balance,
                "currency": base_currency.value,
            })

        return sorted(
            ranking,
            key=lambda item: item["total_balance"],
            reverse=True
        )

    def create_transaction(
        self,
        queue: TransactionQueue,
        amount: float,
        currency: CurrencyType,
        commission: float,
        sender_account_id: str,
        receiver_account_id: str,
        transaction_type: TransactionType,
        priority: TransactionPriority,
        available_at: datetime | None = None,
        transaction_id: str | None = None,
    ):
        self.check_time()

        if sender_account_id not in self.accounts:
            raise InvalidOperationError('Sender account does not exist')

        if transaction_type != TransactionType.EXTERNAL_TRANSACTION and receiver_account_id not in self.accounts:
            raise InvalidOperationError('Receiver account does not exist')

        transaction = Transaction(
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            commission=commission,
            sender_account_id=sender_account_id,
            receiver_account_id=receiver_account_id,
            transaction_type=transaction_type,
            priority=priority,
            available_at=available_at,
        )

        self.register_transaction(transaction)
        queue.add_transaction(transaction)

        return transaction

class AuditLevel(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class AuditEntry:
    def __init__(
        self,
        level: AuditLevel,
        event_type: str,
        message: str,
        client_id: str | None,
        account_id: str | None,
        transaction_id: str | None,
        metadata: dict[str, object] | None
    ):
        self.timestamp = datetime.now()
        self.level = level
        self.event_type = event_type
        self.message = message
        self.client_id = client_id
        self.account_id = account_id
        self.transaction_id = transaction_id
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "event_type": self.event_type,
            "message": self.message,
            "client_id": self.client_id,
            "account_id": self.account_id,
            "transaction_id": self.transaction_id,
            "metadata": self.metadata,
        }

class AuditLog:
    def __init__(self, file_name: str | None = None):
        self.entries: list[AuditEntry] = []
        self.file_name = file_name

    def log(
        self,
        level: AuditLevel,
        event_type: str,
        message: str,
        client_id: str | None = None,
        account_id: str | None = None,
        transaction_id: str | None = None,
        metadata: dict[str, object] | None = None
    ):
        entry = AuditEntry(
            level=level,
            event_type=event_type,
            message=message,
            client_id=client_id,
            account_id=account_id,
            transaction_id=transaction_id,
            metadata=metadata
        )

        self.entries.append(entry)

        return entry

    def filter_by_level(self, level: AuditLevel) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.level == level]

    def filter_by_client_id(self, client_id: str | None) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.client_id == client_id]

    def filter_by_account_id(self, account_id: str | None) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.account_id == account_id]

    def filter_by_date_range(self, start: datetime, end: datetime) -> list[AuditEntry]:
        if start > end:
            raise InvalidOperationError('Start date cannot be later than end date')

        return [entry for entry in self.entries if start <= entry.timestamp <= end]

    def save_to_file(self):
        if self.file_name is None:
            raise InvalidOperationError('File name is not set')

        payload = {
            "entries": [entry.to_dict() for entry in self.entries]
        }

        with open(self.file_name, 'w', encoding='utf-8') as file:
            json.dump(payload, file, ensure_ascii=False, indent=4)

class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class RiskAnalyzer:
    def __init__(
        self,
        bank: Bank,
        large_amount_threshold: float = 100000,
        frequent_ops_window_minutes: int = 10,
        frequent_ops_count_threshold: int = 3,
    ):
        self.bank = bank
        self.large_amount_threshold = large_amount_threshold
        self.frequent_ops_window_minutes = frequent_ops_window_minutes
        self.frequent_ops_count_threshold = frequent_ops_count_threshold

    def analyze_risk(self, transaction: Transaction) -> RiskLevel:
        risk_score = 0

        if self.is_large_amount(transaction):
            risk_score += 1

        if self.is_night_operation(transaction):
            risk_score += 1

        if self.is_new_receiver(transaction):
            risk_score += 1

        if self.is_frequent_operation(transaction):
            risk_score += 1

        if risk_score == 0:
            return RiskLevel.LOW
        elif risk_score == 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def is_large_amount(self, transaction: Transaction) -> bool:
        return transaction.amount >= self.large_amount_threshold

    def is_night_operation(self, transaction: Transaction) -> bool:
        transaction_time = transaction.created_at.time()
        return time(0, 0) <= transaction_time < time(5, 0)

    def is_new_receiver(self, transaction: Transaction) -> bool:
        for old_transaction in self.bank.transactions:
            if old_transaction.transaction_id == transaction.transaction_id:
                continue

            if (
                old_transaction.sender_account_id == transaction.sender_account_id
                and old_transaction.receiver_account_id == transaction.receiver_account_id
                and old_transaction.status == TransactionStatus.COMPLETED
            ):
                return False

        return True

    def is_frequent_operation(self, transaction: Transaction) -> bool:
        window_start = datetime.now() - timedelta(
            minutes=self.frequent_ops_window_minutes
        )

        count = 0

        for old_transaction in self.bank.transactions:
            if old_transaction.transaction_id == transaction.transaction_id:
                continue

            if old_transaction.sender_account_id != transaction.sender_account_id:
                continue

            if old_transaction.status is not TransactionStatus.COMPLETED:
                continue

            if old_transaction.completed_at is None:
                continue

            if old_transaction.completed_at < window_start:
                continue

            count += 1

        return count >= self.frequent_ops_count_threshold

class AuditReport:
    def __init__(
        self,
        audit_log: AuditLog,
        bank: Bank,
        risk_analyzer: RiskAnalyzer
    ):
        self.audit_log = audit_log
        self.bank = bank
        self.risk_analyzer = risk_analyzer

    def get_suspicious_transactions_report(self) -> list[dict]:
        suspicious_transactions = []

        for transaction in self.bank.transactions:
            if transaction.status == TransactionStatus.CANCELED:
                continue

            risk_level = self.risk_analyzer.analyze_risk(transaction)

            if risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH):
                suspicious_transactions.append({
                    "transaction_id": transaction.transaction_id,
                    "sender_account_id": transaction.sender_account_id,
                    "receiver_account_id": transaction.receiver_account_id,
                    "amount": transaction.amount,
                    "currency": transaction.currency.value,
                    "risk_level": risk_level.name,
                    "status": transaction.status.name,
                })

        return suspicious_transactions

    def get_client_risk_profile(self, client_id: str) -> dict:
        if client_id not in self.bank.clients:
            raise InvalidOperationError('Client does not exist')

        client = self.bank.clients[client_id]

        client_transactions = []
        risk_counts = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
        }

        for transaction in self.bank.transactions:
            if transaction.sender_account_id in client.accounts or \
                    transaction.receiver_account_id in client.accounts:
                client_transactions.append(transaction)

                risk_level = self.risk_analyzer.analyze_risk(transaction)
                risk_counts[risk_level] += 1

        total_amount = sum(t.amount for t in client_transactions)

        return {
            "client_id": client_id,
            "name": client.name,
            "total_transactions": len(client_transactions),
            "total_amount": total_amount,
            "risk_breakdown": {
                "low": risk_counts[RiskLevel.LOW],
                "medium": risk_counts[RiskLevel.MEDIUM],
                "high": risk_counts[RiskLevel.HIGH],
            },
            "is_suspicious": client.is_suspicious,
        }

    def get_error_statistics(self) -> dict:
        stats = {
            AuditLevel.INFO: 0,
            AuditLevel.WARNING: 0,
            AuditLevel.ERROR: 0,
            AuditLevel.CRITICAL: 0,
        }

        for entry in self.audit_log.entries:
            stats[entry.level] += 1

        return {
            "info": stats[AuditLevel.INFO],
            "warning": stats[AuditLevel.WARNING],
            "error": stats[AuditLevel.ERROR],
            "critical": stats[AuditLevel.CRITICAL],
        }

class TransactionProcessor:

    def __init__(
        self,
        bank: Bank,
        risk_analyzer: RiskAnalyzer,
        audit_log: AuditLog
    ):
        self.bank = bank
        self.risk_analyzer = risk_analyzer
        self.audit_log = audit_log

    def process_next_transaction(self, queue: TransactionQueue):
        self.bank.check_time()

        if not queue.has_available_transactions():
            raise InvalidOperationError('There are no available pending transactions')

        transaction = queue.get_next_transaction()

        risk_level = self.risk_analyzer.analyze_risk(transaction)

        sender_account = self._get_sender_account(transaction)
        sender_client = next(
            (
                client
                for client in self.bank.clients.values()
                if sender_account.account_id in client.accounts
            ),
            None,
        )

        if sender_client is not None and risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH):
            sender_client.is_suspicious = True

        if risk_level == RiskLevel.HIGH:
            transaction.status = TransactionStatus.BLOCKED
            transaction.failure_reason = 'Transaction is blocked due to high risk'
            transaction.completed_at = datetime.now()
            self.audit_log.log(
                level=AuditLevel.CRITICAL,
                event_type='transaction_blocked',
                message='Transaction blocked due to high risk',
                account_id=transaction.sender_account_id,
                transaction_id=transaction.transaction_id,
                metadata={
                    'risk_level': risk_level.name,
                    'sender_account_id': transaction.sender_account_id,
                    'receiver_account_id': transaction.receiver_account_id,
                }
            )
            return

        if risk_level == RiskLevel.MEDIUM:
            self.audit_log.log(
                level=AuditLevel.WARNING,
                event_type='transaction_warning',
                message='Transaction marked as suspicious with medium risk',
                account_id=transaction.sender_account_id,
                transaction_id=transaction.transaction_id,
                metadata={
                    'risk_level': risk_level.name,
                    'sender_account_id': transaction.sender_account_id,
                    'receiver_account_id': transaction.receiver_account_id,
                }
            )

        transaction.status = TransactionStatus.PROCESSING
        transaction.attempts += 1

        try:
            self._process_transaction(transaction)
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            transaction.failure_reason = None

            self.audit_log.log(
                level=AuditLevel.INFO,
                event_type='transaction_completed',
                message='Transaction completed successfully',
                account_id=transaction.sender_account_id,
                transaction_id=transaction.transaction_id,
                metadata={
                    'risk_level': risk_level.name,
                    'sender_account_id': transaction.sender_account_id,
                    'receiver_account_id': transaction.receiver_account_id,
                }
            )
        except Exception as ex:
            transaction.failure_reason = str(ex)

            if transaction.attempts < transaction.max_attempts:
                transaction.status = TransactionStatus.PENDING
                transaction.available_at = datetime.now() + timedelta(minutes=5)

                self.audit_log.log(
                    level=AuditLevel.WARNING,
                    event_type='transaction_retry_scheduled',
                    message=str(ex),
                    account_id=transaction.sender_account_id,
                    transaction_id=transaction.transaction_id,
                    metadata={
                        'risk_level': risk_level.name,
                        'attempts': transaction.attempts,
                        'max_attempts': transaction.max_attempts,
                        'next_retry_at': transaction.available_at.isoformat(),
                        'sender_account_id': transaction.sender_account_id,
                        'receiver_account_id': transaction.receiver_account_id,
                    }
                )
            else:
                transaction.status = TransactionStatus.FAILED
                transaction.completed_at = datetime.now()

                self.audit_log.log(
                    level=AuditLevel.ERROR,
                    event_type='transaction_failed',
                    message=str(ex),
                    account_id=transaction.sender_account_id,
                    transaction_id=transaction.transaction_id,
                    metadata={
                        'risk_level': risk_level.name,
                        'attempts': transaction.attempts,
                        'max_attempts': transaction.max_attempts,
                        'sender_account_id': transaction.sender_account_id,
                        'receiver_account_id': transaction.receiver_account_id,
                    }
                )

    def _process_transaction(self, transaction: Transaction):
        self._validate_transaction(transaction)

        sender_account = self._get_sender_account(transaction)
        receiver_account = None

        if transaction.transaction_type != TransactionType.EXTERNAL_TRANSACTION:
            receiver_account = self._get_receiver_account(transaction)

        self._execute_transaction_by_type(
            transaction,
            sender_account,
            receiver_account
        )

    def _get_sender_account(self, transaction: Transaction):
        if transaction.sender_account_id not in self.bank.accounts:
            raise InvalidOperationError('Sender account does not exist')

        return self.bank.accounts[transaction.sender_account_id]

    def _get_receiver_account(self, transaction: Transaction):
        if transaction.receiver_account_id not in self.bank.accounts:
            raise InvalidOperationError('Receiver account does not exist')

        return self.bank.accounts[transaction.receiver_account_id]

    def _execute_transaction_by_type(self, transaction: Transaction, sender_account: BankAccount, receiver_account: BankAccount | None):
        if transaction.transaction_type == TransactionType.INTERNAL_TRANSACTION:
            self._process_internal_transaction(transaction, sender_account, receiver_account)
        elif transaction.transaction_type == TransactionType.EXTERNAL_TRANSACTION:
            self._process_external_transaction(transaction, sender_account)
        elif transaction.transaction_type == TransactionType.EXCHANGE_TRANSACTION:
            self._process_exchange_transaction(transaction, sender_account, receiver_account)
        else:
            raise InvalidOperationError('Transaction type not supported')

    def _validate_transaction(self, transaction: Transaction):
        if transaction.amount <= 0:
            raise InvalidOperationError('Amount cannot be zero')

        if transaction.commission < 0:
            raise InvalidOperationError('Commission cannot be negative')

        if transaction.sender_account_id == transaction.receiver_account_id:
            raise InvalidOperationError('Sender and receiver accounts must be different')

    def _process_internal_transaction(
        self,
        transaction: Transaction,
        sender_account: BankAccount,
        receiver_account: BankAccount | None
    ):
        if receiver_account is None:
            raise InvalidOperationError('Receiver account is required for this transaction type')

        if transaction.currency != sender_account.currency:
            raise InvalidOperationError("Transaction currency must match sender account currency")

        if transaction.currency != receiver_account.currency:
            raise InvalidOperationError("Transaction currency must match receiver account currency for internal transactions")

        total_debit = transaction.amount + transaction.commission

        receiver_account.check_status()
        receiver_account.check_amount(transaction.amount)

        sender_account.withdraw(total_debit)
        receiver_account.deposit(transaction.amount)

    def _process_external_transaction(
        self,
        transaction: Transaction,
        sender_account: BankAccount,
    ):
        if transaction.currency != sender_account.currency:
            raise InvalidOperationError("Transaction currency must match sender account currency")

        total_debit = transaction.amount + transaction.commission
        sender_account.withdraw(total_debit)
        # receiver_account.deposit(transaction.amout) Данный перевод не делается потому что счет вне этого банка

    def _get_exchange_rate(
        self,
        from_currency: CurrencyType,
        to_currency: CurrencyType
    ):
        if from_currency == to_currency:
            return 1.0

        key = (from_currency, to_currency)
        if key not in _EXCHANGE_RATES:
            raise InvalidOperationError('Exchange rate not available for this currency pair')

        return _EXCHANGE_RATES[key]

    def _process_exchange_transaction(
        self,
        transaction: Transaction,
        sender_account: BankAccount,
        receiver_account: BankAccount | None
    ):
        if receiver_account is None:
            raise InvalidOperationError('Receiver account is required for this transaction type')

        if transaction.currency != sender_account.currency:
            raise InvalidOperationError('Transaction currency must match sender account currency')


        rate = self._get_exchange_rate(transaction.currency, receiver_account.currency)

        converted_amount = transaction.amount * rate
        total_debit = transaction.amount + transaction.commission

        receiver_account.check_status()
        receiver_account.check_amount(transaction.amount)
        sender_account.withdraw(total_debit)
        receiver_account.deposit(converted_amount)

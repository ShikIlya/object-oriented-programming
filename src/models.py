from enum import Enum
import abc
import uuid

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
    account_id: str
    name: str
    status: AccountStatus = AccountStatus.ACTIVE
    _balance: int = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: int = 0
    ):
        self.account_id = account_id
        self.name = name
        self.status = status
        self._balance = balance

    @abc.abstractmethod
    def deposit(self, amount: int): pass

    @abc.abstractmethod
    def withdraw(self, amount: int): pass

    @abc.abstractmethod
    def get_account_info(self): pass

class BankAccount(AbstractAccount):
    currency: CurrencyType = CurrencyType.RUB

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: int = 0,
        currency: CurrencyType = CurrencyType.RUB
    ):
        super().__init__(account_id, name, status, balance)
        self.currency = currency

        if account_id is None:
            self.account_id = str(uuid.uuid4())

    def deposit(self, amount: int):
        self.check_status()
        self.check_amount(amount)
        self._balance += amount

    def withdraw(self, amount: int):
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

    def check_amount(self, amount: int):
        if amount <= 0:
            raise InvalidOperationError('Amount must be positive')
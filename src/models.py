from enum import Enum
import abc
import uuid

class AbstractAccount(abc.ABC):
    account_id: str
    name: str
    status: AccountStatus = AccountStatus.ACTIVE
    __balance: int = 0

    def __init__(self, account_id: str | None = None, name: str = '', status: AccountStatus = AccountStatus.ACTIVE, balance: int = 0):
        self.account_id = account_id
        self.name = name
        self.status = status
        self.__balance = balance

    @abstractmethod
    def deposit(self, amount: int): pass

    @abstractmethod
    def withdraw(self, amount: int): pass

    @abstractmethod
    def get_account_info(self): pass

class BankAccount(AbstractAccount):
    currency: CurrencyType = CurrencyType.RUB

    def __init__(self, currency: CurrencyType = CurrencyType.RUB):
        super().__init__(account_id, name, status, balance)
        self.currency = currency

        if account_id is None:
            self.account_id = str(uuid.uuid4())


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
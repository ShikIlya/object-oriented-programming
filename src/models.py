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

        if account_id is None:
            self.account_id = str(uuid.uuid4())

        if balance < 0:
            raise InvalidOperationError('Initial balance cannot be negative')
        else:
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

    def __str__(self):
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balace}{self.currency.value}"

class SavingsAccount(BankAccount):
    _min_balance: int = 0
    interest_rest: int = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: int = 0,
        currency: CurrencyType = CurrencyType.RUB,
        min_balance: int = 0,
        interest_rest: int = 0
    ):
        super().__init__(account_id, name, status, balance, currency)

        if min_balance < 0:
            raise InvalidOperationError('Initial minimun balance cannot be negative')
        else:
            self.min_balance = min_balance

        if min_balance > balance:
            raise InvalidOperationError('Balance cannot be less than the minimum balance')

        if interest_rest < 0:
            raise InvalidOperationError('Interest rest cannot be negative')
        else:
            self.interest_rest = interest_rest

    def withdraw(self, amount: int):
        self.check_status()
        self.check_amount(amount)

        if self._balance - amount > self._min_balance:
            raise InsufficientFundsError('Withdrawal would violate the minimum balance')

        self._balance -= amount

    def get_account_info(self):
        return {
            "account_id": self.account_id,
            "name": self.name,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
            "min_balance": self.min_balance,
            "interest_rest": self.interest_rest,
        }

    def __str__(self):
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balace}{self.currency.value} {self.min_balance} {self.interest_rest}"

    def apply_monthly_interest(self):
        self._balance = self.balance * (1 + self.interest_rest / 100)

class PremiumAccount(BankAccount):
    commission: int = 0
    overdraft: int = 0
    limit: int = 0

    def __init__(
        self,
        account_id: str | None = None,
        name: str = '',
        status: AccountStatus = AccountStatus.ACTIVE,
        balance: int = 0,
        currency: CurrencyType = CurrencyType.RUB,
        commission: int = 0,
        overdraft: int = 0,
        limit: int = 0
    ):
        super().__init(account_id, name, status, balance, currency)

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

    def withdraw(self, amount: int):
        self.check_status()
        self.check_amount(amount)

        if self.limit < amount:
            raise InvalidOperationError('Limit cannot be less than amount')

        if self._balance - amount - self.commission >= -self.overdraft:
            _balance -= amount + self.commission
        else:
            raise InsufficientFundsError('Amount and commission exceed overdraft')

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
        return f"{self.account_id[-4:]} {self.name} {self.status.value} {self._balace}{self.currency.value} {self.commission} {self.overdraft} {self.limit}"

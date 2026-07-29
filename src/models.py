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

    def withdraw(self, amount: float):
        self.check_status()
        self.check_amount(amount)

        if self.limit < amount:
            raise InvalidOperationError('Limit cannot be less than amount')

        if self._balance - amount - self.commission >= -self.overdraft:
            self._balance -= amount + self.commission
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
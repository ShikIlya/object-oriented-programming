from enum import Enum

class AbstractAccount:
    id: int
    name: str
    status: AccountStatus = AccountStatus.ACTIVE
    __balance: int = 0

    # def deposit(self, amount: int):
    #
    # def withdraw(self, amount: int):
    #
    # def get_account_info(self):

# class BankAccount(AbstractAccount):

class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"
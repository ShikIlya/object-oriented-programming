from models import (
    Bank,
    TransactionQueue,
    AuditLog,
    RiskAnalyzer,
    TransactionProcessor,
    AccountType,
    CurrencyType,
    TransactionType,
    TransactionPriority,
    Stock,
    Bond,
    Etf,
    TransactionStatus
)
from reports import (
    ReportBuilder
)
from datetime import datetime

DEMO_CLIENTS = [
    {
        "client_id": "client_1",
        "name": "Ivan Petrov",
        "phone_number": "+79990000001",
        "email": "ivan@example.com",
        "age": 28,
        "password": "ivan123",
    },
    {
        "client_id": "client_2",
        "name": "Anna Smirnova",
        "phone_number": "+79990000002",
        "email": "anna@example.com",
        "age": 31,
        "password": "anna123",
    },
    {
        "client_id": "client_3",
        "name": "Sergey Volkov",
        "phone_number": "+79990000003",
        "email": "sergey@example.com",
        "age": 45,
        "password": "sergey123",
    },
    {
        "client_id": "client_4",
        "name": "Maria Orlova",
        "phone_number": "+79990000004",
        "email": "maria@example.com",
        "age": 26,
        "password": "maria123",
    },
    {
        "client_id": "client_5",
        "name": "Dmitry Kozlov",
        "phone_number": "+79990000005",
        "email": "dmitry@example.com",
        "age": 39,
        "password": "dmitry123",
    },
]

DEMO_ACCOUNTS = [
    {
        "account_id": "acc_1",
        "client_id": "client_1",
        "account_type": AccountType.BANK,
        "name": "Ivan salary",
        "balance": 120000,
        "currency": CurrencyType.RUB,
    },
    {
        "account_id": "acc_2",
        "client_id": "client_1",
        "account_type": AccountType.SAVINGS,
        "name": "Ivan savings",
        "balance": 300000,
        "currency": CurrencyType.RUB,
        "min_balance": 50000,
        "interest_rate": 5.0,
    },
    {
        "account_id": "acc_3",
        "client_id": "client_2",
        "account_type": AccountType.BANK,
        "name": "Anna main",
        "balance": 2500,
        "currency": CurrencyType.USD,
    },
    {
        "account_id": "acc_4",
        "client_id": "client_2",
        "account_type": AccountType.PREMIUM,
        "name": "Anna premium",
        "balance": 10000,
        "currency": CurrencyType.USD,
        "commission": 1.5,
        "overdraft": 3000,
        "limit": 15000,
    },
    {
        "account_id": "acc_5",
        "client_id": "client_3",
        "account_type": AccountType.BANK,
        "name": "Sergey daily",
        "balance": 80000,
        "currency": CurrencyType.RUB,
    },
    {
        "account_id": "acc_6",
        "client_id": "client_3",
        "account_type": AccountType.SAVINGS,
        "name": "Sergey reserve",
        "balance": 500000,
        "currency": CurrencyType.EUR,
        "min_balance": 100000,
        "interest_rate": 4.2,
    },
    {
        "account_id": "acc_7",
        "client_id": "client_4",
        "account_type": AccountType.BANK,
        "name": "Maria card",
        "balance": 150000,
        "currency": CurrencyType.RUB,
    },
    {
        "account_id": "acc_8",
        "client_id": "client_4",
        "account_type": AccountType.PREMIUM,
        "name": "Maria premium",
        "balance": 7000,
        "currency": CurrencyType.EUR,
        "commission": 2.0,
        "overdraft": 2000,
        "limit": 8000,
    },
    {
        "account_id": "acc_9",
        "client_id": "client_5",
        "account_type": AccountType.BANK,
        "name": "Dmitry main",
        "balance": 200000,
        "currency": CurrencyType.RUB,
    },
    {
        "account_id": "acc_10",
        "client_id": "client_5",
        "account_type": AccountType.SAVINGS,
        "name": "Dmitry savings",
        "balance": 450000,
        "currency": CurrencyType.CNY,
        "min_balance": 100000,
        "interest_rate": 3.8,
    },
    {
        "account_id": "acc_11",
        "client_id": "client_1",
        "account_type": AccountType.INVESTMENT,
        "name": "Ivan investments",
        "balance": 200000,
        "currency": CurrencyType.RUB,
        "stocks": [
            Stock(id="stock_1", name="SBER", price=250.0, quantity=100),
            Stock(id="stock_2", name="GAZP", price=180.0, quantity=150),
        ],
        "bonds": [
            Bond(id="bond_1", name="OFZ-26", price=950.0, quantity=50),
        ],
        "etf": [
            Etf(id="etf_1", name="VTB SP500", price=1200.0, quantity=30),
        ],
    },
]

def create_demo_clients(bank: Bank):
    for client_data in DEMO_CLIENTS:
        bank.add_client(**client_data)


def create_demo_accounts(bank: Bank):
    created_accounts = {}

    for account_data in DEMO_ACCOUNTS:
        data = account_data.copy()
        demo_account_id = data.pop("account_id")

        account = bank.open_account(**data)
        created_accounts[demo_account_id] = account.account_id

    return created_accounts

def build_demo_transactions():
    transactions = []
    tx_number = 1

    def add_transaction(
        amount,
        currency,
        commission,
        sender_account_id,
        receiver_account_id,
        transaction_type,
        priority,
    ):
        nonlocal tx_number

        transactions.append({
            "transaction_id": f"tx_{tx_number}",
            "amount": amount,
            "currency": currency,
            "commission": commission,
            "sender_account_id": sender_account_id,
            "receiver_account_id": receiver_account_id,
            "transaction_type": transaction_type,
            "priority": priority,
        })
        tx_number += 1

    valid_patterns = [
        (10000, CurrencyType.RUB, 50, "acc_1", "acc_5", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
        (15000, CurrencyType.RUB, 50, "acc_5", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.LOW),
        (5000, CurrencyType.USD, 20, "acc_3", "external_usd_1", TransactionType.EXTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
        (20000, CurrencyType.RUB, 100, "acc_9", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (1000, CurrencyType.USD, 10, "acc_3", "acc_8", TransactionType.EXCHANGE_TRANSACTION, TransactionPriority.MEDIUM),
        (7000, CurrencyType.RUB, 30, "acc_7", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.LOW),
        (2500, CurrencyType.EUR, 15, "acc_8", "external_eur_1", TransactionType.EXTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
        (12000, CurrencyType.RUB, 40, "acc_1", "acc_9", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
    ]

    for _ in range(3):
        for pattern in valid_patterns:
            add_transaction(*pattern)

    suspicious_patterns = [
        (150000, CurrencyType.RUB, 100, "acc_9", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (120000, CurrencyType.RUB, 100, "acc_9", "acc_5", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (110000, CurrencyType.RUB, 100, "acc_9", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (130000, CurrencyType.RUB, 100, "acc_9", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (125000, CurrencyType.RUB, 100, "acc_9", "acc_5", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (140000, CurrencyType.RUB, 100, "acc_9", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (170000, CurrencyType.RUB, 100, "acc_1", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (180000, CurrencyType.RUB, 100, "acc_5", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
    ]

    for pattern in suspicious_patterns:
        add_transaction(*pattern)

    invalid_patterns = [
        (-1000, CurrencyType.RUB, 10, "acc_1", "acc_5", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.LOW),
        (99999999, CurrencyType.RUB, 100, "acc_1", "acc_5", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (5000, CurrencyType.RUB, -10, "acc_5", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.LOW),
        (3000, CurrencyType.RUB, 10, "acc_1", "acc_1", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
        (0, CurrencyType.USD, 10, "acc_3", "external_usd_2", TransactionType.EXTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
        (999999, CurrencyType.USD, 10, "acc_3", "external_usd_3", TransactionType.EXTERNAL_TRANSACTION, TransactionPriority.HIGH),
        (900000, CurrencyType.EUR, 20, "acc_8", "acc_3", TransactionType.EXCHANGE_TRANSACTION, TransactionPriority.HIGH),
        (40000, CurrencyType.RUB, 10, "acc_4", "acc_7", TransactionType.INTERNAL_TRANSACTION, TransactionPriority.MEDIUM),
    ]

    for pattern in invalid_patterns:
        add_transaction(*pattern)

    return transactions


def create_demo_transactions(
    bank: Bank,
    queue: TransactionQueue,
    account_ids: dict[str, str],
    demo_transactions: list[dict],
):
    created_transactions = []

    for transaction_data in demo_transactions:
        data = transaction_data.copy()
        transaction_id = data.pop("transaction_id")

        try:
            sender_demo_id = data["sender_account_id"]
            data["sender_account_id"] = account_ids[sender_demo_id]

            if data["transaction_type"] != TransactionType.EXTERNAL_TRANSACTION:
                receiver_demo_id = data["receiver_account_id"]
                data["receiver_account_id"] = account_ids[receiver_demo_id]

            transaction = bank.create_transaction(
                queue=queue,
                transaction_id=transaction_id,
                **data
            )
            created_transactions.append(transaction)

            print(
                f'Queued: {transaction.transaction_id} | '
                f'{transaction.transaction_type.name} | '
                f'{transaction.amount} {transaction.currency.value}'
            )

        except Exception as ex:
            print(f'Rejected on creation: {transaction_id} | {ex}')

    return created_transactions

def process_all_transactions(
    bank: Bank,
    queue: TransactionQueue,
    processor: TransactionProcessor,
):
    processed_count = 0

    while True:
        if queue.has_available_transactions():
            transaction = queue.get_next_transaction()

            processor.process_next_transaction(queue)
            processed_count += 1

            if transaction.failure_reason is not None:
                print(f"Reason: {transaction.failure_reason}")

            continue

        retry_transactions = [
            t for t in queue.transactions
            if t.status is TransactionStatus.PENDING
            and t.available_at is not None
        ]

        if not retry_transactions:
            break

        for t in retry_transactions:
            t.available_at = datetime.now()

    summary = {
        "PENDING": 0,
        "PROCESSING": 0,
        "COMPLETED": 0,
        "FAILED": 0,
        "CANCELED": 0,
        "BLOCKED": 0,
    }

    for t in bank.transactions:
        summary[t.status.name] += 1

    for status, count in summary.items():
        print(f"  {status}: {count}")

    pending_with_reason = [
        t for t in bank.transactions
        if t.status is TransactionStatus.PENDING
        and t.failure_reason is not None
    ]

    if pending_with_reason:
        for t in pending_with_reason:
            print(f"  {t.transaction_id}: {t.failure_reason}")

def show_client_accounts(bank: Bank, client_id: str):
    client = bank.clients[client_id]

    print(f'\nClient accounts: {client.name}')

    for account_id in client.accounts:
        account = bank.accounts[account_id]
        print(account.get_account_info())


def show_client_history(bank: Bank, client_id: str):
    client = bank.clients[client_id]
    client_account_ids = set(client.accounts)

    history = [
        transaction
        for transaction in bank.transactions
        if transaction.sender_account_id in client_account_ids
        or transaction.receiver_account_id in client_account_ids
    ]

    print(f'\nTransaction history: {client.name}')
    print(f'Total transactions: {len(history)}')

    for transaction in history:
        print(
            f'{transaction.transaction_id} | '
            f'{transaction.transaction_type.name} | '
            f'{transaction.amount} {transaction.currency.value} | '
            f'{transaction.status.name}'
        )


def show_suspicious_transactions(bank: Bank, risk_analyzer: RiskAnalyzer):
    print('\nSuspicious transactions:')

    suspicious = []

    for transaction in bank.transactions:
        risk_level = risk_analyzer.analyze_risk(transaction)

        if risk_level.name in ('MEDIUM', 'HIGH') and transaction.status.name != 'CANCELED':
            suspicious.append((transaction, risk_level))

    print(f'Total suspicious: {len(suspicious)}')

    for transaction, risk_level in suspicious:
        print(
            f'{transaction.transaction_id} | '
            f'{transaction.amount} {transaction.currency.value} | '
            f'{transaction.status.name} | '
            f'{risk_level.name}'
        )


def show_reports(bank: Bank):
    print('\nTop-3 clients:')
    ranking = bank.get_clients_ranking()[:3]

    for index, client_data in enumerate(ranking, start=1):
        print(
            f'{index}. {client_data["name"]} | '
            f'{client_data["total_balance"]}'
        )

    print('\nTransaction statistics:')

    stats = {
        'PENDING': 0,
        'PROCESSING': 0,
        'COMPLETED': 0,
        'FAILED': 0,
        'CANCELED': 0,
        'BLOCKED': 0,
    }

    for transaction in bank.transactions:
        stats[transaction.status.name] += 1

    for status, count in stats.items():
        print(f'{status}: {count}')

    print('\nTotal bank balance:')
    print(bank.get_total_balance())

def show_audit_log(audit_log: AuditLog):
    print('\nAudit log entries:')
    print(f'Total entries: {len(audit_log.entries)}')

    if not audit_log.entries:
        return

    for entry in audit_log.entries:
        print(
            f'[{entry.timestamp.strftime("%H:%M:%S")}] '
            f'{entry.level.name:8} | '
            f'{entry.event_type:20} | '
            f'{entry.message}'
        )
        if entry.account_id:
            print(f'  Account: {entry.account_id}')
        if entry.transaction_id:
            print(f'  Transaction: {entry.transaction_id}')

    print('\nAudit log summary by level:')
    for level in [level for level in dir(audit_log.entries[0].level) if not level.startswith('_')] if audit_log.entries else []:
        pass

    level_counts = {
        'INFO': 0,
        'WARNING': 0,
        'ERROR': 0,
        'CRITICAL': 0,
    }

    for entry in audit_log.entries:
        level_counts[entry.level.name] += 1

    for level, count in level_counts.items():
        print(f'{level:8}: {count}')

def show_audit_report(audit_log: AuditLog, bank: Bank, risk_analyzer: RiskAnalyzer):
    from models import AuditReport as AuditReportModel

    report = AuditReportModel(audit_log, bank, risk_analyzer)

    print('\nAudit Report')

    print('\nSuspicious transactions report:')
    suspicious = report.get_suspicious_transactions_report()
    print(f'Total suspicious: {len(suspicious)}')

    for tx in suspicious:
        print(
            f'{tx["transaction_id"]} | '
            f'{tx["amount"]} {tx["currency"]} | '
            f'{tx["status"]} | '
            f'{tx["risk_level"]}'
        )

    print('\nError statistics:')
    error_stats = report.get_error_statistics()
    for level, count in error_stats.items():
        print(f'{level:8}: {count}')

def main():
    bank = Bank()
    queue = TransactionQueue()
    audit_log = AuditLog(file_name='audit_log.json')
    risk_analyzer = RiskAnalyzer(bank)
    processor = TransactionProcessor(bank, risk_analyzer, audit_log)

    print('Bank system initialized')
    print(f'Clients: {len(bank.clients)}')
    print(f'Accounts: {len(bank.accounts)}')
    print(f'Transactions: {len(bank.transactions)}')

    create_demo_clients(bank)
    account_ids = create_demo_accounts(bank)

    print('\nClients created:')
    print(f'Clients: {len(bank.clients)}')
    for client in bank.clients.values():
        print(f'{client.name} | {client.client_id} | {client.status.value}')

    print('\nAccounts created:')
    print(f'Accounts: {len(bank.accounts)}')
    for account in bank.accounts.values():
        print(account)

    print('\n')
    demo_transactions = build_demo_transactions()
    transactions = create_demo_transactions(bank, queue, account_ids, demo_transactions)

    print('\nTransactions registered:')
    print(f'Transactions in bank: {len(bank.transactions)}')
    print(f'Transactions successfully queued: {len(transactions)}')
    print(f'Queue size: {len(queue.transactions)}')

    process_all_transactions(bank, queue, processor)

    show_client_accounts(bank, 'client_1')

    inv_account = bank.accounts[account_ids["acc_11"]]
    print("\nInvestment account info:")
    print(inv_account.get_account_info())

    projection = inv_account.project_yearly_growth(annual_rate=12.0)
    print("\nYearly projection (12%):")
    print(f"Current value: {projection['current_value']:.2f} RUB")
    print(f"Projected value: {projection['projected_value']:.2f} RUB")
    print(f"Projected growth: {projection['projected_growth']:.2f} RUB")

    show_client_history(bank, 'client_1')
    show_suspicious_transactions(bank, risk_analyzer)
    show_reports(bank)

    show_audit_log(audit_log)
    show_audit_report(audit_log, bank, risk_analyzer)

    report_builder = ReportBuilder(bank, audit_log, risk_analyzer)

    bank_report = report_builder.build_bank_report()
    client_report = report_builder.build_client_report("client_1")
    risk_report = report_builder.build_risk_report()

    print("\nBANK REPORT")
    text = report_builder.format_as_text(bank_report)
    print(text)

    print("\nCLIENT REPORT")
    print(report_builder.format_as_text(client_report))

    print("\nRISK REPORT")
    print(report_builder.format_as_text(risk_report))

    report_builder.export_to_json(bank_report, "reports/bank_report.json")
    report_builder.export_to_json(client_report, "reports/client_report.json")
    report_builder.export_to_json(risk_report, "reports/risk_report.json")

    report_builder.save_charts(bank_report, "charts/bank_charts")
    report_builder.save_charts(client_report, "charts/client_charts")
    report_builder.save_charts(risk_report, "charts/risk_charts")

    report_builder.export_to_csv(bank_report, "reports/bank_report.csv")
    report_builder.export_to_csv(client_report, "reports/client_report.csv")
    report_builder.export_to_csv(risk_report, "reports/risk_report.csv")

    audit_log.save_to_file()
    print('\nAudit log saved to audit_log.json')

    print('\nChecklist:')
    print('Initialization: done')
    print('Simulation: done')
    print('Logging: done')
    print('User scenarios: done')
    print('Reports: done')

if __name__ == '__main__':
    main()
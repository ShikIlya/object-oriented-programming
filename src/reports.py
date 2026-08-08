from models import (
    Bank,
    AuditLog,
    RiskAnalyzer,
    CurrencyType,
    TransactionStatus, TransactionType
)
from datetime import datetime, timedelta
import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

class ReportBuilder:
    def __init__(
        self,
        bank: Bank,
        audit_log: AuditLog,
        risk_analyzer: RiskAnalyzer
    ):
        self.bank = bank
        self.audit_log = audit_log
        self.risk_analyzer = risk_analyzer

    def _transaction_effect_rub(
        self,
        transaction,
        account_ids: set[str],
    ) -> float:
        sender_in_scope = transaction.sender_account_id in account_ids
        receiver_in_scope = transaction.receiver_account_id in account_ids

        effect = 0.0

        if sender_in_scope:
            sender_account = self.bank.accounts[transaction.sender_account_id]

            debit = transaction.amount + transaction.commission

            debit += getattr(sender_account, "commission", 0.0)

            effect -= self.bank._convert_amount(
                debit,
                transaction.currency,
                CurrencyType.RUB,
            )

        if receiver_in_scope:
            receiver_account = self.bank.accounts[transaction.receiver_account_id]

            credited_amount = transaction.amount

            if transaction.transaction_type.name == TransactionType.EXCHANGE_TRANSACTION.name:
                credited_amount = self.bank._convert_amount(
                    transaction.amount,
                    transaction.currency,
                    receiver_account.currency,
                )

            effect += self.bank._convert_amount(
                credited_amount,
                receiver_account.currency,
                CurrencyType.RUB,
            )

        return effect

    def _build_balance_history(
        self,
        current_balance_rub: float,
        transactions: list,
        account_ids: set[str],
    ) -> tuple[list[str], list[float]]:
        transactions = sorted(
            transactions,
            key=lambda transaction: (
                    transaction.completed_at or transaction.created_at
            ),
        )

        if not transactions:
            return (
                [datetime.now().strftime("%d.%m.%Y %H:%M:%S")],
                [current_balance_rub],
            )

        balance_before_first = current_balance_rub

        for transaction in reversed(transactions):
            effect = self._transaction_effect_rub(transaction, account_ids)
            balance_before_first -= effect

        labels = []
        values = []

        running_balance = balance_before_first

        first_timestamp = (transactions[0].completed_at or transactions[0].created_at)

        labels.append(
            f"0 | {(first_timestamp).strftime('%d.%m.%Y %H:%M:%S')}"
        )
        values.append(running_balance)

        for index, transaction in enumerate(transactions, start=1):
            effect = self._transaction_effect_rub(transaction, account_ids)
            running_balance += effect

            timestamp = (transaction.completed_at or transaction.created_at)

            labels.append(f"{index} | {timestamp.strftime('%d.%m.%Y %H:%M:%S')}")
            values.append(running_balance)

        return labels, values

    def build_bank_report(self) -> dict:
        stats = {
            "PENDING": 0,
            "PROCESSING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "CANCELED": 0,
            "BLOCKED": 0,
        }

        for transaction in self.bank.transactions:
            stats[transaction.status.name] += 1

        total_balance = self.bank.get_total_balance()

        ranking_currency = CurrencyType.RUB
        top_clients_raw = self.bank.get_clients_ranking(ranking_currency)[:3]

        top_clients: list[dict] = []
        for index, client_data in enumerate(top_clients_raw, start=1):
            top_clients.append({
                "rank": index,
                "client_id": client_data["client_id"],
                "name": client_data["name"],
                "total_balance": client_data["total_balance"],
                "currency": client_data["currency"],
            })

        completed_transactions = [
            t for t in self.bank.transactions
            if t.status is TransactionStatus.COMPLETED
        ]

        completed_transactions.sort(
            key=lambda t: t.completed_at or t.created_at
        )

        def current_total_balance_rub() -> float:
            total = 0.0
            for currency_value, amount in total_balance.items():
                currency = CurrencyType(currency_value)
                total += self.bank._convert_amount(
                    amount,
                    currency,
                    CurrencyType.RUB,
                )
            return total

        completed_transactions = [
            transaction
            for transaction in self.bank.transactions
            if transaction.status is TransactionStatus.COMPLETED
        ]

        bank_account_ids = set(self.bank.accounts.keys())

        current_bank_balance_rub = 0.0

        for currency_value, amount in total_balance.items():
            currency = CurrencyType(currency_value)

            current_bank_balance_rub += self.bank._convert_amount(
                amount,
                currency,
                CurrencyType.RUB,
            )

        bank_balance_labels, bank_balance_values = (
            self._build_balance_history(
                current_balance_rub=current_bank_balance_rub,
                transactions=completed_transactions,
                account_ids=bank_account_ids,
            )
        )

        return {
            "report_type": "bank",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "clients_count": len(self.bank.clients),
                "accounts_count": len(self.bank.accounts),
                "transactions_count": len(self.bank.transactions),
                "total_balance": total_balance,
                "ranking_currency": ranking_currency.value,
            },
            "details": {
                "transaction_status_stats": stats,
                "top_clients": top_clients,
            },
            "charts_data": {
                "pie_chart": {
                    "title": "Transaction Status Distribution",
                    "labels": list(stats.keys()),
                    "values": list(stats.values()),
                },
                "bar_chart": {
                    "title": "Top Clients by Balance",
                    "ylabel": f"Balance ({ranking_currency.value.upper()})",
                    "labels": [client["name"] for client in top_clients],
                    "values": [client["total_balance"] for client in top_clients],
                },
                "line_chart": {
                    "title": "Bank Balance Movement",
                    "ylabel": "Balance (RUB)",
                    "labels": bank_balance_labels,
                    "values": bank_balance_values,
                },
            },
        }

    def build_client_report(self, client_id: str) -> dict:
        if client_id not in self.bank.clients:
            raise ValueError(f"Client {client_id} does not exist")

        client = self.bank.clients[client_id]

        accounts: list[dict] = []
        total_balance_rub = 0.0

        for account_id in client.accounts:
            account = self.bank.accounts[account_id]
            account_info = account.get_account_info()
            accounts.append(account_info)

            total_balance_rub += self.bank._convert_amount(
                account._balance,
                account.currency,
                CurrencyType.RUB,
            )

        # --- Accounts for bar chart ---
        account_labels: list[str] = []
        account_balances_in_rub: list[float] = []

        for account in accounts:
            account_currency = CurrencyType(account["currency"])
            converted_balance = self.bank._convert_amount(
                account["balance"],
                account_currency,
                CurrencyType.RUB,
            )

            account_labels.append(
                f'{account["name"]} ({account["currency"].upper()})'
            )
            account_balances_in_rub.append(converted_balance)

        transactions: list[dict] = []
        suspicious_transactions: list[dict] = []

        status_stats = {
            "PENDING": 0,
            "PROCESSING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "CANCELED": 0,
            "BLOCKED": 0,
        }

        client_account_ids = set(client.accounts)

        for transaction in self.bank.transactions:
            is_client_transaction = (
                    transaction.sender_account_id in client_account_ids
                    or transaction.receiver_account_id in client_account_ids
            )
            if not is_client_transaction:
                continue

            transaction_data = {
                "transaction_id": transaction.transaction_id,
                "amount": transaction.amount,
                "currency": transaction.currency.value,
                "transaction_type": transaction.transaction_type.name,
                "status": transaction.status.name,
                "sender_account_id": transaction.sender_account_id,
                "receiver_account_id": transaction.receiver_account_id,
                "commission": transaction.commission,
                "created_at": transaction.created_at.isoformat(),
                "completed_at": (
                    transaction.completed_at.isoformat()
                    if transaction.completed_at is not None
                    else None
                ),
                "failure_reason": transaction.failure_reason,
            }

            transactions.append(transaction_data)
            status_stats[transaction.status.name] += 1

            risk_level = transaction.risk_level

            if (
                risk_level is not None
                and risk_level.name in ("MEDIUM", "HIGH")
                and transaction.status is not TransactionStatus.CANCELED
            ):
                suspicious_transactions.append({
                    **transaction_data,
                    "risk_level": risk_level.name,
                })

        completed_transactions = [
            transaction
            for transaction in self.bank.transactions
            if (
                transaction.status is TransactionStatus.COMPLETED
                and (
                    transaction.sender_account_id in client_account_ids
                    or transaction.receiver_account_id in client_account_ids
                )
            )
        ]

        balance_history_labels, balance_history_values = (
            self._build_balance_history(
                current_balance_rub=total_balance_rub,
                transactions=completed_transactions,
                account_ids=client_account_ids,
            )
        )

        return {
            "report_type": "client",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "client_id": client.client_id,
                "client_name": client.name,
                "client_status": client.status.value,
                "accounts_count": len(accounts),
                "total_balance": total_balance_rub,
                "transactions_count": len(transactions),
                "suspicious_transactions_count": len(suspicious_transactions),
            },
            "details": {
                "accounts": accounts,
                "transactions": transactions,
                "suspicious_transactions": suspicious_transactions,
                "transaction_status_stats": status_stats,
            },
            "charts_data": {
                "pie_chart": {
                    "title": "Client Transaction Status Distribution",
                    "labels": list(status_stats.keys()),
                    "values": list(status_stats.values()),
                },
                "bar_chart": {
                    "title": "Client Account Balances in RUB",
                    "ylabel": "Balance (RUB)",
                    "labels": account_labels,
                    "values": account_balances_in_rub,
                },
                "line_chart": {
                    "title": "Client Balance Movement",
                    "ylabel": "Balance (RUB)",
                    "labels": balance_history_labels,
                    "values": balance_history_values,
                },
            },
        }

    def build_risk_report(self) -> dict:
        if self.risk_analyzer is None:
            raise ValueError("Risk analyzer is not configured")

        suspicious_transactions = []

        risk_level_stats = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
        }

        status_stats = {
            "PENDING": 0,
            "PROCESSING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "CANCELED": 0,
            "BLOCKED": 0,
        }

        client_risk_counts = {}

        for transaction in self.bank.transactions:
            risk_level = transaction.risk_level

            if risk_level is None:
                continue

            risk_level_stats[risk_level.name] += 1
            status_stats[transaction.status.name] += 1

            if risk_level.name in ("MEDIUM", "HIGH") and transaction.status.name != "CANCELED":
                client_id = "UNKNOWN"

                for client in self.bank.clients.values():
                    if transaction.sender_account_id in client.accounts:
                        client_id = client.client_id
                        break

                suspicious_transaction = {
                    "transaction_id": transaction.transaction_id,
                    "client_id": client_id,
                    "amount": transaction.amount,
                    "currency": transaction.currency.value,
                    "transaction_type": transaction.transaction_type.name,
                    "status": transaction.status.name,
                    "sender_account_id": transaction.sender_account_id,
                    "receiver_account_id": transaction.receiver_account_id,
                    "commission": transaction.commission,
                    "created_at": transaction.created_at.isoformat(),
                    "completed_at": (
                        transaction.completed_at.isoformat()
                        if transaction.completed_at is not None
                        else None
                    ),
                    "failure_reason": transaction.failure_reason,
                    "risk_level": risk_level.name,
                }

                suspicious_transactions.append(suspicious_transaction)

                if client_id not in client_risk_counts:
                    client_risk_counts[client_id] = 0
                client_risk_counts[client_id] += 1

        top_risky_clients = sorted(
            client_risk_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )[:5]

        top_risky_clients_data = [
            {
                "rank": index + 1,
                "client_id": client_id,
                "suspicious_transactions_count": count,
            }
            for index, (client_id, count) in enumerate(top_risky_clients)
        ]

        return {
            "report_type": "risk",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "transactions_analyzed": len(self.bank.transactions),
                "suspicious_transactions_count": len(suspicious_transactions),
                "high_risk_count": risk_level_stats["HIGH"],
                "medium_risk_count": risk_level_stats["MEDIUM"],
                "low_risk_count": risk_level_stats["LOW"],
            },
            "details": {
                "risk_level_stats": risk_level_stats,
                "transaction_status_stats": status_stats,
                "suspicious_transactions": suspicious_transactions,
                "top_risky_clients": top_risky_clients_data,
            },
            "charts_data": {
                "pie_chart": {
                    "title": "Risk Level Distribution",
                    "labels": list(risk_level_stats.keys()),
                    "values": list(risk_level_stats.values()),
                },
                "bar_chart": {
                    "title": "Top Risky Clients",
                    "ylabel": "Suspicious Transactions Count",
                    "labels": [item["client_id"] for item in top_risky_clients_data],
                    "values": [item["suspicious_transactions_count"] for item in top_risky_clients_data],
                },
                "line_chart": {
                    "title": "Suspicious Transactions Flow",
                    "ylabel": "Count",
                    "labels": ["Low", "Medium", "High"],
                    "values": [
                        risk_level_stats["LOW"],
                        risk_level_stats["MEDIUM"],
                        risk_level_stats["HIGH"],
                    ],
                },
            },
        }

    def format_as_text(self, report_data: dict) -> str:
        report_type = report_data.get("report_type", "unknown")
        generated_at = report_data.get("generated_at", "unknown")
        summary = report_data.get("summary", {})
        details = report_data.get("details", {})

        lines = []
        lines.append("=" * 60)
        lines.append(f"{report_type.upper()} REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated at: {generated_at}")
        lines.append("")

        if report_type == "bank":
            status_stats = details.get("transaction_status_stats", {})
            top_clients = details.get("top_clients", [])

            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(f"Clients: {summary.get('clients_count', 0)}")
            lines.append(f"Accounts: {summary.get('accounts_count', 0)}")
            lines.append(f"Transactions: {summary.get('transactions_count', 0)}")
            lines.append(f"Total balance: {summary.get('total_balance', 0)}")
            lines.append("")

            lines.append("TRANSACTION STATISTICS")
            lines.append("-" * 60)
            for status, count in status_stats.items():
                lines.append(f"{status}: {count}")
            lines.append("")

            lines.append("TOP CLIENTS")
            lines.append("-" * 60)
            for client in top_clients:
                lines.append(
                    f"{client.get('rank', '')}. "
                    f"{client.get('name', 'Unknown')} | "
                    f"{client.get('total_balance', 0)} "
                    f"{str(client.get('currency', '')).upper()}"
                )
        elif report_type == "client":
            accounts = details.get("accounts", [])
            transactions = details.get("transactions", [])
            suspicious_transactions = details.get("suspicious_transactions", [])
            status_stats = details.get("transaction_status_stats", {})

            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(f"Client ID: {summary.get('client_id', '')}")
            lines.append(f"Client name: {summary.get('client_name', '')}")
            lines.append(f"Client status: {summary.get('client_status', '')}")
            lines.append(f"Accounts count: {summary.get('accounts_count', 0)}")
            lines.append(f"Total balance: {summary.get('total_balance', 0)}")
            lines.append(f"Transactions count: {summary.get('transactions_count', 0)}")
            lines.append(
                f"Suspicious transactions count: "
                f"{summary.get('suspicious_transactions_count', 0)}"
            )
            lines.append("")

            lines.append("ACCOUNTS")
            lines.append("-" * 60)
            for account in accounts:
                lines.append(
                    f"{account.get('name', '')} | "
                    f"{account.get('balance', 0)} {account.get('currency', '')} | "
                    f"{account.get('status', '')}"
                )
            lines.append("")

            lines.append("TRANSACTION STATISTICS")
            lines.append("-" * 60)
            for status, count in status_stats.items():
                lines.append(f"{status}: {count}")
            lines.append("")

            lines.append("RECENT TRANSACTIONS")
            lines.append("-" * 60)
            for transaction in transactions[:10]:
                lines.append(
                    f"{transaction.get('transaction_id', '')} | "
                    f"{transaction.get('amount', 0)} {transaction.get('currency', '')} | "
                    f"{transaction.get('status', '')}"
                )
            lines.append("")

            lines.append("SUSPICIOUS TRANSACTIONS")
            lines.append("-" * 60)
            for transaction in suspicious_transactions:
                lines.append(
                    f"{transaction.get('transaction_id', '')} | "
                    f"{transaction.get('amount', 0)} {transaction.get('currency', '')} | "
                    f"{transaction.get('status', '')} | "
                    f"{transaction.get('risk_level', '')}"
                )
        elif report_type == "risk":
            risk_level_stats = details.get("risk_level_stats", {})
            status_stats = details.get("transaction_status_stats", {})
            suspicious_transactions = details.get("suspicious_transactions", [])
            top_risky_clients = details.get("top_risky_clients", [])

            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(f"Transactions analyzed: {summary.get('transactions_analyzed', 0)}")
            lines.append(
                f"Suspicious transactions count: "
                f"{summary.get('suspicious_transactions_count', 0)}"
            )
            lines.append(f"High risk count: {summary.get('high_risk_count', 0)}")
            lines.append(f"Medium risk count: {summary.get('medium_risk_count', 0)}")
            lines.append(f"Low risk count: {summary.get('low_risk_count', 0)}")
            lines.append("")

            lines.append("RISK LEVEL STATISTICS")
            lines.append("-" * 60)
            for level, count in risk_level_stats.items():
                lines.append(f"{level}: {count}")
            lines.append("")

            lines.append("TRANSACTION STATUS STATISTICS")
            lines.append("-" * 60)
            for status, count in status_stats.items():
                lines.append(f"{status}: {count}")
            lines.append("")

            lines.append("TOP RISKY CLIENTS")
            lines.append("-" * 60)
            for client in top_risky_clients:
                lines.append(
                    f"{client.get('rank', '')}. "
                    f"{client.get('client_id', 'UNKNOWN')} | "
                    f"{client.get('suspicious_transactions_count', 0)} suspicious transactions"
                )
            lines.append("")

            lines.append("SUSPICIOUS TRANSACTIONS")
            lines.append("-" * 60)
            for transaction in suspicious_transactions[:10]:
                lines.append(
                    f"{transaction.get('transaction_id', '')} | "
                    f"{transaction.get('client_id', 'UNKNOWN')} | "
                    f"{transaction.get('amount', 0)} {transaction.get('currency', '')} | "
                    f"{transaction.get('status', '')} | "
                    f"{transaction.get('risk_level', '')}"
                )
        else:
            lines.append("Unsupported report type")

        return "\n".join(lines)

    def export_to_json(self, report_data: dict, file_path: str) -> None:
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(report_data, file, ensure_ascii=False, indent=4)

    def export_to_csv(self, report_data: dict, file_path: str) -> None:
        report_type = report_data.get("report_type")
        details = report_data.get("details", {})

        if report_type == "bank":
            rows = details.get("top_clients", [])

        elif report_type == "client":
            rows = details.get("transactions", [])

        elif report_type == "risk":
            rows = details.get("suspicious_transactions", [])

        else:
            raise ValueError(f"Unsupported report type: {report_type}")

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8", newline="") as file:
            if not rows:
                file.write("")
                return

            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(rows)

    def save_charts(self, report_data: dict, output_dir: str) -> list[str]:
        charts_data = report_data.get("charts_data", {})
        report_type = report_data.get("report_type", "report")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []

        def format_number(value, _):
            return f"{value:,.0f}".replace(",", " ")

        def save_pie_chart(data: dict, filename: str):
            labels = data.get("labels", [])
            values = data.get("values", [])
            title = data.get("title", "Pie Chart")

            filtered_data = [
                (label, value)
                for label, value in zip(labels, values)
                if value > 0
            ]

            if not filtered_data:
                return

            filtered_labels = [item[0] for item in filtered_data]
            filtered_values = [item[1] for item in filtered_data]

            fig, ax = plt.subplots(figsize=(8, 5))

            wedges, _, _ = ax.pie(
                filtered_values,
                labels=None,
                autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
                startangle=90,
                pctdistance=0.7
            )

            ax.legend(
                wedges,
                filtered_labels,
                title="Categories",
                loc="center left",
                bbox_to_anchor=(1, 0.5)
            )

            ax.set_title(title)
            fig.tight_layout()

            file_path = output_path / filename
            fig.savefig(file_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            saved_files.append(str(file_path))

        def save_bar_chart(data: dict, filename: str):
            labels = data.get("labels", [])
            values = data.get("values", [])
            title = data.get("title", "Bar Chart")
            ylabel = data.get("ylabel", "Value")

            if not labels or not values:
                return

            if len(labels) != len(values):
                return

            if not all(isinstance(value, (int, float)) for value in values):
                return

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(labels, values)
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.yaxis.set_major_formatter(FuncFormatter(format_number))
            ax.tick_params(axis="x", rotation=30)
            plt.setp(ax.get_xticklabels(), ha="right")
            fig.tight_layout()

            file_path = output_path / filename
            fig.savefig(file_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            saved_files.append(str(file_path))

        def save_line_chart(data: dict, filename: str):
            labels = data.get("labels", [])
            values = data.get("values", [])
            title = data.get("title", "Line Chart")
            ylabel = data.get("ylabel", "Value")

            if not labels or not values:
                return

            if len(labels) != len(values):
                return

            if not all(isinstance(value, (int, float)) for value in values):
                return

            fig, ax = plt.subplots(figsize=(12, 6))

            x_positions = list(range(len(values)))

            ax.plot(
                x_positions,
                values,
                marker="o",
                linewidth=2,
                markersize=5,
            )

            ax.set_title(title)
            ax.set_xlabel("Transaction timeline")
            ax.set_ylabel(ylabel)

            ax.yaxis.set_major_formatter(
                FuncFormatter(format_number)
            )

            if len(labels) <= 8:
                tick_positions = x_positions
            else:
                step = max(1, len(labels) // 8)
                tick_positions = list(range(0, len(labels), step))

            ax.set_xticks(tick_positions)
            ax.set_xticklabels(
                [labels[index] for index in tick_positions],
                rotation=35,
                ha="right",
            )

            ax.grid(
                axis="y",
                linestyle="--",
                alpha=0.35,
            )

            fig.tight_layout()

            file_path = output_path / filename
            fig.savefig(
                file_path,
                dpi=300,
                bbox_inches="tight",
            )

            plt.close(fig)
            saved_files.append(str(file_path))

        pie_data = charts_data.get("pie_chart")

        if pie_data:
            save_pie_chart(pie_data, f"{report_type}_pie_chart.png")

        bar_data = charts_data.get("bar_chart")
        if bar_data:
            save_bar_chart(bar_data, f"{report_type}_bar_chart.png")

        line_data = charts_data.get("line_chart")
        if line_data:
            save_line_chart(line_data, f"{report_type}_line_chart.png")

        return saved_files
from services.ports import (
    ICacheRepository, ITransactionRepository, IBudgetRepository,
    IGoalRepository, IStatsRepository
)
from models.exceptions import DatosNoEncontradosError


class LocalRepository(ITransactionRepository, IBudgetRepository, IGoalRepository, IStatsRepository):
    def __init__(self, cache: ICacheRepository):
        self.cache = cache

    def get_transactions(self, month: str = "", category: str = "", type_: str = "") -> list:
        data = self.cache.get_cached_transactions(month)
        if not data:
            raise DatosNoEncontradosError("No hay transacciones en caché local.")
        if category:
            data = [t for t in data if t.get("category") == category or t.get("Categoría") == category]
        if type_:
            data = [t for t in data if t.get("type") == type_]
        return data

    def create_transaction(self, data: dict) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def update_transaction(self, id: str, data: dict) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def delete_transaction(self, id: str) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def bulk_delete_transactions(self, ids: list[str]) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def cache_transactions(self, transactions: list, month: str):
        self.cache.cache_transactions(transactions, month)

    def get_budgets(self, month: str = "") -> list:
        data = self.cache.get_cached_budgets(month)
        if not data:
            raise DatosNoEncontradosError("No hay presupuestos en caché local.")
        return data

    def get_budget_status(self, month: str) -> list:
        return self.get_budgets(month)

    def create_budget(self, data: dict) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def update_budget(self, id: str, data: dict) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def delete_budget(self, id: str) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def bulk_delete_budgets(self, ids: list[str]) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def cache_budgets(self, budgets: list, month: str):
        self.cache.cache_budgets(budgets, month)

    def get_goals(self) -> list:
        data = self.cache.get_cached_goals()
        if not data:
            raise DatosNoEncontradosError("No hay metas en caché local.")
        return data

    def create_goal(self, data: dict) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def deposit_to_goal(self, id: str, amount: float) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def delete_goal(self, id: str) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def bulk_delete_goals(self, ids: list[str]) -> dict:
        raise NotImplementedError("LocalRepository es solo lectura.")

    def cache_goals(self, goals: list):
        self.cache.cache_goals(goals)

    def get_summary(self, month: str) -> dict:
        transactions = self.get_transactions(month)
        income = sum(t["amount"] for t in transactions if t.get("type") == "income")
        expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
        balance = income - expense
        savings_rate = ((income - expense) / income * 100) if income > 0 else 0
        return {
            "income": income,
            "expense": expense,
            "balance": balance,
            "savingsRate": round(savings_rate, 1),
        }

    def get_category_stats(self, month: str) -> dict:
        transactions = self.get_transactions(month)
        stats = {}
        for t in transactions:
            if t.get("type") == "expense":
                cat = t.get("category", "Otros")
                stats[cat] = stats.get(cat, 0) + t["amount"]
        return stats

    def get_trends(self, months: int = 6) -> list:
        from datetime import datetime, timedelta
        trends = []
        today = datetime.now()
        for i in range(months - 1, -1, -1):
            d = today.replace(day=1) - timedelta(days=30 * i)
            m_str = d.strftime("%Y-%m")
            try:
                summary = self.get_summary(m_str)
                trends.append({
                    "month": m_str,
                    "income": summary["income"],
                    "expense": summary["expense"],
                    "balance": summary["balance"],
                })
            except DatosNoEncontradosError:
                trends.append({"month": m_str, "income": 0, "expense": 0, "balance": 0})
        return trends

    def get_top_expenses(self, month: str, limit: int = 5) -> list:
        transactions = self.get_transactions(month)
        expenses = [t for t in transactions if t.get("type") == "expense"]
        expenses.sort(key=lambda x: x["amount"], reverse=True)
        return expenses[:limit]

    def get_heatmap(self, month: str) -> dict:
        raise NotImplementedError("LocalRepository no soporta heatmap.")

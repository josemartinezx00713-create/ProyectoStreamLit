import os
import requests
from typing import Any, Optional
from services.ports import (
    IApiClient, ITransactionRepository, IBudgetRepository,
    IGoalRepository, IStatsRepository, IExchangeRateRepository
)
from models.exceptions import ApiCaidaError, DatosNoEncontradosError

API_URL = os.environ.get("FINTRACK_API_URL", "http://localhost:3000")


class ApiClient(
    IApiClient, ITransactionRepository, IBudgetRepository,
    IGoalRepository, IStatsRepository, IExchangeRateRepository
):
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        try:
            r = requests.get(self._url(path), params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            raise ApiCaidaError()
        except requests.exceptions.Timeout:
            raise ApiCaidaError("La API no respondió a tiempo.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise DatosNoEncontradosError()
            raise ApiCaidaError(f"Error HTTP {e.response.status_code}")

    def post(self, path: str, json: dict) -> Any:
        try:
            r = requests.post(self._url(path), json=json, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            raise ApiCaidaError()
        except requests.exceptions.Timeout:
            raise ApiCaidaError("La API no respondió a tiempo.")

    def patch(self, path: str, json: dict) -> Any:
        try:
            r = requests.patch(self._url(path), json=json, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            raise ApiCaidaError()
        except requests.exceptions.Timeout:
            raise ApiCaidaError("La API no respondió a tiempo.")

    def delete(self, path: str) -> Any:
        try:
            r = requests.delete(self._url(path), timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            raise ApiCaidaError()
        except requests.exceptions.Timeout:
            raise ApiCaidaError("La API no respondió a tiempo.")

    def check_status(self) -> bool:
        try:
            r = requests.get(self._url("/"), timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # -- Transactions --
    def get_transactions(self, month: str = "", category: str = "", type_: str = "") -> list:
        params = {}
        if month: params["month"] = month
        if category: params["category"] = category
        if type_: params["type"] = type_
        return self.get("/transactions", params)

    def create_transaction(self, data: dict) -> dict:
        return self.post("/transactions", data)

    def update_transaction(self, id: str, data: dict) -> dict:
        return self.patch(f"/transactions/{id}", data)

    def delete_transaction(self, id: str) -> dict:
        return self.delete(f"/transactions/{id}")

    def bulk_delete_transactions(self, ids: list[str]) -> dict:
        return self.post("/transactions/bulk-delete", {"ids": ids})

    def cache_transactions(self, transactions: list, month: str):
        pass

    # -- Budgets --
    def get_budgets(self, month: str = "") -> list:
        params = {}
        if month: params["month"] = month
        return self.get("/budgets", params)

    def get_budget_status(self, month: str) -> list:
        return self.get("/budgets/status", {"month": month})

    def create_budget(self, data: dict) -> dict:
        return self.post("/budgets", data)

    def update_budget(self, id: str, data: dict) -> dict:
        return self.patch(f"/budgets/{id}", data)

    def delete_budget(self, id: str) -> dict:
        return self.delete(f"/budgets/{id}")

    def bulk_delete_budgets(self, ids: list[str]) -> dict:
        return self.post("/budgets/bulk-delete", {"ids": ids})

    def cache_budgets(self, budgets: list, month: str):
        pass

    # -- Goals --
    def get_goals(self) -> list:
        return self.get("/goals")

    def create_goal(self, data: dict) -> dict:
        return self.post("/goals", data)

    def deposit_to_goal(self, id: str, amount: float) -> dict:
        return self.patch(f"/goals/{id}/deposit", {"amount": amount})

    def delete_goal(self, id: str) -> dict:
        return self.delete(f"/goals/{id}")

    def bulk_delete_goals(self, ids: list[str]) -> dict:
        return self.post("/goals/bulk-delete", {"ids": ids})

    def cache_goals(self, goals: list):
        pass

    # -- Stats --
    def get_summary(self, month: str) -> dict:
        return self.get("/stats/summary", {"month": month})

    def get_category_stats(self, month: str) -> dict:
        return self.get("/stats/by-category", {"month": month})

    def get_trends(self, months: int = 6) -> list:
        return self.get("/stats/trends", {"months": str(months)})

    def get_top_expenses(self, month: str, limit: int = 5) -> list:
        return self.get("/stats/top-expenses", {"month": month, "limit": str(limit)})

    def get_heatmap(self, month: str) -> dict:
        return self.get("/stats/heatmap", {"month": month})

    # -- Exchange Rates --
    def get_exchange_rates(self) -> dict:
        return self.get("/exchange-rates")

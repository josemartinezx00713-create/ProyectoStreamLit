import streamlit as st
from dataclasses import dataclass
from services.ports import (
    IApiClient, ITransactionRepository, IBudgetRepository,
    IGoalRepository, IStatsRepository, IExchangeRateRepository,
    ICacheRepository
)
from services.api_client import ApiClient
from services.cache_service import CacheService
from services.currency_service import CurrencyService, CURRENCIES as _CURRENCIES
from services.local_repository import LocalRepository
from ui.styles import apply_global_css as _apply_css
from ui.navigation import render_sidebar


@dataclass
class Container:
    api_client: ApiClient
    cache: CacheService
    currency_service: CurrencyService
    local_repo: LocalRepository


def build_container() -> Container:
    api_client = ApiClient()
    cache = CacheService()
    local_repo = LocalRepository(cache)
    currency_service = CurrencyService(api_client, cache)
    return Container(
        api_client=api_client,
        cache=cache,
        currency_service=currency_service,
        local_repo=local_repo,
    )


_container: Container | None = None


def _get_container() -> Container:
    global _container
    if _container is None:
        _container = build_container()
    return _container


def apply_global_css():
    c = _get_container()
    _apply_css()
    render_sidebar(c.api_client, c.currency_service)


def get_currency():
    return _get_container().currency_service.get_currency_symbol()


def get_currency_code():
    return _get_container().currency_service.get_currency_code()


def get_rate():
    return _get_container().currency_service.get_rate()


def fmt_money(amount):
    return _get_container().currency_service.fmt_money(amount)


def fmt_html_money(amount):
    return _get_container().currency_service.fmt_html_money(amount)


def get_currency_string():
    return _get_container().currency_service.get_currency_string()


def set_currency_string(symbol):
    return _get_container().currency_service.set_currency_string(symbol)


def check_api_status():
    return _get_container().api_client.check_status()


def render_connection_status():
    from ui.navigation import _render_connection_status
    _render_connection_status(_get_container().api_client)


def render_currency_selector():
    from ui.navigation import _render_currency_selector
    _render_currency_selector(_get_container().currency_service)


def get_api_client() -> ApiClient:
    return _get_container().api_client


def get_local_repo() -> LocalRepository:
    return _get_container().local_repo


CURRENCIES = _CURRENCIES

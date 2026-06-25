import json
import os
from services.ports import IExchangeRateRepository, ICacheRepository

PREFS_FILE = "user_preferences.json"
BASE_CURRENCY = "NIO"

CURRENCIES = [
    "$ (USD)", "€ (EUR)", "£ (GBP)", "¥ (JPY)",
    "$ (MXN)", "$ (COP)", "$ (ARS)", "$ (CLP)",
    "S/. (PEN)", "R$ (BRL)", "C$ (NIO)"
]


class CurrencyService:
    def __init__(self, exchange_repo: IExchangeRateRepository, cache: ICacheRepository):
        self.exchange_repo = exchange_repo
        self.cache = cache

    def get_currency_string(self) -> str:
        if not os.path.exists(PREFS_FILE):
            return "C$ (NIO)"
        try:
            with open(PREFS_FILE, "r") as f:
                data = json.load(f)
                val = data.get("currency", "C$ (NIO)")
                if len(val) > 10:
                    return "C$ (NIO)"
                return val
        except Exception:
            return "C$ (NIO)"

    def set_currency_string(self, symbol: str):
        with open(PREFS_FILE, "w") as f:
            json.dump({"currency": symbol}, f)

    def get_currency_code(self) -> str:
        return self.get_currency_string().split("(")[-1].replace(")", "").strip()

    def get_currency_symbol(self) -> str:
        return self.get_currency_string().split(" ")[0]

    def get_rate(self) -> float:
        code = self.get_currency_code()
        if code == BASE_CURRENCY:
            return 1.0

        local = self.cache.get_rate(BASE_CURRENCY, code)
        if local is not None:
            return local

        try:
            data = self.exchange_repo.get_exchange_rates()
            rates = data.get("rates", {})
            if rates:
                self.cache.cache_rates(BASE_CURRENCY, rates)
            return rates.get(code, 1.0)
        except Exception:
            return 1.0

    def fmt_money(self, amount: float) -> str:
        rate = self.get_rate()
        sym = self.get_currency_symbol()
        converted = amount * rate
        return f"{sym}{converted:,.2f}"

    def fmt_html_money(self, amount: float) -> str:
        return self.fmt_money(amount).replace("$", "&#36;")

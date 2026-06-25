import streamlit as st
from services.ports import IApiClient
from services.currency_service import CurrencyService, CURRENCIES


def render_sidebar(api_client: IApiClient, currency_service: CurrencyService):
    _render_connection_status(api_client)
    _render_currency_selector(currency_service)


def _render_connection_status(api_client: IApiClient):
    online = api_client.check_status()
    if online:
        st.sidebar.markdown(
            "<div style='display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(16,185,129,0.1);border-radius:8px;margin:8px 0'>"
            "<span style='color:#10B981;font-size:1.2rem;'>⬤</span>"
            "<span style='color:#D1D5DB;font-size:0.85rem;'>API Conectada</span>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            "<div style='display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(239,68,68,0.1);border-radius:8px;margin:8px 0'>"
            "<span style='color:#EF4444;font-size:1.2rem;'>⬤</span>"
            "<span style='color:#D1D5DB;font-size:0.85rem;'>API Desconectada</span>"
            "</div>",
            unsafe_allow_html=True
        )


def _render_currency_selector(currency_service: CurrencyService):
    curr = currency_service.get_currency_string()
    idx = 0
    if curr in CURRENCIES:
        idx = CURRENCIES.index(curr)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Mercado (En Vivo)**")
    sel = st.sidebar.selectbox("Moneda de Pantalla", CURRENCIES, index=idx)

    if sel != curr:
        currency_service.set_currency_string(sel)
        st.cache_data.clear()
        st.rerun()

    rate = currency_service.get_rate()
    code = currency_service.get_currency_code()
    if code != "NIO":
        st.sidebar.caption(f"API: 1 NIO = {rate:,.2f} {code}")
    else:
        st.sidebar.caption("Moneda Origen de BD")

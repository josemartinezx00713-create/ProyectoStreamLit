import streamlit as st
import pandas as pd
from datetime import datetime
from ui_tweak import apply_global_css, fmt_money, get_rate, get_api_client, get_local_repo
from ui.components import render_kpi_card, render_donut_chart, render_trend_chart, render_top_expenses
from models.exceptions import ApiCaidaError, DatosNoEncontradosError

st.set_page_config(page_title="FinTrack", layout="wide", initial_sidebar_state="expanded")
apply_global_css()

api = get_api_client()
local_repo = get_local_repo()

st.title("Panel Principal")

current_month = datetime.now()
month_input = st.date_input("Selecciona el Mes (Usa el calendario)", current_month).strftime("%Y-%m")

def get_prev_month(month_str: str) -> str:
    try:
        y, m = map(int, month_str.split("-"))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        return f"{y}-{m:02d}"
    except:
        return ""

def calc_delta(curr, prev, prev_label, invert_colors=False):
    if not prev or prev == 0:
        return ""
    pct = ((curr - prev) / prev) * 100
    if pct > 0:
        css = "delta-positive" if not invert_colors else "delta-negative"
        return f'<div class="delta-badge {css}">+{pct:.1f}% vs {prev_label}</div>'
    elif pct < 0:
        css = "delta-negative" if not invert_colors else "delta-positive"
        return f'<div class="delta-badge {css}">{pct:.1f}% vs {prev_label}</div>'
    else:
        return f'<div class="delta-badge delta-neutral">0% vs {prev_label}</div>'

def fetch_summary(month):
    try:
        data = api.get_summary(month)
        try:
            txns = api.get_transactions(month)
            if txns:
                local_repo.cache_transactions(txns, month)
        except Exception:
            pass
        return data
    except ApiCaidaError:
        try:
            data = local_repo.get_summary(month)
            st.warning("Usando datos locales (API no disponible)")
            return data
        except DatosNoEncontradosError:
            return None
    except DatosNoEncontradosError:
        return None

summary = fetch_summary(month_input)

prev_month_input = get_prev_month(month_input)
prev_summary = fetch_summary(prev_month_input) if prev_month_input else None

if summary:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        d_inc = calc_delta(summary["income"], prev_summary["income"] if prev_summary else 0, prev_month_input)
        render_kpi_card(c1, "Ingresos Totales", fmt_money(summary["income"]), d_inc, "card-income", "payments", "#10B981")
    with c2:
        d_exp = calc_delta(summary["expense"], prev_summary["expense"] if prev_summary else 0, prev_month_input, invert_colors=True)
        render_kpi_card(c2, "Gastos Totales", fmt_money(summary["expense"]), d_exp, "card-expense", "credit_card", "#EF4444")
    with c3:
        d_bal = calc_delta(summary["balance"], prev_summary["balance"] if prev_summary else 0, prev_month_input)
        render_kpi_card(c3, "Balance Neto", fmt_money(summary["balance"]), d_bal, "card-balance", "account_balance", "#14B8A6")
    with c4:
        d_sav = calc_delta(summary["savingsRate"], prev_summary["savingsRate"] if prev_summary else 0, prev_month_input)
        render_kpi_card(c4, "Tasa de Ahorro", f'{summary["savingsRate"]:,.1f}%', d_sav, "card-savings", "trending_up", "#14B8A6")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown('<div class="section-card"><h3>Distribución de Gastos</h3>', unsafe_allow_html=True)
        try:
            cat_stats = api.get_category_stats(month_input)
        except ApiCaidaError:
            try:
                cat_stats = local_repo.get_category_stats(month_input)
            except DatosNoEncontradosError:
                cat_stats = {}
        render_donut_chart(cat_stats, fmt_money)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><h3>Tendencia (Últimos 6 Meses)</h3>', unsafe_allow_html=True)
        try:
            trends = api.get_trends()
        except ApiCaidaError:
            try:
                trends = local_repo.get_trends()
            except DatosNoEncontradosError:
                trends = []
        render_trend_chart(trends, get_rate())
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card" style="margin-bottom: 0px;"><h3>Categorías de Gastos Top</h3>', unsafe_allow_html=True)
    try:
        top_exp = api.get_top_expenses(month_input)
    except ApiCaidaError:
        try:
            top_exp = local_repo.get_top_expenses(month_input)
        except DatosNoEncontradosError:
            top_exp = []
    render_top_expenses(top_exp, summary.get("expense", 1), fmt_money)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Utiliza el panel superior para seleccionar el mes y ver datos.")

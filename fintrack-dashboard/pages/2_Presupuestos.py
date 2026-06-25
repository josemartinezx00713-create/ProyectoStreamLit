import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from ui_tweak import apply_global_css, fmt_money, fmt_html_money, get_api_client, get_local_repo
from models.exceptions import ApiCaidaError, DatosNoEncontradosError

st.set_page_config(page_title="Presupuestos", layout="wide")
apply_global_css()

api = get_api_client()
local_repo = get_local_repo()
CATEGORIAS = ["Comida", "Transporte", "Vivienda", "Salud", "Entretenimiento", "Compras", "Educación", "Servicios", "Ahorros", "Otros"]

st.title("Presupuestos")

current_month = datetime.now()
month_input = st.date_input("Seleccionar Mes (Usa el calendario)", current_month).strftime("%Y-%m")

with st.sidebar.expander("Establecer Presupuesto", expanded=False):
    with st.form("add_budget"):
        b_cat = st.selectbox("Categoría", CATEGORIAS)
        b_limit = st.number_input("Límite Crudo Numérico", min_value=1.0, step=10.0)
        submitted = st.form_submit_button("Crear")
        if submitted:
            try:
                api.create_budget({"category": b_cat, "limitAmount": b_limit, "month": month_input})
                st.success("¡Presupuesto guardado!")
                st.cache_data.clear()
                st.rerun()
            except ApiCaidaError as e:
                st.error(f"Error de conexión: {e.message}")

try:
    budgets = api.get_budget_status(month_input)
    if budgets:
        local_repo.cache_budgets(budgets, month_input)
except ApiCaidaError:
    try:
        budgets = local_repo.get_budgets(month_input)
        st.warning("Usando datos locales (API no disponible)")
    except DatosNoEncontradosError:
        budgets = []
        st.info("No hay datos de presupuestos en caché local.")

if budgets:
    total_limes = sum(b["limitAmount"] for b in budgets)
    total_spent = sum(b.get("spent", 0) for b in budgets)
    global_pct = (total_spent / total_limes * 100) if total_limes > 0 else 0

    st.markdown("### Salud Global")
    col_ring, col_stats = st.columns([1, 3])
    with col_ring:
        ring_color = "#10B981" if global_pct < 70 else ("#FBBF24" if global_pct < 90 else "#EF4444")
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=global_pct,
            number={"suffix": "%", "font": {"color": ring_color}},
            gauge={"axis": {"range": [None, 100], "visible": False},
                   "bar": {"color": ring_color}, "bgcolor": "rgba(255,255,255,0.05)", "borderwidth": 0}
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font={"color":"#a0aec0"})
        st.plotly_chart(fig, width="stretch")
    with col_stats:
        st.markdown(f"<br><br><h2 style='color: {ring_color}'>Has gastado {fmt_html_money(total_spent)}</h2><h4>de {fmt_html_money(total_limes)} presupuestados</h4>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Vista de Consumo")

    for b in budgets:
        pct = b.get("percentUsed", 0)
        spent = b.get("spent", 0)
        bar_color = "#10B981" if pct < 70 else ("#FBBF24" if pct < 90 else "#EF4444")
        clamped_pct = min(pct, 100)

        st.markdown(f"""<div class="budget-card" style="border-left-color: {bar_color};">
    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <div class="budget-title">{b["category"]}</div>
            <div class="budget-limits">Límite Mensual: <b>{fmt_html_money(b["limitAmount"])}</b></div>
        </div>
    </div>
    <div class="bar-container">
        <div class="bar-fill" style="width: {clamped_pct}%; background-color: {bar_color};"></div>
    </div>
    <div class="budget-stats" style="color: {bar_color};">
        Gastado: {fmt_html_money(spent)} ({pct:.1f}%)
    </div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Ajuste de Presupuestos")
    st.caption("Marca la casilla 'Seleccionar' en un presupuesto para editarlo o eliminarlo.")

    df = pd.DataFrame(budgets)
    df_view = df.copy()
    df_view["Límite"] = df_view["limitAmount"].apply(fmt_money)
    df_view["Gastado"] = df_view["spent"].apply(fmt_money)
    df_view.insert(0, "Seleccionar", False)
    df_view = df_view[["Seleccionar", "id", "category", "Límite", "Gastado", "limitAmount"]]
    df_view.rename(columns={"id": "ID_Oculto", "category": "Categoría", "limitAmount": "Monto_Crudo"}, inplace=True)

    edited_df = st.data_editor(
        df_view, width="stretch", hide_index=True, disabled=["Categoría", "Límite", "Gastado"],
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("Ver/Editar", default=False),
            "ID_Oculto": None, "Monto_Crudo": None
        }
    )

    selected = edited_df[edited_df["Seleccionar"] == True]

    if len(selected) == 1:
        row = selected.iloc[0]
        st.markdown("---")
        st.subheader(f" Ajustar límite: {row['Categoría']}")

        with st.container(border=True):
            with st.form("update_budget"):
                u_limit = st.number_input("Nuevo Límite Numérico", value=float(row["Monto_Crudo"]), step=10.0)
                st.markdown("<br>", unsafe_allow_html=True)
                cA, cB = st.columns([1, 10])
                with cA:
                    if st.form_submit_button("Guardar", type="primary"):
                        try:
                            api.update_budget(row["ID_Oculto"], {"limitAmount": u_limit})
                            st.success("Límite actualizado.")
                            st.cache_data.clear()
                            st.rerun()
                        except ApiCaidaError as e:
                            st.error(f"Error de conexión: {e.message}")
                with cB:
                    if st.form_submit_button("Eliminar Presupuesto"):
                        try:
                            api.delete_budget(row["ID_Oculto"])
                            st.success("Eliminado con éxito.")
                            st.cache_data.clear()
                            st.rerun()
                        except ApiCaidaError as e:
                            st.error(f"Error de conexión: {e.message}")
    elif len(selected) > 1:
        st.markdown("---")
        st.subheader(f"{len(selected)} Presupuestos Seleccionados")
        with st.container(border=True):
            st.info("Has seleccionado múltiples presupuestos. La edición simultánea no está permitida.")
            with st.form("bulk_delete_bg"):
                    if st.form_submit_button("Eliminar Seleccionados"):
                        try:
                            ids = [r["ID_Oculto"] for _, r in selected.iterrows()]
                            api.bulk_delete_budgets(ids)
                            st.success("Presupuestos eliminados.")
                            st.cache_data.clear()
                            st.rerun()
                        except ApiCaidaError as e:
                            st.error(f"Error de conexión: {e.message}")
else:
    st.info("No hay presupuestos configurados para este mes.")

try:
    cat_r = api.get_category_stats(month_input)
    if isinstance(cat_r, dict):
        cats_spent = set(cat_r.keys())
        budgeted_cats = set(b["category"] for b in budgets) if budgets else set()
        unbudgeted = cats_spent - budgeted_cats
        if unbudgeted:
            st.warning(f"La API reporta gastos en categorías sin presupuesto asignado: **{', '.join(unbudgeted)}**")
except Exception:
    pass

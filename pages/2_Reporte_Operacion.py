import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import date

st.set_page_config(
    page_title="Reporte Operación",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .section-title {
    font-size: 1.1rem; font-weight: 600; color: #1A1D23;
    border-left: 4px solid #0D9488; padding-left: 10px; margin-bottom: 16px;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# CONEXIÓN
# ─────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine("mysql+pymysql://root:@localhost:3306/gkmobile")

engine = get_engine()


# ─────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────
import time

@st.cache_data(ttl=300)
def cargar_reporte(fecha_ini, fecha_fin, agencia, puesto, promotor):
    t0 = time.time()

    filtros = f"fecha >= '{fecha_ini}' AND fecha <= '{fecha_fin}'"
    if agencia != "Todas":
        filtros += f" AND agencia = '{agencia}'"
    if puesto != "Todos":
        filtros += f" AND puesto = '{puesto}'"
    if promotor != "Todos":
        filtros += f" AND nombre = '{promotor}'"

    q = f"""
        SELECT
            fecha, usuario, puesto, agencia, nombre,
            supervisor, entidad, inicio_jornada, fin_jornada,
            horas_laboradas, incidencia, visitas_programadas,
            visitas_dentro_itinerario, visitas_fuera_itinerario,
            total_pdv_visitas, pct_cumplimiento_plan, pct_cumplimiento_visitas
        FROM v_operacion_promotores
        WHERE {filtros}
        ORDER BY fecha DESC, nombre
        LIMIT 10000
    """

    df = pd.read_sql(q, engine)
    t1 = time.time()

    t2 = time.time()
    # procesamiento pandas — por ahora vacío
    t3 = time.time()

    return df, round(t1 - t0, 2), round(t3 - t2, 2)



#@st.cache_data(ttl=300)
#def cargar_reporte(fecha_ini, fecha_fin, agencia, puesto, promotor):
#    filtros = f"fecha >= '{fecha_ini}' AND fecha <= '{fecha_fin}'"
#    if agencia != "Todas":
#        filtros += f" AND agencia = '{agencia}'"
#    if puesto != "Todos":
#        filtros += f" AND puesto = '{puesto}'"
#    if promotor != "Todos":
#        filtros += f" AND nombre = '{promotor}'"

#    q = f"""
#        SELECT
#            fecha,
#            usuario,
#            puesto,
#            agencia,
#            nombre,
#            supervisor,
#            entidad,
#            inicio_jornada,
#            fin_jornada,
#            horas_laboradas,
#            incidencia,
#            visitas_programadas,
#            visitas_dentro_itinerario,
#            visitas_fuera_itinerario,
#            total_pdv_visitas,
#            pct_cumplimiento_plan,
#            pct_cumplimiento_visitas
#        FROM v_operacion_promotores
#        WHERE {filtros}
#        ORDER BY fecha DESC, nombre
#        LIMIT 10000
#    """
#    return pd.read_sql(q, engine)


@st.cache_data(ttl=600)
def cargar_opciones():
    agencias   = pd.read_sql("SELECT DISTINCT agencia FROM v_operacion_promotores WHERE agencia IS NOT NULL ORDER BY agencia", engine)
    puestos    = pd.read_sql("SELECT DISTINCT puesto  FROM v_operacion_promotores WHERE puesto  IS NOT NULL ORDER BY puesto",  engine)
    promotores = pd.read_sql("SELECT DISTINCT nombre  FROM v_operacion_promotores WHERE nombre  IS NOT NULL ORDER BY nombre",  engine)
    return (
        ["Todas"] + agencias["agencia"].tolist(),
        ["Todos"] + puestos["puesto"].tolist(),
        ["Todos"] + promotores["nombre"].tolist(),
    )


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Reporte de Operación")
    st.markdown("---")

    hoy = date.today()
    fecha_ini = st.date_input("Fecha inicio", value=hoy.replace(day=1))
    fecha_fin = st.date_input("Fecha fin",    value=hoy)

    agencias_opts, puestos_opts, promotores_opts = cargar_opciones()
    agencia_sel  = st.selectbox("Agencia",  agencias_opts)
    puesto_sel   = st.selectbox("Puesto",   puestos_opts)
    promotor_sel = st.selectbox("Promotor", promotores_opts)

    st.markdown("---")
    st.caption(f"GKMobile · Operación · {hoy.year}")

fi = str(fecha_ini)
ff = str(fecha_fin)

# ─────────────────────────────────────────
# CARGA
# ─────────────────────────────────────────
# Ahora
with st.spinner("Cargando reporte..."):
    df, t_sql, t_pandas = cargar_reporte(fi, ff, agencia_sel, puesto_sel, promotor_sel)

st.sidebar.metric("⏱ Extracción SQL", f"{t_sql}s")
st.sidebar.metric("⚙️ Procesamiento", f"{t_pandas}s")

st.title("Reporte de Operación — Promotores")
st.caption(f"Periodo: {fi}  →  {ff}  |  {df['usuario'].nunique()} promotores  |  {len(df):,} registros")

if df.empty:
    st.warning("Sin datos para los filtros seleccionados. Ajusta el rango de fechas.")
    st.stop()

# ─────────────────────────────────────────
# KPIs RÁPIDOS
# ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Promotores",          df["usuario"].nunique())
c2.metric("Visitas programadas", f"{int(df['visitas_programadas'].sum()):,}")
c3.metric("Visitas realizadas",  f"{int(df['total_pdv_visitas'].sum()):,}")
c4.metric("% Cumplimiento prom.",
          f"{df['pct_cumplimiento_plan'].dropna().mean():.1f}%")
c5.metric("Hrs promedio/día",
          f"{df['horas_laboradas'].dropna().mean():.1f}h")

st.divider()

# ─────────────────────────────────────────
# BÚSQUEDA Y TABLA
# ─────────────────────────────────────────
st.markdown('<p class="section-title">Detalle por promotor y día</p>',
            unsafe_allow_html=True)

buscar = st.text_input("Buscar en la tabla",
                       placeholder="Nombre, usuario, agencia, entidad...")

df_tabla = df.copy()
if buscar:
    mask = (
            df_tabla["nombre"].str.contains(buscar, case=False, na=False)  |
            df_tabla["usuario"].str.contains(buscar, case=False, na=False) |
            df_tabla["agencia"].str.contains(buscar, case=False, na=False) |
            df_tabla["entidad"].str.contains(buscar, case=False, na=False)
    )
    df_tabla = df_tabla[mask]

# Formatear columnas para presentación
df_tabla["fecha"]          = pd.to_datetime(df_tabla["fecha"]).dt.strftime("%d/%m/%Y")
df_tabla["inicio_jornada"] = pd.to_datetime(df_tabla["inicio_jornada"]).dt.strftime("%H:%M").fillna("—")
df_tabla["fin_jornada"]    = pd.to_datetime(df_tabla["fin_jornada"]).dt.strftime("%H:%M").fillna("—")
df_tabla["horas_laboradas"] = df_tabla["horas_laboradas"].apply(
    lambda x: f"{x:.1f}h" if pd.notna(x) else "—"
)
df_tabla["pct_cumplimiento_plan"] = df_tabla["pct_cumplimiento_plan"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
)
df_tabla["pct_cumplimiento_visitas"] = df_tabla["pct_cumplimiento_visitas"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
)
df_tabla["incidencia"] = df_tabla["incidencia"].fillna("—")

# Renombrar columnas al español del reporte original
df_mostrar = df_tabla.rename(columns={
    "fecha":                      "Fecha",
    "usuario":                    "Usuario",
    "puesto":                     "Puesto",
    "agencia":                    "Agencia",
    "nombre":                     "Nombre",
    "supervisor":                 "Supervisor",
    "entidad":                    "Entidad",
    "inicio_jornada":             "Inicio jornada",
    "fin_jornada":                "Fin jornada",
    "horas_laboradas":            "Horas laboradas",
    "incidencia":                 "Incidencias",
    "visitas_programadas":        "Vis. programadas",
    "visitas_dentro_itinerario":  "Dentro itinerario",
    "visitas_fuera_itinerario":   "Fuera itinerario",
    "total_pdv_visitas":          "Total PDV",
    "pct_cumplimiento_plan":      "% Cumpl. plan",
    "pct_cumplimiento_visitas":   "% Cumpl. visitas",
})

st.dataframe(
    df_mostrar[[
        "Fecha", "Usuario", "Puesto", "Agencia", "Nombre",
        "Supervisor", "Entidad", "Inicio jornada", "Fin jornada",
        "Horas laboradas", "Incidencias", "Vis. programadas",
        "Dentro itinerario", "Fuera itinerario", "Total PDV",
        "% Cumpl. plan", "% Cumpl. visitas",
    ]],
    use_container_width=True,
    hide_index=True,
    height=520,
)

st.caption(f"Mostrando {len(df_mostrar):,} de {len(df):,} registros")

st.divider()

# ─────────────────────────────────────────
# DESCARGA
# ─────────────────────────────────────────
col_a, col_b = st.columns([1, 4])

with col_a:
    csv = df_mostrar.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Descargar CSV",
        data=csv,
        file_name=f"reporte_operacion_{fi}_{ff}.csv",
        mime="text/csv",
        use_container_width=True,
    )
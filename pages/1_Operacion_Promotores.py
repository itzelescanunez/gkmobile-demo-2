import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import date

st.set_page_config(
    page_title="Operación Promotores",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .section-title {
        font-size: 1.1rem; font-weight: 600; color: #1A1D23;
        border-left: 4px solid #0D9488; padding-left: 10px; margin-bottom: 16px;
    }
    .kpi-label { font-size: 0.72rem; color: #6B7280; text-transform: uppercase;
                 letter-spacing: 0.08em; }
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
@st.cache_data(ttl=300)
def cargar_datos(fecha_ini, fecha_fin, agencia, puesto, promotor):
    filtros = f"fecha >= '{fecha_ini}' AND fecha <= '{fecha_fin}'"
    if agencia != "Todas":
        filtros += f" AND agencia = '{agencia}'"
    if puesto != "Todos":
        filtros += f" AND puesto = '{puesto}'"
    if promotor != "Todos":
        filtros += f" AND nombre = '{promotor}'"

    q = f"""
        SELECT
            fecha, usuario_id, usuario, nombre, puesto, agencia,
            supervisor, entidad, incidencia,
            inicio_jornada, fin_jornada, horas_laboradas,
            visitas_programadas, visitas_dentro_itinerario,
            visitas_fuera_itinerario, total_pdv_visitas,
            pct_cumplimiento_plan, pct_cumplimiento_visitas
        FROM v_operacion_promotores
        WHERE {filtros}
        ORDER BY fecha DESC, nombre
        LIMIT 5000
    """
    return pd.read_sql(q, engine)


@st.cache_data(ttl=600)
def cargar_opciones():
    agencias  = pd.read_sql("SELECT DISTINCT agencia FROM v_operacion_promotores WHERE agencia IS NOT NULL ORDER BY agencia", engine)
    puestos   = pd.read_sql("SELECT DISTINCT puesto  FROM v_operacion_promotores WHERE puesto  IS NOT NULL ORDER BY puesto",  engine)
    promotores = pd.read_sql("SELECT DISTINCT nombre FROM v_operacion_promotores WHERE nombre IS NOT NULL ORDER BY nombre", engine)
    return (
        ["Todas"]  + agencias["agencia"].tolist(),
        ["Todos"]  + puestos["puesto"].tolist(),
        ["Todos"]  + promotores["nombre"].tolist(),
    )


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Operación Promotores")
    st.markdown("---")

    hoy = date.today()
    fecha_ini = st.date_input("Fecha inicio", value=hoy.replace(day=1))
    fecha_fin = st.date_input("Fecha fin",    value=hoy)

    agencias_opts, puestos_opts, promotores_opts = cargar_opciones()
    agencia_sel  = st.selectbox("Agencia",   agencias_opts)
    puesto_sel   = st.selectbox("Puesto",    puestos_opts)
    promotor_sel = st.selectbox("Promotor",  promotores_opts)

    st.markdown("---")
    st.caption(f"GKMobile · Operación · {hoy.year}")

fi = str(fecha_ini)
ff = str(fecha_fin)

# ─────────────────────────────────────────
# CARGA
# ─────────────────────────────────────────
with st.spinner("Cargando datos..."):
    df = cargar_datos(fi, ff, agencia_sel, puesto_sel, promotor_sel)

st.title("Reporte de Operación — Promotores")
st.caption(f"Periodo: {fi}  →  {ff}  |  {len(df):,} registros  |  {df['usuario_id'].nunique()} promotores")

if df.empty:
    st.warning("Sin datos para los filtros seleccionados.")
    st.stop()

# ─────────────────────────────────────────
# KPIs GENERALES
# ─────────────────────────────────────────
st.markdown('<p class="section-title">KPIs generales</p>', unsafe_allow_html=True)

total_promotores    = df["usuario_id"].nunique()
total_visitas_prog  = int(df["visitas_programadas"].sum())
total_visitas_real  = int(df["total_pdv_visitas"].sum())
total_fuera         = int(df["visitas_fuera_itinerario"].sum())
pct_plan_gral       = round(total_visitas_real / total_visitas_prog * 100, 1) if total_visitas_prog else 0
horas_prom          = round(df["horas_laboradas"].dropna().mean(), 1)
incidencias         = df["incidencia"].notna().sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Promotores",         f"{total_promotores:,}")
c2.metric("Visitas programadas",f"{total_visitas_prog:,}")
c3.metric("Visitas realizadas", f"{total_visitas_real:,}")
c4.metric("Fuera de itinerario",f"{total_fuera:,}")
c5.metric("% Cumplimiento",     f"{pct_plan_gral}%")
c6.metric("Hrs promedio/día",   f"{horas_prom}")

st.divider()

# ─────────────────────────────────────────
# GRÁFICAS — FILA 1
# ─────────────────────────────────────────
st.markdown('<p class="section-title">Cumplimiento y jornada</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # % cumplimiento plan por agencia
    df_ag = df.groupby("agencia").agg(
        programadas=("visitas_programadas", "sum"),
        realizadas=("total_pdv_visitas", "sum"),
    ).reset_index()
    df_ag["pct"] = (df_ag["realizadas"] / df_ag["programadas"].replace(0, pd.NA) * 100).round(1)
    df_ag = df_ag.dropna(subset=["pct"]).sort_values("pct", ascending=True).tail(15)

    fig1 = px.bar(
        df_ag, x="pct", y="agencia", orientation="h",
        title="% Cumplimiento plan por agencia",
        color="pct",
        color_continuous_scale=["#E55B4D", "#D97706", "#0D9488"],
        range_color=[0, 100],
        text="pct",
    )
    fig1.update_traces(texttemplate="%{text}%", textposition="outside")
    fig1.update_layout(
        showlegend=False, height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
    )
    fig1.update_xaxes(showgrid=True, gridcolor="#F4F5F7", range=[0, 115])
    fig1.update_yaxes(showgrid=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Horas laboradas promedio por agencia
    df_hrs = df.groupby("agencia")["horas_laboradas"].mean().round(1).reset_index()
    df_hrs = df_hrs.dropna().sort_values("horas_laboradas", ascending=True).tail(15)

    fig2 = px.bar(
        df_hrs, x="horas_laboradas", y="agencia", orientation="h",
        title="Horas laboradas promedio por agencia",
        color="horas_laboradas",
        color_continuous_scale=["#B5D4F4", "#0057FF"],
        text="horas_laboradas",
    )
    fig2.update_traces(texttemplate="%{text}h", textposition="outside")
    fig2.update_layout(
        showlegend=False, height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
    )
    fig2.update_xaxes(showgrid=True, gridcolor="#F4F5F7")
    fig2.update_yaxes(showgrid=False)
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────
# GRÁFICAS — FILA 2
# ─────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    # Visitas dentro vs fuera de itinerario
    df_iti = df.groupby("nombre").agg(
        dentro=("visitas_dentro_itinerario", "sum"),
        fuera=("visitas_fuera_itinerario",   "sum"),
    ).reset_index()
    df_iti["total"] = df_iti["dentro"] + df_iti["fuera"]
    df_iti = df_iti.sort_values("total", ascending=False).head(15)

    df_melt = df_iti.melt(
        id_vars="nombre", value_vars=["dentro", "fuera"],
        var_name="tipo", value_name="visitas"
    )
    df_melt["tipo"] = df_melt["tipo"].map({"dentro": "Dentro itinerario", "fuera": "Fuera de itinerario"})

    fig3 = px.bar(
        df_melt, x="visitas", y="nombre", color="tipo",
        orientation="h", barmode="stack",
        title="Top 15 promotores — visitas dentro/fuera itinerario",
        color_discrete_map={
            "Dentro itinerario":     "#0D9488",
            "Fuera de itinerario":   "#E55B4D",
        },
    )
    fig3.update_layout(
        height=420, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02),
    )
    fig3.update_xaxes(showgrid=True, gridcolor="#F4F5F7")
    fig3.update_yaxes(showgrid=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    # Distribución de % cumplimiento de visitas
    df_pct = df[df["pct_cumplimiento_visitas"].notna()].copy()
    fig4 = px.histogram(
        df_pct, x="pct_cumplimiento_visitas",
        title="Distribución de % cumplimiento de visitas",
        nbins=20,
        color_discrete_sequence=["#0057FF"],
    )
    fig4.update_layout(
        height=420, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="% Cumplimiento", yaxis_title="Promotores",
        bargap=0.05,
    )
    fig4.update_xaxes(showgrid=True, gridcolor="#F4F5F7")
    fig4.update_yaxes(showgrid=True, gridcolor="#F4F5F7")

    # Líneas de referencia
    fig4.add_vline(x=80,  line_dash="dash", line_color="#D97706", annotation_text="80%")
    fig4.add_vline(x=100, line_dash="dash", line_color="#0D9488", annotation_text="100%")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# INCIDENCIAS
# ─────────────────────────────────────────
df_inc = df[df["incidencia"].notna() & (df["incidencia"] != "")]
if not df_inc.empty:
    st.markdown('<p class="section-title">Incidencias</p>', unsafe_allow_html=True)
    col5, col6 = st.columns([1, 2])

    with col5:
        st.metric("Total incidencias", f"{len(df_inc):,}")
        top_inc = df_inc["incidencia"].value_counts().head(8).reset_index()
        top_inc.columns = ["Incidencia", "Frecuencia"]
        st.dataframe(top_inc, use_container_width=True, hide_index=True)

    with col6:
        fig5 = px.bar(
            top_inc, x="Frecuencia", y="Incidencia", orientation="h",
            title="Incidencias más frecuentes",
            color_discrete_sequence=["#D97706"],
        )
        fig5.update_layout(
            height=320, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        fig5.update_xaxes(showgrid=True, gridcolor="#F4F5F7")
        fig5.update_yaxes(showgrid=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.divider()

# ─────────────────────────────────────────
# TABLA DETALLADA
# ─────────────────────────────────────────
st.markdown('<p class="section-title">Detalle por promotor y día</p>', unsafe_allow_html=True)

# Búsqueda rápida
buscar = st.text_input("Buscar por nombre o usuario", placeholder="Escribe para filtrar...")
df_tabla = df.copy()
if buscar:
    df_tabla = df_tabla[
        df_tabla["nombre"].str.contains(buscar, case=False, na=False) |
        df_tabla["usuario"].str.contains(buscar, case=False, na=False)
        ]

# Formato de la tabla
df_tabla["inicio_jornada"] = pd.to_datetime(df_tabla["inicio_jornada"]).dt.strftime("%H:%M")
df_tabla["fin_jornada"]    = pd.to_datetime(df_tabla["fin_jornada"]).dt.strftime("%H:%M")
df_tabla["fecha"]          = pd.to_datetime(df_tabla["fecha"]).dt.strftime("%d/%m/%Y")
df_tabla["horas_laboradas"] = df_tabla["horas_laboradas"].apply(
    lambda x: f"{x:.1f}h" if pd.notna(x) else "—"
)
df_tabla["pct_cumplimiento_plan"]    = df_tabla["pct_cumplimiento_plan"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
)
df_tabla["pct_cumplimiento_visitas"] = df_tabla["pct_cumplimiento_visitas"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
)

st.dataframe(
    df_tabla[[
        "fecha", "nombre", "puesto", "agencia", "supervisor", "entidad",
        "inicio_jornada", "fin_jornada", "horas_laboradas", "incidencia",
        "visitas_programadas", "visitas_dentro_itinerario",
        "visitas_fuera_itinerario", "total_pdv_visitas",
        "pct_cumplimiento_plan", "pct_cumplimiento_visitas",
    ]].rename(columns={
        "fecha":                      "Fecha",
        "nombre":                     "Nombre",
        "puesto":                     "Puesto",
        "agencia":                    "Agencia",
        "supervisor":                 "Supervisor",
        "entidad":                    "Entidad",
        "inicio_jornada":             "Inicio jornada",
        "fin_jornada":                "Fin jornada",
        "horas_laboradas":            "Horas laboradas",
        "incidencia":                 "Incidencia",
        "visitas_programadas":        "Vis. programadas",
        "visitas_dentro_itinerario":  "Dentro itinerario",
        "visitas_fuera_itinerario":   "Fuera itinerario",
        "total_pdv_visitas":          "Total PDV",
        "pct_cumplimiento_plan":      "% Plan",
        "pct_cumplimiento_visitas":   "% Visitas",
    }),
    use_container_width=True,
    hide_index=True,
    height=480,
)

# Descarga CSV
csv = df_tabla.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name=f"operacion_promotores_{fi}_{ff}.csv",
    mime="text/csv",
)
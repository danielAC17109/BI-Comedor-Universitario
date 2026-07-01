import os
from pathlib import Path

import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

def obtener_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        st.error("No existe DATABASE_URL configurado.")
        st.stop()
    return create_engine(database_url)


engine = obtener_engine()


@st.cache_data(ttl=60)
def cargar_df(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


st.title(" Dashboard BI - Comedor Universitario")
st.caption("Dashboard conectado a Supabase PostgreSQL")


# =========================
# KPIs GENERALES
# =========================

df_kpis = cargar_df("SELECT * FROM vw_kpis_generales")

if df_kpis.empty:
    st.warning("No hay datos cargados todavía.")
    st.stop()

total_registros = int(df_kpis.loc[0, "total_registros"])
total_comidas = int(df_kpis.loc[0, "total_comidas"] or 0)
total_ingresos = float(df_kpis.loc[0, "total_ingresos"] or 0)
promedio_consumo = float(df_kpis.loc[0, "promedio_consumo"] or 0)

# KPI de Google Analytics
df_eventos = cargar_df("""
    SELECT COUNT(*) AS total
    FROM analytics_eventos
""")

total_eventos = int(df_eventos.loc[0, "total"])

# =========================
# TARJETAS KPI
# =========================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "📄 Registros",
    f"{total_registros:,}"
)

col2.metric(
    "🍽️ Total comidas",
    f"{total_comidas:,}"
)

col3.metric(
    "💰 Ingresos",
    f"S/ {total_ingresos:,.2f}"
)

col4.metric(
    "📊 Promedio consumo",
    f"{promedio_consumo:,.2f}"
)

col5.metric(
    "📈 Interacciones ",
    f"{total_eventos:,}"
)

st.divider()

# =========================
# GRÁFICOS
# =========================

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Consumo por fecha")
    df_fecha = cargar_df("""
        SELECT fecha, total_comidas, total_ingresos
        FROM vw_consumo_fecha
        ORDER BY fecha
    """)

    if not df_fecha.empty:
        st.line_chart(
            df_fecha,
            x="fecha",
            y="total_comidas"
        )
    else:
        st.info("No hay datos por fecha.")

with col_b:
    st.subheader("Demanda")
    df_demanda = cargar_df("""
        SELECT nivel_demanda, cantidad
        FROM vw_demanda
        ORDER BY cantidad DESC
    """)

    if not df_demanda.empty:
        st.bar_chart(
            df_demanda,
            x="nivel_demanda",
            y="cantidad"
        )
    else:
        st.info("No hay datos de demanda.")


col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Consumo por menú")
    df_menu = cargar_df("""
        SELECT tipo_menu, total_consumo
        FROM vw_menu
        ORDER BY total_consumo DESC
    """)

    if not df_menu.empty:
        st.bar_chart(
            df_menu,
            x="tipo_menu",
            y="total_consumo"
        )
    else:
        st.info("No hay datos de menú.")

with col_d:
    st.subheader("Clima vs consumo")
    df_clima = cargar_df("""
        SELECT temperatura_max, promedio_consumo
        FROM vw_clima
        ORDER BY temperatura_max
    """)

    if not df_clima.empty:
        st.line_chart(
            df_clima,
            x="temperatura_max",
            y="promedio_consumo"
        )
    else:
        st.info("No hay datos de clima.")


st.divider()


# =========================
# KPI IOT
# =========================

st.subheader(" KPI IoT - Aforo en tiempo real")

try:
    df_iot = cargar_df("""
        SELECT
            fecha_hora,
            personas_actuales,
            capacidad,
            porcentaje_ocupacion,
            estado
        FROM iot_aforo
        ORDER BY fecha_hora DESC
        LIMIT 1
    """)

    if df_iot.empty:
        st.info("Todavía no hay datos IoT registrados.")
    else:
        personas = int(df_iot.loc[0, "personas_actuales"])
        capacidad = int(df_iot.loc[0, "capacidad"])
        porcentaje = float(df_iot.loc[0, "porcentaje_ocupacion"])
        estado = df_iot.loc[0, "estado"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Personas actuales", personas)
        c2.metric("Capacidad", capacidad)
        c3.metric("Ocupación", f"{porcentaje:.2f}%")
        c4.metric("Estado", estado)

except Exception:
    st.info("La tabla IoT aún no está creada. La agregaremos en la siguiente fase.")


st.divider()



# =========================
# GOOGLE ANALYTICS (EVENTOS)
# =========================

st.divider()

st.header("📈 Analítica de uso de la plataforma")

try:

    df_eventos = cargar_df("""
        SELECT *
        FROM analytics_eventos
        ORDER BY fecha_hora DESC
    """)

    if df_eventos.empty:

        st.info("Todavía no existen eventos registrados.")

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Eventos por tipo")

            eventos_tipo = (
                df_eventos
                .groupby("nombre_evento")
                .size()
                .reset_index(name="cantidad")
            )

            st.bar_chart(
                eventos_tipo,
                x="nombre_evento",
                y="cantidad"
            )

        with col2:

            st.subheader("Eventos por página")

            eventos_pagina = (
                df_eventos
                .groupby("pagina")
                .size()
                .reset_index(name="cantidad")
            )

            st.bar_chart(
                eventos_pagina,
                x="pagina",
                y="cantidad"
            )

        st.subheader("Historial de eventos")

        st.dataframe(
            df_eventos,
            use_container_width=True
        )

except Exception as e:

    st.warning(f"No se pudieron cargar las analíticas: {e}")

# =========================
# TABLA DETALLE
# =========================

st.subheader("Detalle de consumo")

df_detalle = cargar_df("""
    SELECT
        fc.id_consumo,
        dt.fecha,
        dm.tipo_menu,
        fc.comidas_servidas,
        fc.ingresos_cafeteria,
        fc.nivel_demanda
    FROM fact_consumo fc
    INNER JOIN dim_tiempo dt
        ON fc.id_tiempo = dt.id_tiempo
    INNER JOIN dim_menu dm
        ON fc.id_menu = dm.id_menu
    ORDER BY fc.id_consumo DESC
    LIMIT 50
""")

st.dataframe(df_detalle, use_container_width=True)
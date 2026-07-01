import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from sqlalchemy import text

from DATABASE.conexion import obtener_conexion


def dibujar_tabla(ax, nombre, columnas, x, y, w=2.4, h=1.35):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="#d9edf7", edgecolor="black", linewidth=1.2))
    ax.add_patch(Rectangle((x, y + h - 0.35), w, 0.35, facecolor="#b7dce8", edgecolor="black", linewidth=1.2))

    ax.text(x + 0.08, y + h - 0.18, nombre, fontsize=9, fontweight="bold", va="center")

    max_cols = 8
    for i, col in enumerate(columnas[:max_cols]):
        ax.text(x + 0.12, y + h - 0.55 - (i * 0.14), col, fontsize=7, va="center")

    if len(columnas) > max_cols:
        ax.text(x + 0.12, y + 0.12, "...", fontsize=8, va="center")


def conectar(ax, origen, destino):
    x1, y1, w1, h1 = origen
    x2, y2, w2, h2 = destino

    start = (x1 + w1, y1 + h1 / 2)
    end = (x2, y2 + h2 / 2)

    if x2 < x1:
        start = (x1, y1 + h1 / 2)
        end = (x2 + w2, y2 + h2 / 2)

    flecha = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.2,
        color="black",
        connectionstyle="arc3,rad=0.05"
    )

    ax.add_patch(flecha)


def generar_modelo():
    engine = obtener_conexion()
    tablas_columnas = {}

    with engine.connect() as conn:
        tablas = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)).fetchall()

        for tabla in tablas:
            nombre_tabla = tabla[0]

            columnas = conn.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = :tabla
                    ORDER BY ordinal_position
                """),
                {"tabla": nombre_tabla}
            ).fetchall()

            tablas_columnas[nombre_tabla] = [c[0] for c in columnas]

        relaciones = conn.execute(text("""
            SELECT
                tc.table_name AS tabla_origen,
                ccu.table_name AS tabla_destino
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """)).fetchall()

    layout = {
        "fact_consumo": (5.0, 3.0, 2.6, 2.1),

        "dim_usuario": (1.2, 5.9, 2.4, 1.25),
        "dim_satisfaccion": (5.0, 6.2, 2.4, 1.25),
        "dim_aforo": (8.6, 5.3, 2.4, 1.1),
        "dim_tiempo": (8.6, 4.0, 2.4, 1.3),
        "dim_menu": (1.2, 3.6, 2.4, 1.25),
        "dim_clima": (1.2, 1.4, 2.4, 1.25),
        "dim_comedor": (5.0, 0.8, 2.4, 1.25),

        "staging_comedor": (0.2, 6.9, 2.7, 2.0),
        "fact_kpis": (9.0, 7.0, 2.5, 1.35),
    }

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    for tabla, rect in layout.items():
        if tabla in tablas_columnas:
            x, y, w, h = rect
            dibujar_tabla(ax, tabla, tablas_columnas[tabla], x, y, w, h)

    for origen, destino in relaciones:
        if origen in layout and destino in layout:
            conectar(ax, layout[origen], layout[destino])

    ax.set_title(
        "Modelo Data Warehouse - Copo de Nieve",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    os.makedirs("static/img", exist_ok=True)
    plt.savefig("static/img/snowflake.png", bbox_inches="tight", dpi=220)
    plt.close()
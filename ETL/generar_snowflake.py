import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
from sqlalchemy import text

from DATABASE.conexion import obtener_conexion


def generar_modelo():

    engine = obtener_conexion()
    graph = nx.DiGraph()
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
            graph.add_node(nombre_tabla)

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

        for origen, destino in relaciones:
            graph.add_edge(origen, destino)

    pos = {
        "fact_consumo": (0, 0),

        "dim_tiempo": (3.2, 2.1),
        "dim_usuario": (3.2, 1.2),
        "dim_menu": (3.2, 0.3),
        "dim_clima": (3.2, -0.6),
        "dim_aforo": (3.2, -1.5),
        "dim_comedor": (-3.2, 1.2),
        "dim_satisfaccion": (-3.2, -1.2),

        "staging_comedor": (-5.8, 0),
        "fact_kpis": (0, -2.6),
    }

    for tabla in graph.nodes:
        if tabla not in pos:
            pos[tabla] = (0, 3)

    labels = {}
    for tabla, columnas in tablas_columnas.items():
        cols = "\n".join(columnas[:12])
        labels[tabla] = f"{tabla}\n────────────\n{cols}"

    plt.figure(figsize=(18, 10))

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=9000,
        node_color="#ADD8E6",
        edgecolors="black",
        linewidths=1.2
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=18,
        width=1.3,
        connectionstyle="arc3,rad=0.05"
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=7,
        font_family="monospace"
    )

    plt.title(
        "Modelo Data Warehouse - Copo de Nieve",
        fontsize=18,
        fontweight="bold"
    )

    plt.axis("off")
    plt.tight_layout()

    os.makedirs("static/img", exist_ok=True)
    plt.savefig("static/img/snowflake.png", bbox_inches="tight", dpi=220)
    plt.close()

    print("Modelo Snowflake generado correctamente")
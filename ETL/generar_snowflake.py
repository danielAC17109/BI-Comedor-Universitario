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

            tablas_columnas[nombre_tabla] = [
                columna[0] for columna in columnas
            ]

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

        for relacion in relaciones:
            graph.add_edge(relacion[0], relacion[1])

    labels = {}

    for tabla, columnas in tablas_columnas.items():
        texto_columnas = "\n".join(columnas[:10])
        labels[tabla] = f"{tabla}\n────────\n{texto_columnas}"

    plt.figure(figsize=(18, 10))

    pos = nx.spring_layout(graph, seed=42, k=1.4)

    nx.draw(
        graph,
        pos,
        labels=labels,
        with_labels=True,
        node_size=8500,
        font_size=7,
        arrows=True
    )

    os.makedirs("static/img", exist_ok=True)

    plt.title("Modelo Data Warehouse - Snowflake")
    plt.savefig("static/img/snowflake.png", bbox_inches="tight", dpi=200)
    plt.close()

    print("Modelo Snowflake generado con NetworkX")
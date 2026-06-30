from sqlalchemy import text
from graphviz import Digraph

from DATABASE.conexion import obtener_conexion


def generar_modelo():

    engine = obtener_conexion()

    dot = Digraph('Snowflake', format='png')
    dot.attr(rankdir='LR')

    with engine.connect() as conn:

        tablas_result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))

        tablas = [row[0] for row in tablas_result.fetchall()]

        for nombre_tabla in tablas:

            columnas_result = conn.execute(
                text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"table_name": nombre_tabla}
            )

            columnas = columnas_result.fetchall()

            atributos = ""

            for columna in columnas:

                nombre_columna = columna[0]
                tipo_columna = columna[1]

                atributos += f"{nombre_columna} : {tipo_columna}\\l"

            etiqueta = f"{{ {nombre_tabla} | {atributos} }}"

            dot.node(
                nombre_tabla,
                etiqueta,
                shape='record',
                style='filled',
                fillcolor='lightblue'
            )

        relaciones_result = conn.execute(text("""
            SELECT
                tc.table_name AS tabla_padre,
                ccu.table_name AS tabla_referencia
            FROM information_schema.table_constraints tc

            INNER JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema

            INNER JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema

            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """))

        relaciones = relaciones_result.fetchall()

        for relacion in relaciones:

            padre = relacion[0]
            referencia = relacion[1]

            dot.edge(
                padre,
                referencia
            )

    dot.render(
        filename='snowflake',
        directory='static/img',
        cleanup=True
    )

    print("Modelo Snowflake COMPLETO")
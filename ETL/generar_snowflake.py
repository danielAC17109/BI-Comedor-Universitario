from DATABASE.conexion import obtener_conexion
from graphviz import Digraph


def generar_modelo():

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    # ==========================================
    # OBTENER TABLAS
    # ==========================================

    cursor.execute("""

        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'

    """)

    tablas = cursor.fetchall()

    dot = Digraph('Snowflake', format='png')

    dot.attr(rankdir='LR')

    # ==========================================
    # CREAR TABLAS CON ATRIBUTOS
    # ==========================================

    for tabla in tablas:

        nombre_tabla = tabla[0]

        cursor.execute(f"""

            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{nombre_tabla}'

        """)

        columnas = cursor.fetchall()

        atributos = ""

        for columna in columnas:

            atributos += f"{columna[0]}\\l"

        etiqueta = f"""

        {{
            {nombre_tabla} |
            {atributos}
        }}

        """

        dot.node(
            nombre_tabla,
            etiqueta,
            shape='record',
            style='filled',
            fillcolor='lightblue'
        )

    # ==========================================
    # RELACIONES FK
    # ==========================================

    cursor.execute("""

        SELECT
            tp.name AS tabla_padre,
            tr.name AS tabla_referencia

        FROM sys.foreign_keys fk

        INNER JOIN sys.tables tp
            ON fk.parent_object_id = tp.object_id

        INNER JOIN sys.tables tr
            ON fk.referenced_object_id = tr.object_id

    """)

    relaciones = cursor.fetchall()

    for relacion in relaciones:

        padre = relacion[0]
        referencia = relacion[1]

        dot.edge(
            padre,
            referencia
        )

    # ==========================================
    # GUARDAR IMAGEN
    # ==========================================

    dot.render(
        'static/img/snowflake',
        cleanup=True
    )

    conexion.close()

    print("Modelo Snowflake COMPLETO ")
import pandas as pd
from DATABASE.conexion import obtener_conexion


def procesar_excel(ruta_excel):

    logs = []

    try:
        logs.append("Conectando a SQL Server ")

        # Uso de la nueva función importada
        conexion = obtener_conexion()

        logs.append("Conexión exitosa ")

        # LEER SEGÚN EXTENSIÓN 

        if ruta_excel.endswith('.xlsx'):

            df = pd.read_excel(ruta_excel)

        elif ruta_excel.endswith('.csv'):

            df = pd.read_csv(ruta_excel)

        elif ruta_excel.endswith('.json'):

            df = pd.read_json(ruta_excel)

        else:

            return "Formato no soportado "


        logs.append("Archivo leído correctamente")
        # CONVERTIR FECHA

        df['Fecha'] = pd.to_datetime(
            df['Fecha'],
            errors='coerce'
        )

        logs.append(f"Excel leído correctamente ")
        logs.append(f"Total filas encontradas: {len(df)}")

        cursor = conexion.cursor()
        # ==========================================
        # LIMPIAR DATA ANTERIOR
        # ==========================================

        cursor.execute("DELETE FROM fact_consumo")

        cursor.execute("DELETE FROM dim_usuario")

        cursor.execute("DELETE FROM dim_clima")

        cursor.execute("DELETE FROM dim_menu")

        cursor.execute("DELETE FROM dim_tiempo")

        cursor.execute("DELETE FROM dim_aforo")

        cursor.execute("DELETE FROM staging_comedor")

        conexion.commit()

        logs.append("Base limpiada correctamente")
        

        for index, row in df.iterrows():

            cursor.execute("""

                INSERT INTO staging_comedor
                (
                    fecha,
                    personas_en_campus,
                    comidas_servidas,
                    estudiantes,
                    personal,
                    temperatura_max,
                    temperatura_min,
                    tipo_menu,
                    calorias_menu,
                    ingresos_cafeteria
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """,

            row['Fecha'].date(),
            row['Personas_en_campus'],
            row['Comidas_servidas'],
            row['Estudiantes'],
            row['Personal'],
            row['Temperatura_max'],
            row['Temperatura_min'],
            row['Tipo_menu'],
            row['Calorias_menu'],
            row['Ingresos_cafeteria']
            )

        conexion.commit()

        logs.append("Datos insertados correctamente ")
        # ==========================================
        # INSERTAR DIM_TIEMPO
        # ==========================================

        cursor.execute("""

            INSERT INTO dim_tiempo
            (
                fecha,
                dia,
                mes,
                anio
            )

            SELECT DISTINCT
                fecha,
                DAY(fecha),
                MONTH(fecha),
                YEAR(fecha)

            FROM staging_comedor

        """)

        conexion.commit()

        logs.append("dim_tiempo cargada ")


        # ==========================================
        # INSERTAR DIM_USUARIO
        # ==========================================

        cursor.execute("""

            INSERT INTO dim_usuario
            (
                estudiantes,
                personal
            )

            SELECT DISTINCT
                estudiantes,
                personal

            FROM staging_comedor

        """)

        conexion.commit()

        logs.append("dim_usuario cargada ")


        # ==========================================
        # INSERTAR DIM_MENU
        # ==========================================

        cursor.execute("""

            INSERT INTO dim_menu
            (
                tipo_menu,
                calorias_menu
            )

            SELECT DISTINCT
                tipo_menu,
                calorias_menu

            FROM staging_comedor

        """)

        conexion.commit()

        logs.append("dim_menu cargada ")


        # ==========================================
        # INSERTAR DIM_CLIMA
        # ==========================================

        cursor.execute("""

            INSERT INTO dim_clima
            (
                temperatura_max,
                temperatura_min
            )

            SELECT DISTINCT
                temperatura_max,
                temperatura_min

            FROM staging_comedor

        """)

        conexion.commit()

        logs.append("dim_clima cargada")


        # ==========================================
        # INSERTAR DIM_AFORO
        # ==========================================

        cursor.execute("""

            INSERT INTO dim_aforo
            (
                personas_en_campus
            )

            SELECT DISTINCT
                personas_en_campus

            FROM staging_comedor

        """)

        conexion.commit()

        logs.append("dim_aforo cargada ")
        # ==========================================
        # INSERTAR FACT_CONSUMO
        # ==========================================

        cursor.execute ("""

        INSERT INTO fact_consumo
        (
            id_tiempo,
            id_usuario,
            id_menu,
            id_clima,
            id_aforo,
            comidas_servidas,
            ingresos_cafeteria,
            nivel_demanda,
            id_satisfaccion,
            id_comedor
        )

        SELECT

            dt.id_tiempo,
            du.id_usuario,
            dm.id_menu,
            dc.id_clima,
            da.id_aforo,

            s.comidas_servidas,
            s.ingresos_cafeteria,

            CASE

                WHEN s.comidas_servidas > 2000
                    THEN 'Alta'

                WHEN s.comidas_servidas > 1000
                    THEN 'Media'

                ELSE 'Baja'

            END,

            ds.id_satisfaccion,

            dco.id_comedor

        FROM staging_comedor s

        INNER JOIN dim_tiempo dt
            ON s.fecha = dt.fecha

        INNER JOIN dim_usuario du
            ON s.estudiantes = du.estudiantes
            AND s.personal = du.personal

        INNER JOIN dim_menu dm
            ON s.tipo_menu = dm.tipo_menu
            AND s.calorias_menu = dm.calorias_menu

        INNER JOIN dim_clima dc
            ON s.temperatura_max = dc.temperatura_max
            AND s.temperatura_min = dc.temperatura_min

        INNER JOIN dim_aforo da
            ON s.personas_en_campus = da.personas_en_campus

        INNER JOIN dim_satisfaccion ds
            ON ds.nivel_satisfaccion = 'Alta'

        INNER JOIN dim_comedor dco
            ON dco.sede = 'Comedor Central'

        """)

        conexion.commit()
        
        logs.append("fact_consumo cargada")
        cursor.execute("""

        SELECT COUNT(*)
        FROM fact_consumo

        """)

        total_fact = cursor.fetchone()[0]

        logs.append(
            f"Fact cargada con {total_fact} registros"
        )
        logs.append("ETL COMPLETADO ")

        conexion.close()

    except Exception as e:

        logs.append(f"ERROR: {str(e)}")

    return logs
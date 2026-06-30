import pandas as pd
from sqlalchemy import text
from DATABASE.conexion import obtener_conexion


def procesar_excel(ruta_excel):

    logs = []

    try:
        logs.append("Conectando a Supabase PostgreSQL")

        engine = obtener_conexion()

        logs.append("Conexión exitosa")

        if ruta_excel.endswith(".xlsx"):
            df = pd.read_excel(ruta_excel)
        elif ruta_excel.endswith(".csv"):
            df = pd.read_csv(ruta_excel)
        elif ruta_excel.endswith(".json"):
            df = pd.read_json(ruta_excel)
        else:
            return ["Formato no soportado"]

        logs.append("Archivo leído correctamente")

        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])

        logs.append(f"Total filas válidas encontradas: {len(df)}")

        df_staging = df.rename(columns={
            "Fecha": "fecha",
            "Personas_en_campus": "personas_en_campus",
            "Comidas_servidas": "comidas_servidas",
            "Estudiantes": "estudiantes",
            "Personal": "personal",
            "Temperatura_max": "temperatura_max",
            "Temperatura_min": "temperatura_min",
            "Tipo_menu": "tipo_menu",
            "Calorias_menu": "calorias_menu",
            "Ingresos_cafeteria": "ingresos_cafeteria"
        })

        columnas = [
            "fecha",
            "personas_en_campus",
            "comidas_servidas",
            "estudiantes",
            "personal",
            "temperatura_max",
            "temperatura_min",
            "tipo_menu",
            "calorias_menu",
            "ingresos_cafeteria"
        ]

        df_staging = df_staging[columnas]

        with engine.begin() as conexion:

            conexion.execute(text("DELETE FROM fact_consumo"))
            conexion.execute(text("DELETE FROM dim_usuario"))
            conexion.execute(text("DELETE FROM dim_clima"))
            conexion.execute(text("DELETE FROM dim_menu"))
            conexion.execute(text("DELETE FROM dim_tiempo"))
            conexion.execute(text("DELETE FROM dim_aforo"))
            conexion.execute(text("DELETE FROM staging_comedor"))

            logs.append("Base limpiada correctamente")

            df_staging.to_sql(
                "staging_comedor",
                con=conexion,
                if_exists="append",
                index=False
            )

            logs.append("Datos insertados en staging correctamente")

            conexion.execute(text("""
                INSERT INTO dim_tiempo
                (
                    fecha,
                    dia,
                    mes,
                    anio
                )
                SELECT DISTINCT
                    fecha,
                    EXTRACT(DAY FROM fecha)::INT,
                    EXTRACT(MONTH FROM fecha)::INT,
                    EXTRACT(YEAR FROM fecha)::INT
                FROM staging_comedor
            """))

            logs.append("dim_tiempo cargada")

            conexion.execute(text("""
                INSERT INTO dim_usuario
                (
                    estudiantes,
                    personal
                )
                SELECT DISTINCT
                    estudiantes,
                    personal
                FROM staging_comedor
            """))

            logs.append("dim_usuario cargada")

            conexion.execute(text("""
                INSERT INTO dim_menu
                (
                    tipo_menu,
                    calorias_menu
                )
                SELECT DISTINCT
                    tipo_menu,
                    calorias_menu
                FROM staging_comedor
            """))

            logs.append("dim_menu cargada")

            conexion.execute(text("""
                INSERT INTO dim_clima
                (
                    temperatura_max,
                    temperatura_min
                )
                SELECT DISTINCT
                    temperatura_max,
                    temperatura_min
                FROM staging_comedor
            """))

            logs.append("dim_clima cargada")

            conexion.execute(text("""
                INSERT INTO dim_aforo
                (
                    personas_en_campus
                )
                SELECT DISTINCT
                    personas_en_campus
                FROM staging_comedor
            """))

            logs.append("dim_aforo cargada")

            conexion.execute(text("""
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
                        WHEN s.comidas_servidas >= 350 THEN 'Alta'
                        WHEN s.comidas_servidas >= 200 THEN 'Media'
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
            """))

            logs.append("fact_consumo cargada")

            total_fact = conexion.execute(
                text("SELECT COUNT(*) FROM fact_consumo")
            ).scalar()

            logs.append(f"Fact cargada con {total_fact} registros")
            logs.append("ETL COMPLETADO")

    except Exception as e:
        logs.append(f"ERROR: {str(e)}")

    return logs
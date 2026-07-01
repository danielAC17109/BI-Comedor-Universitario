import os
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import text

from DATABASE.conexion import obtener_conexion


BASE_DIR = Path(__file__).resolve().parent

modelo_demanda = joblib.load(BASE_DIR / "modelo_demanda.pkl")
modelo_ingresos = joblib.load(BASE_DIR / "modelo_ingresos.pkl")
modelo_consumo = joblib.load(BASE_DIR / "modelo_consumo.pkl")


def predecir_demanda():

    engine = obtener_conexion()

    df = pd.read_sql(
        text("SELECT COUNT(*) AS total FROM fact_consumo"),
        engine
    )

    siguiente_indice = int(df.loc[0, "total"]) + 1

    prediccion = modelo_demanda.predict(
        pd.DataFrame({"indice": [siguiente_indice]})
    )

    return round(prediccion[0], 2)


def predecir_ingresos():

    engine = obtener_conexion()

    df = pd.read_sql(
        text("SELECT COUNT(*) AS total FROM fact_consumo"),
        engine
    )

    siguiente_indice = int(df.loc[0, "total"]) + 1

    prediccion = modelo_ingresos.predict(
        pd.DataFrame({"indice": [siguiente_indice]})
    )

    return round(prediccion[0], 2)


def predecir_consumo():

    engine = obtener_conexion()

    df = pd.read_sql(
        text("""
            SELECT AVG(da.personas_en_campus) AS promedio_aforo
            FROM fact_consumo fc
            INNER JOIN dim_aforo da
                ON fc.id_aforo = da.id_aforo
        """),
        engine
    )

    promedio_aforo = float(df.loc[0, "promedio_aforo"] or 0)

    prediccion = modelo_consumo.predict(
        pd.DataFrame({"personas_en_campus": [promedio_aforo]})
    )

    return round(prediccion[0], 2)
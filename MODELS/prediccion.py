import pandas as pd
from sklearn.linear_model import LinearRegression
from DATABASE.conexion import obtener_conexion


# =========================================
# PREDICCIÓN DEMANDA 
# =========================================

def predecir_demanda():

    # Uso de la función importada
    conexion = obtener_conexion()

    query = """

    SELECT
        comidas_servidas

    FROM fact_consumo

    """

    df = pd.read_sql(query, conexion)

    # GENERAR ÍNDICE LIMPIO 
    df['indice'] = range(1, len(df) + 1)

    X = df[['indice']]
    y = df['comidas_servidas']

    modelo = LinearRegression()

    modelo.fit(X, y)

    # FUTURO 
    futuro = pd.DataFrame({
        'indice': [len(df) + 1]
    })

    prediccion = modelo.predict(futuro)

    conexion.close()

    return round(prediccion[0], 2)


# =========================================
# PREDICCIÓN INGRESOS 
# =========================================

def predecir_ingresos():

    # Uso de la función importada
    conexion = obtener_conexion()

    query = """

    SELECT
        ingresos_cafeteria

    FROM fact_consumo

    """

    df = pd.read_sql(query, conexion)

    # GENERAR ÍNDICE LIMPIO 
    df['indice'] = range(1, len(df) + 1)

    X = df[['indice']]
    y = df['ingresos_cafeteria']

    modelo = LinearRegression()

    modelo.fit(X, y)

    # FUTURO 
    futuro = pd.DataFrame({
        'indice': [len(df) + 1]
    })

    prediccion = modelo.predict(futuro)

    conexion.close()

    return round(prediccion[0], 2)


# =========================================
# PREDICCIÓN CONSUMO
# =========================================

def predecir_consumo():

    # Uso de la función importada
    conexion = obtener_conexion()

    query = """

    SELECT
        personas_en_campus,
        comidas_servidas

    FROM fact_consumo fc

    INNER JOIN dim_aforo af
        ON fc.id_aforo = af.id_aforo

    """

    df = pd.read_sql(query, conexion)

    X = df[['personas_en_campus']]
    y = df['comidas_servidas']

    modelo = LinearRegression()

    modelo.fit(X, y)

    promedio_personas = df['personas_en_campus'].mean()

    futuro = pd.DataFrame({
        'personas_en_campus': [promedio_personas]
    })

    prediccion = modelo.predict(futuro)

    conexion.close()

    return round(prediccion[0], 2)
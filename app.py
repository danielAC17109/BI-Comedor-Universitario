from flask import Flask, render_template, request, redirect
import pandas as pd
import os


from sqlalchemy import text

# Importación de la conexión centralizada
from DATABASE.conexion import obtener_conexion

from ETL.generar_snowflake import generar_modelo
from ETL.etl import procesar_excel

from MODELS.prediccion import (
    predecir_demanda,
    predecir_ingresos,
    predecir_consumo
)

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# =========================
# INICIO
# =========================

@app.route('/')
def inicio():

    return render_template('index.html')


# =========================
# CARGA ARCHIVOS
# =========================

@app.route('/carga')
def carga():

    return render_template('carga.html')


# =========================
# UPLOAD + ETL
# =========================

@app.route('/upload', methods=['POST'])
def upload():

    archivo = request.files['archivo']

    if archivo:

        ruta = os.path.join(
            app.config['UPLOAD_FOLDER'],
            archivo.filename
        )

        archivo.save(ruta)

        resultado = procesar_excel(ruta)

        try:

            engine = obtener_conexion()

            df_preview = pd.read_sql(
                text("""
                    SELECT *
                    FROM staging_comedor
                    ORDER BY id_staging DESC
                    LIMIT 10
                """),
                engine
            )

            tabla = df_preview.to_html(
                classes="table table-striped table-dark",
                index=False
            )

        except Exception as e:

            tabla = f"""
            <div class="alert alert-danger">
                ERROR AL MOSTRAR STAGING:<br>{e}
            </div>
            """

        return render_template(
            'staging.html',
            logs=resultado,
            tabla=tabla
        )

    return "No se subió archivo"


# =========================
# STAGING
# =========================

@app.route('/staging')
def staging():

    try:

        # Cambio por la función centralizada
        conexion = obtener_conexion()

        df = pd.read_sql(
            "SELECT TOP 10 * FROM staging_comedor",
            conexion
        )

        tabla = df.to_html(
            classes='table table-striped',
            index=False
        )

        conexion.close()

    except Exception as e:

        print(e)

        tabla = "No hay datos"

    return render_template(
        'staging.html',
        tabla=tabla
    )

#==========================
# PROCESO ETL
#==========================

@app.route('/etl')
def etl():

    return render_template(
        'etl.html'
    )

# =========================
# SNOWFLAKE
# =========================

@app.route('/snowflake')
def snowflake():

    generar_modelo()

    return render_template('snowflake.html')


# =========================
# PREDICCIONES
# =========================

@app.route('/predicciones')
def predicciones():

    return render_template(
        'predicciones.html'
    )


@app.route(
    '/generar_prediccion',
    methods=['POST']
)
def generar_prediccion():

    tipo = request.form['tipo_prediccion']

    resultado = ""

    if tipo == 'demanda':

        resultado = (
            str(predecir_demanda())
            + " comidas estimadas "
        )

    elif tipo == 'ingresos':

        resultado = (
            "S/ "
            + str(predecir_ingresos())
            + " ingresos estimados "
        )

    elif tipo == 'consumo':

        resultado = (
            str(predecir_consumo())
            + " comidas estimadas según aforo "
        )

    return render_template(
        'predicciones.html',
        resultado=resultado
    )

#=======================
# KPIS
#=========================

@app.route('/kpis')
def kpis():

    return render_template('kpis.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    return render_template('dashboard.html')


@app.route('/abrir_dashboard')
def abrir_dashboard():

    ruta = os.path.abspath(
        'static/powerbi/dashboard_comedor.pbix'
    )

    os.startfile(ruta)

    return redirect('/dashboard')

# =========================
# MAIN
# =========================

if __name__ == '__main__':

    app.run(debug=True)
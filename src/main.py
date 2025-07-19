from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import statistics
from scipy.stats import binom
import math

app = FastAPI()

@app.get("/mpu/estadisticas")
def obtener_estadisticas():
    url = "http://localhost:8082/mpu"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los datos")

    datos = response.json()

    if not datos or "MPU" not in datos:
        return JSONResponse(content={"message": "No hay datos disponibles"}, status_code=200)

    registros = datos["MPU"]

    if not registros:
        return JSONResponse(content={"message": "No hay datos en 'MPU'"}, status_code=200)

    try:
        pasos = [item["pasos"] for item in registros if isinstance(item.get("pasos"), (int, float))]
    except (TypeError, KeyError):
        raise HTTPException(status_code=500, detail="Estructura de datos inválida: faltan claves 'pasos'")

    if len(pasos) < 2:
        raise HTTPException(status_code=400, detail="No hay suficientes datos para estadísticas")

    # Estadísticas: media y desviación estándar
    try:
        media = statistics.mean(pasos)
        desviacion = statistics.stdev(pasos)
    except statistics.StatisticsError:
        # Por si no hay suficiente variabilidad para stdev
        media = statistics.mean(pasos)
        desviacion = 0.0

    # Distribución binomial
    n = 60  # segundos por minuto
    # Probabilidad p debe estar entre 0 y 1
    p = media / n
    if p < 0:
        p = 0
    elif p > 1:
        p = 1

    # Cálculo probabilidad más de 50 pasos en 1 minuto
    try:
        prob_mas_50 = 1 - binom.cdf(50, n, p)
    except Exception:
        prob_mas_50 = 0.0

    # Clasificación de actividad
    activos = sum(1 for paso in pasos if paso > 30)
    inactivos = len(pasos) - activos
    porcentaje_activo = (activos / len(pasos) * 100) if pasos else 0

    # Aseguramos que no haya NaN en el retorno (en caso de algún cálculo extraño)
    def safe_round(value, digits=2):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return 0.0
        return round(value, digits)

    return {
        "media_pasos": safe_round(media),
        "desviacion_estandar": safe_round(desviacion),
        "prob_mas_50_pasos": safe_round(prob_mas_50, 4),
        "minutos_activos": activos,
        "minutos_inactivos": inactivos,
        "porcentaje_activo": safe_round(porcentaje_activo)
    }

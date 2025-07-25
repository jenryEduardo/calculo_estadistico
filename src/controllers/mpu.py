from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import statistics
from scipy.stats import binom
import math




def DataCompleteMPU():
    url = "https://vivaltest-back.namixcode.cc/mpu"
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
        temperaturas = [item["temperatura"] for item in registros if isinstance(item.get("temperatura"), (int, float))]
    except (TypeError, KeyError):
        raise HTTPException(status_code=500, detail="Estructura de datos inválida: faltan claves 'pasos' o 'temperatura'")

    if len(pasos) < 2 or len(temperaturas) < 2:
        raise HTTPException(status_code=400, detail="No hay suficientes datos para estadísticas")

    # Estadísticas de pasos
    try:
        media_pasos = statistics.mean(pasos)
        desviacion_pasos = statistics.stdev(pasos)
    except statistics.StatisticsError:
        media_pasos = statistics.mean(pasos)
        desviacion_pasos = 0.0

    # Distribución binomial
    n = 60
    p = media_pasos / n
    p = max(0, min(p, 1))
    try:
        prob_mas_50 = 1 - binom.cdf(50, n, p)
    except Exception:
        prob_mas_50 = 0.0

    # Clasificación actividad
    activos = sum(1 for paso in pasos if paso > 30)
    inactivos = len(pasos) - activos
    porcentaje_activo = (activos / len(pasos) * 100) if pasos else 0
    def safe_round(value, digits=2):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return 0.0
        return round(value, digits)
    return {
        # Pasos
        "media_pasos": safe_round(media_pasos),
        "desviacion_estandar_pasos": safe_round(desviacion_pasos),
        "prob_mas_50_pasos": safe_round(prob_mas_50, 4),
        "minutos_activos": activos,
        "minutos_inactivos": inactivos,
        "porcentaje_activo": safe_round(porcentaje_activo),
    
    }





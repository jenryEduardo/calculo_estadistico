from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import statistics
from scipy.stats import binom
import math

app = FastAPI()


@app.get("/bme280/estadisticas")
def estadisticas_bme280():
    url = "https://vivaltest-back.namixcode.cc/bme"  # <--- cambia esto según tu API
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los datos")

    datos = response.json()

    if not datos or "BME" not in datos:
        return JSONResponse(content={"message": "No hay datos disponibles"}, status_code=200)

    registros = datos["BME"]

    try:
        temperaturas = [d["temperatura"] for d in registros]
        presiones = [d["presion"] for d in registros]
        humedades = [d["humedad"] for d in registros]
    except KeyError:
        raise HTTPException(status_code=500, detail="Faltan campos en los datos")

    def calc_stats(data, umbral, tipo):
        media = statistics.mean(data)
        try:
            desviacion = statistics.stdev(data)
        except statistics.StatisticsError:
            desviacion = 0.0
        p = sum(1 for d in data if d > umbral) / len(data)
        p_binomial = 1 - binom.cdf(10, 20, p)  # ejemplo: 20 mediciones, más de 10 altas
        return {
            f"media_{tipo}": round(media, 2),
            f"desviacion_{tipo}": round(desviacion, 2),
            f"prob_{tipo}_alta": round(p * 100, 2),
            f"prob_binomial_{tipo}": round(p_binomial, 4)
        }

    return {
        **calc_stats(temperaturas, 25, "temperatura"),
        **calc_stats(presiones, 1010, "presion"),
        **calc_stats(humedades, 60, "humedad")
    }


@app.get("/mlx/estadisticas")
def estadisticas_mlx():
    url = "https://vivaltest-back.namixcode.cc/mlx"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los datos")

    datos = response.json()

    if not datos or "MLX" not in datos:
        return JSONResponse(content={"message": "No hay datos disponibles"}, status_code=200)

    registros = datos["MLX"]

    temp_amb = [d["temperatura_ambiente"] for d in registros]
    temp_obj = [d["temperatura_objeto"] for d in registros]

    def calc_mlx_stats(data, tipo):
        media = statistics.mean(data)
        try:
            desviacion = statistics.stdev(data)
        except statistics.StatisticsError:
            desviacion = 0.0
        p_alta = sum(1 for d in data if d > 30) / len(data)
        p_binomial = 1 - binom.cdf(10, 20, p_alta)
        return {
            f"media_{tipo}": round(media, 2),
            f"desviacion_{tipo}": round(desviacion, 2),
            f"prob_alta_{tipo}": round(p_alta * 100, 2),
            f"prob_binomial_{tipo}": round(p_binomial, 4)
        }

    return {
        **calc_mlx_stats(temp_amb, "ambiente"),
        **calc_mlx_stats(temp_obj, "objeto")
    }


@app.get("/mpu6050/estadisticas")
def estadisticas_mpu_pasos():
    url = "https://vivaltest-back.namixcode.cc/mpu/get"  # Cambia esto si tu endpoint real es otro
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los datos")

    datos = response.json()

    if not datos or "MPU6050" not in datos:
        return JSONResponse(content={"message": "No hay datos disponibles"}, status_code=200)

    registros = datos["MPU6050"]

    try:
        pasos = [r["pasos"] for r in registros]
    except KeyError:
        raise HTTPException(status_code=500, detail="El campo 'pasos' no está en los datos")

    # Estadísticas básicas
    media = statistics.mean(pasos)
    try:
        desviacion = statistics.stdev(pasos)
    except statistics.StatisticsError:
        desviacion = 0.0

    # Probabilidad de pasos altos (>10)
    p_alto = sum(1 for p in pasos if p > 10) / len(pasos)
    p_binomial = 1 - binom.cdf(5, 10, p_alto)

    # Clasificación de actividad
    categorias = {
        "sedentario": 0,
        "ligero": 0,
        "activo": 0,
        "muy_activo": 0
    }

    for p in pasos:
        if p <= 5:
            categorias["sedentario"] += 1
        elif p <= 10:
            categorias["ligero"] += 1
        elif p <= 20:
            categorias["activo"] += 1
        else:
            categorias["muy_activo"] += 1

    total = len(pasos)
    distribucion_actividad = {
        "sedentario": round(categorias["sedentario"] * 100 / total, 2),
        "ligero": round(categorias["ligero"] * 100 / total, 2),
        "activo": round(categorias["activo"] * 100 / total, 2),
        "muy_activo": round(categorias["muy_activo"] * 100 / total, 2)
    }

    # Retornar todo junto
    return {
        "media_pasos": round(media, 2),
        "desviacion_pasos": round(desviacion, 2),
        "prob_pasos_altos": round(p_alto * 100, 2),
        "prob_binomial_altos": round(p_binomial, 4),
        "distribucion_actividad": distribucion_actividad
    }
from datetime import date

import pandas as pd


MONITOREO_FREQ = "5min"


def obtener_rango_monitoreo(referencia=None):
    referencia = referencia or date.today()
    anio_objetivo = referencia.year - 1
    inicio = pd.Timestamp(year=anio_objetivo, month=12, day=31, hour=0, minute=0, second=0)
    fin = pd.Timestamp(year=anio_objetivo, month=12, day=31, hour=23, minute=59, second=59)
    return inicio, fin


def obtener_rango_monitoreo_serializado(referencia=None):
    inicio, fin = obtener_rango_monitoreo(referencia)
    return [inicio.isoformat(), fin.isoformat()]


def describir_rango_monitoreo(referencia=None):
    referencia = referencia or date.today()
    anio_objetivo = referencia.year - 1
    return f"31 de diciembre de {anio_objetivo} (00:00 a 23:59)"

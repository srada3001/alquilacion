import pandas as pd
import re
import unicodedata


def normalizar_texto(texto):
    normalizado = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(char for char in normalizado if not unicodedata.combining(char))
    limpio = re.sub(r"[^a-z0-9]+", "", sin_acentos.lower())
    return limpio


def formatear_valor_metrica(valor):
    if valor is None or pd.isna(valor):
        return "-"
    return f"{float(valor):.4f}"


def resolver_fila_resumen(summary, candidatos):
    if summary is None or summary.empty:
        return None

    candidatos_normalizados = [normalizar_texto(candidato) for candidato in candidatos]
    for row in summary.itertuples(index=False):
        feature = getattr(row, "feature", "")
        feature_normalizado = normalizar_texto(feature)
        if feature in candidatos or feature_normalizado in candidatos_normalizados:
            return row
    return None

import pandas as pd


OPERADORES_FILTRO = [
    {"label": "Mayor que", "value": ">"},
    {"label": "Mayor o igual que", "value": ">="},
    {"label": "Menor que", "value": "<"},
    {"label": "Menor o igual que", "value": "<="},
]


def construir_mascara_desde_df(df, filtros):
    if df.empty or not filtros:
        return None

    mascara = pd.Series(True, index=df.index)
    for filtro in filtros:
        columna = filtro.get("columna")
        operador = filtro.get("operador")
        valor = filtro.get("valor")

        if columna is None or operador is None or valor is None:
            continue
        if columna not in df.columns:
            continue

        serie = df[columna]
        if operador == ">":
            mascara &= serie > valor
        elif operador == ">=":
            mascara &= serie >= valor
        elif operador == "<":
            mascara &= serie < valor
        elif operador == "<=":
            mascara &= serie <= valor

    return mascara


def construir_mascara_rechazo_desde_df(df, filtros):
    if df.empty or not filtros:
        return None

    rechazo = pd.Series(False, index=df.index)
    for filtro in filtros:
        columna = filtro.get("columna")
        operador = filtro.get("operador")
        valor = filtro.get("valor")

        if columna is None or operador is None or valor is None:
            continue
        if columna not in df.columns:
            continue

        serie = df[columna]
        validos = serie.notna()
        if operador == ">":
            rechazo |= validos & ~(serie > valor)
        elif operador == ">=":
            rechazo |= validos & ~(serie >= valor)
        elif operador == "<":
            rechazo |= validos & ~(serie < valor)
        elif operador == "<=":
            rechazo |= validos & ~(serie <= valor)

    return rechazo

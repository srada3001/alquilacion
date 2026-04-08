import pandas as pd


def combinar_mascaras(*mascaras):
    mascaras_validas = [mascara for mascara in mascaras if mascara is not None]
    if not mascaras_validas:
        return None

    resultado = mascaras_validas[0].copy()
    for mascara in mascaras_validas[1:]:
        resultado &= mascara.reindex(resultado.index, fill_value=False)
    return resultado


def normalizar_filtros_guardados(filtros_guardados):
    if isinstance(filtros_guardados, dict):
        return {
            "variables": list(filtros_guardados.get("variables") or []),
            "fechas": list(filtros_guardados.get("fechas") or []),
        }
    return {
        "variables": list(filtros_guardados or []),
        "fechas": [],
    }


def obtener_filtros_variable(filtros_guardados):
    return normalizar_filtros_guardados(filtros_guardados)["variables"]


def obtener_filtros_fecha(filtros_guardados):
    return normalizar_filtros_guardados(filtros_guardados)["fechas"]


def construir_rango_fecha(filtro):
    inicio_dt = pd.to_datetime(filtro.get("inicio"), errors="coerce")
    fin_dt = pd.to_datetime(filtro.get("fin"), errors="coerce")
    if pd.isna(inicio_dt) or pd.isna(fin_dt):
        return None, None
    if fin_dt < inicio_dt:
        inicio_dt, fin_dt = fin_dt, inicio_dt
    return inicio_dt, fin_dt


def construir_mascara_fechas_desde_df(df, filtros_fecha):
    if df.empty or not filtros_fecha:
        return None

    mascara = pd.Series(False, index=df.index)
    indice = pd.to_datetime(df.index, errors="coerce")

    for filtro in filtros_fecha:
        inicio_dt, fin_dt = construir_rango_fecha(filtro)
        if inicio_dt is None or fin_dt is None:
            continue
        mascara |= (indice >= inicio_dt) & (indice <= fin_dt)

    return mascara


def construir_mascara_variables_desde_df(df, filtros_variable):
    if df.empty or not filtros_variable:
        return None

    mascara = pd.Series(True, index=df.index)
    for filtro in filtros_variable:
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


def construir_mascara_desde_df(df, filtros):
    filtros_variable = obtener_filtros_variable(filtros)
    filtros_fecha = obtener_filtros_fecha(filtros)

    if df.empty or (not filtros_variable and not filtros_fecha):
        return None

    mascara_variables = construir_mascara_variables_desde_df(df, filtros_variable)
    mascara_fechas = construir_mascara_fechas_desde_df(df, filtros_fecha)

    if mascara_variables is None:
        return mascara_fechas
    if mascara_fechas is None:
        return mascara_variables
    return combinar_mascaras(mascara_variables, mascara_fechas)


def construir_mascara_rechazo_desde_df(df, filtros):
    filtros_variable = obtener_filtros_variable(filtros)
    filtros_fecha = obtener_filtros_fecha(filtros)

    if df.empty or (not filtros_variable and not filtros_fecha):
        return None

    rechazo = pd.Series(False, index=df.index)
    for filtro in filtros_variable:
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

    mascara_fechas = construir_mascara_fechas_desde_df(df, filtros_fecha)
    if mascara_fechas is not None:
        rechazo |= ~mascara_fechas

    return rechazo

import pandas as pd


def _asegurar_serie_booleana(mascara):
    if mascara is None:
        return None
    if isinstance(mascara, pd.Series):
        return mascara.fillna(False).astype(bool)
    return pd.Series(mascara, dtype=bool)


def combinar_mascaras(*mascaras):
    mascaras_validas = [
        _asegurar_serie_booleana(mascara)
        for mascara in mascaras
        if mascara is not None
    ]
    if not mascaras_validas:
        return None

    resultado = mascaras_validas[0].copy()
    for mascara in mascaras_validas[1:]:
        resultado &= mascara.reindex(resultado.index, fill_value=False)
    return resultado


def normalizar_filtros_guardados(filtros_guardados):
    if isinstance(filtros_guardados, dict):
        periodo = filtros_guardados.get("periodo")
        if periodo is None:
            fechas = list(filtros_guardados.get("fechas") or [])
            periodo = fechas[0] if fechas else None
        return {
            "variables": list(filtros_guardados.get("variables") or []),
            "periodo": periodo,
        }
    return {
        "variables": list(filtros_guardados or []),
        "periodo": None,
    }


def obtener_filtros_variable(filtros_guardados):
    return normalizar_filtros_guardados(filtros_guardados)["variables"]


def obtener_filtro_periodo(filtros_guardados):
    return normalizar_filtros_guardados(filtros_guardados)["periodo"]


def construir_rango_fecha(periodo):
    if not periodo:
        return None, None
    inicio_dt = pd.to_datetime(periodo.get("inicio"), errors="coerce")
    fin_dt = pd.to_datetime(periodo.get("fin"), errors="coerce")
    if pd.isna(inicio_dt) or pd.isna(fin_dt):
        return None, None
    if fin_dt < inicio_dt:
        inicio_dt, fin_dt = fin_dt, inicio_dt
    return inicio_dt, fin_dt


def construir_mascara_periodo_desde_df(df, filtro_periodo):
    if df.empty or not filtro_periodo:
        return None

    indice = pd.to_datetime(df.index, errors="coerce")
    inicio_dt, fin_dt = construir_rango_fecha(filtro_periodo)
    if inicio_dt is None or fin_dt is None:
        return None
    return (indice >= inicio_dt) & (indice <= fin_dt)


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
    filtro_periodo = obtener_filtro_periodo(filtros)

    if df.empty or (not filtros_variable and not filtro_periodo):
        return None

    mascara_variables = construir_mascara_variables_desde_df(df, filtros_variable)
    mascara_periodo = construir_mascara_periodo_desde_df(df, filtro_periodo)

    if mascara_variables is None:
        return mascara_periodo
    if mascara_periodo is None:
        return mascara_variables
    return combinar_mascaras(mascara_variables, mascara_periodo)


def construir_mascara_rechazo_desde_df(df, filtros):
    filtros_variable = obtener_filtros_variable(filtros)
    filtro_periodo = obtener_filtro_periodo(filtros)

    if df.empty or (not filtros_variable and not filtro_periodo):
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

    mascara_periodo = construir_mascara_periodo_desde_df(df, filtro_periodo)
    if mascara_periodo is not None:
        rechazo |= ~mascara_periodo

    return rechazo

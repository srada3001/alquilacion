import pandas as pd
from functools import lru_cache

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.data import formatear_nombre_fase, obtener_columnas_fase


BADGE_CONTAINER_STYLE = {
    "display": "flex",
    "flexWrap": "wrap",
    "gap": "8px",
    "marginBottom": "12px",
}


BADGE_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "8px",
    "padding": "6px 10px",
    "border": "1px solid #d9d9d9",
    "borderRadius": "999px",
    "backgroundColor": "#f7f7f7",
}

ACCION_CIRCULAR_STYLE = {
    "width": "28px",
    "height": "28px",
    "borderRadius": "50%",
    "border": "none",
    "display": "inline-flex",
    "alignItems": "center",
    "justifyContent": "center",
    "fontSize": "18px",
    "fontWeight": "700",
    "lineHeight": "1",
    "cursor": "pointer",
    "color": "#ffffff",
}

ACCION_AGREGAR_STYLE = {
    **ACCION_CIRCULAR_STYLE,
    "backgroundColor": "#2e9f44",
}

ACCION_RETIRAR_STYLE = {
    **ACCION_CIRCULAR_STYLE,
    "backgroundColor": "#c83c3c",
}

TITULO_CENTRADO_STYLE = {
    "textAlign": "center",
}


GRUPO_PREFIX = "__grupo__::"
GRUPOS_VARIABLES = {
    "AI": "Niveles de oxigeno",
    "FI": "Flujos",
    "NI": "Niveles",
    "PD": "Presiones",
    "PI": "Presiones",
    "TI": "Temperaturas",
}

VENTANAS_PARADA = (
    ("2017-06-12 18:50", "2017-06-14 12:15"),
    ("2017-06-17 16:10", "2017-07-19 15:10"),
    ("2020-10-01 10:00", "2020-10-11 23:00"),
    ("2021-02-16 11:20", "2021-02-27 23:55"),
    ("2021-03-26 12:00", "2021-05-14 16:45"),
    ("2021-08-19 18:00", "2021-08-20 23:30"),
    ("2021-08-21 10:05", "2021-08-22 11:05"),
    ("2023-03-09 23:10", "2023-03-12 15:10"),
    ("2024-08-03 06:20", "2024-08-08 16:25"),
    ("2024-08-17 06:25", "2024-08-19 17:25"),
    ("2025-02-15 08:50", "2025-02-19 03:30"),
    ("2025-09-24 08:55", "2025-09-25 12:00"),
    ("2025-11-05 16:55", "2025-11-08 15:45"),
)


def normalizar_serie(serie):
    rango = serie.max() - serie.min()
    if rango == 0:
        return serie * 0
    return (serie - serie.min()) / rango


def construir_valor_columna(fase, columna):
    return f"{fase} | {columna}"


def separar_valor_columna(valor):
    return valor.split(" | ", 1)


def construir_etiqueta_fase(fase):
    return formatear_nombre_fase(fase)


def construir_etiqueta_columna(valor):
    fase, columna = separar_valor_columna(valor)
    return f"{construir_etiqueta_fase(fase)} | {columna}"


def construir_opciones_variables_por_fase(freq, fase, incluir_grupos=True):
    if not fase:
        return []

    columnas = sorted(obtener_columnas_fase(fase, freq))
    opciones = []

    if incluir_grupos:
        conteos_grupo = {}
        for columna in columnas:
            prefijo = columna[:2]
            if prefijo in GRUPOS_VARIABLES:
                conteos_grupo[prefijo] = conteos_grupo.get(prefijo, 0) + 1

        grupos = sorted(
            prefijo
            for prefijo, cantidad in conteos_grupo.items()
            if cantidad >= 2
        )
        opciones.extend(
            {"label": GRUPOS_VARIABLES[grupo], "value": f"{GRUPO_PREFIX}{grupo}"}
            for grupo in grupos
        )

    opciones.extend(
        {"label": columna, "value": construir_valor_columna(fase, columna)}
        for columna in columnas
    )
    return opciones


def expandir_valor_variable(freq, fase, valor):
    if not fase or not valor:
        return []
    if valor.startswith(GRUPO_PREFIX):
        grupo = valor.replace(GRUPO_PREFIX, "", 1)
        columnas = sorted(obtener_columnas_fase(fase, freq))
        return [
            construir_valor_columna(fase, columna)
            for columna in columnas
            if columna.startswith(grupo)
        ]
    return [valor]


def normalizar_lista_unica(valores):
    return sorted(set(valores), key=lambda x: x.lower())


def obtener_freq_desde_relayout(relayout_data):
    if not relayout_data:
        return "1h"

    inicio = relayout_data.get("xaxis.range[0]") or relayout_data.get("xaxis.range", [None, None])[0]
    fin = relayout_data.get("xaxis.range[1]") or relayout_data.get("xaxis.range", [None, None])[1]
    if not inicio or not fin:
        return "1h"

    try:
        inicio_dt = pd.to_datetime(inicio)
        fin_dt = pd.to_datetime(fin)
    except Exception:
        return "1h"

    if inicio_dt is None or fin_dt is None:
        return "1h"
    if pd.isna(inicio_dt) or pd.isna(fin_dt):
        return "1h"

    return "5min" if (fin_dt - inicio_dt).days < 365 else "1h"


def obtener_rango_desde_relayout(relayout_data):
    if not relayout_data:
        return None

    inicio = relayout_data.get("xaxis.range[0]") or relayout_data.get("xaxis.range", [None, None])[0]
    fin = relayout_data.get("xaxis.range[1]") or relayout_data.get("xaxis.range", [None, None])[1]
    if not inicio or not fin:
        return None
    return [inicio, fin]


def obtener_freq_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return "1h"
    return estado_grafico.get("freq", "1h")


def obtener_rango_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return None
    return estado_grafico.get("range")


def cargar_dataset_para_columnas(freq, columnas_requeridas, cargar_todo_si_vacio=False):
    columnas = list(dict.fromkeys(columnas_requeridas or []))
    if not columnas:
        if cargar_todo_si_vacio:
            return load_combined_dataset(freq)
        return pd.DataFrame()
    return load_combined_dataset(freq, columns=columnas)


@lru_cache(maxsize=2)
def get_shutdown_mask(freq):
    df = load_combined_dataset(freq)
    mask = pd.Series(False, index=df.index)
    for inicio, fin in VENTANAS_PARADA:
        inicio_ts = pd.Timestamp(inicio)
        fin_ts = pd.Timestamp(fin)
        mask |= (df.index >= inicio_ts) & (df.index <= fin_ts)
    return mask


def construir_mascara_modo_datos(df, modo_datos, freq):
    if df.empty or modo_datos == "todo":
        return None

    shutdown_mask = get_shutdown_mask(freq)
    shutdown_mask = shutdown_mask.reindex(df.index, fill_value=False)
    if modo_datos == "paradas":
        return shutdown_mask
    if modo_datos == "operacion":
        return ~shutdown_mask
    return None

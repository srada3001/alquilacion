from functools import lru_cache

import pandas as pd

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

MODO_OPERACION_OPCIONES = [
    {"label": "Toda la data", "value": "toda"},
    {"label": "Operacion normal", "value": "normal"},
]

EVENTOS_OPERACION = [
    ("2017-05-16 18:00", "2017-05-17 00:00", "2017-05-29 17:00", "2017-06-04 22:10"),
    ("2017-06-06 14:00", "2017-06-08 00:00", "2017-07-19 12:00", "2017-07-24 02:00"),
    ("2017-08-18 02:00", "2017-08-18 07:00", "2017-08-21 15:00", "2017-08-22 19:00"),
    ("2017-10-04 12:00", "2017-10-04 22:00", "2017-10-05 17:00", "2017-10-06 18:00"),
    ("2017-10-30 17:00", "2017-10-31 14:00", "2017-10-31 16:00", "2017-11-04 00:00"),
    ("2018-03-27 08:00", "2018-03-27 09:00", "2018-03-27 09:15", "2018-03-27 18:00"),
    ("2018-03-28 09:40", "2018-03-28 10:50", "2018-03-28 11:30", "2018-03-29 00:00"),
    ("2018-03-30 03:45", "2018-03-30 05:20", "2018-03-30 06:00", "2018-03-30 18:00"),
    ("2018-04-08 00:20", "2018-04-09 14:00", "2018-04-10 14:55", "2018-04-12 23:50"),
    ("2018-05-10 11:40", "2018-05-11 20:00", "2018-05-11 16:00", "2018-05-13 08:00"),
    ("2018-09-19 20:00", "2018-09-20 14:00", "2018-09-21 00:00", "2018-09-21 06:35"),
    ("2018-12-01 04:10", "2018-12-02 06:00", "2018-12-03 11:00", "2018-12-04 06:00"),
    ("2018-12-27 00:00", "2018-12-27 10:10", "2018-12-29 00:00", "2018-12-30 12:00"),
    ("2019-06-03 12:00", "2019-06-04 06:00", "2019-06-07 09:00", "2019-06-08 19:05"),
    ("2019-08-17 09:15", "2019-08-18 04:20", "2019-08-20 18:00", "2019-08-22 20:00"),
    ("2019-09-02 10:10", "2019-09-03 12:00", "2019-10-04 00:00", "2019-10-05 12:00"),
    ("2020-03-05 10:00", "2020-03-05 12:00", "2020-03-05 20:50", "2020-03-06 02:00"),
    ("2020-07-02 00:00", "2020-07-02 03:00", "2020-07-02 07:00", "2020-07-02 23:00"),
    ("2020-09-26 06:00", "2020-09-27 16:00", "2020-10-13 09:00", "2020-10-16 00:00"),
    ("2020-11-18 09:45", "2020-11-19 00:00", "2020-11-21 07:55", "2020-11-21 20:00"),
    ("2021-02-14 00:00", "2021-02-14 15:00", "2021-05-23 14:30", "2021-06-13 00:00"),
    ("2021-06-13 17:20", "2021-06-13 17:50", "2021-06-13 18:45", "2021-06-17 00:00"),
    ("2021-06-26 02:00", "2021-06-26 03:15", "2021-06-26 14:00", "2021-06-27 00:00"),
    ("2021-08-16 22:00", "2021-08-17 08:00", "2021-09-19 15:00", "2021-09-19 20:00"),
    ("2021-10-01 02:40", "2021-10-01 03:05", "2021-10-01 15:00", "2021-10-01 23:00"),
    ("2021-10-03 09:45", "2021-10-03 11:05", "2021-10-05 11:00", "2021-10-06 07:40"),
    ("2021-10-22 10:00", "2021-10-22 23:59", "2021-10-23 01:00", "2021-10-23 09:45"),
    ("2021-11-29 06:00", "2021-12-01 11:05", "2021-12-03 11:00", "2021-12-04 09:30"),
    ("2021-12-26 13:35", "2021-12-26 15:50", "2021-12-31 07:45", "2021-12-31 19:00"),
    ("2022-01-03 17:00", "2022-01-04 15:15", "2022-01-06 09:50", "2022-01-08 04:00"),
    ("2022-01-15 15:05", "2022-01-15 15:05", "2022-01-22 00:00", "2022-01-22 17:35"),
    ("2022-04-03 06:35", "2022-04-03 07:25", "2022-04-03 19:15", "2022-04-06 16:20"),
    ("2022-05-04 18:00", "2022-05-04 20:20", "2022-05-05 14:10", "2022-05-05 19:25"),
    ("2022-10-14 10:20", "2022-10-14 11:20", "2022-10-16 03:15", "2022-10-16 19:00"),
    ("2023-03-07 16:35", "2023-03-08 00:00", "2023-03-14 06:10", "2023-03-14 18:00"),
    ("2024-07-29 11:35", "2024-07-29 16:25", "2024-08-11 05:20", "2024-08-11 18:20"),
    ("2024-08-16 07:25", "2024-08-16 07:40", "2024-08-23 13:30", "2024-08-24 00:00"),
    ("2024-10-05 10:00", "2024-10-05 20:10", "2024-10-06 21:20", "2024-10-07 06:00"),
    ("2024-11-28 11:50", "2024-11-28 12:45", "2024-11-30 04:30", "2024-11-30 10:45"),
    ("2025-02-01 21:55", "2025-02-01 22:40", "2025-02-04 17:40", "2025-02-05 06:00"),
    ("2025-02-14 16:05", "2025-02-14 16:30", "2025-02-20 12:40", "2025-02-21 00:00"),
    ("2025-03-16 12:45", "2025-03-16 13:45", "2025-03-17 05:00", "2025-03-17 18:00"),
    ("2025-07-05 05:00", "2025-07-05 06:20", "2025-07-05 10:20", "2025-07-05 14:00"),
    ("2025-09-23 11:00", "2025-09-23 14:45", "2025-09-30 20:25", "2025-10-01 18:00"),
    ("2025-11-03 08:20", "2025-11-03 19:00", "2025-11-10 02:40", "2025-11-11 00:00"),
    ("2025-11-29 07:20", "2025-11-29 08:05", "2025-11-30 05:00", "2025-11-30 12:15"),
    ("2026-02-22 07:00", "2026-02-22 12:00", None, None),
]

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


def obtener_freq_efectiva(estado_grafico, modo_operacion="toda", arranque_id=None, parada_id=None):
    if arranque_id or parada_id:
        return "5min"
    if modo_operacion != "toda":
        return "1h"
    return obtener_freq_desde_estado_grafico(estado_grafico)


def obtener_rango_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return None
    return estado_grafico.get("range")


def obtener_eventos_operacion():
    eventos = []
    for indice, (parada_inicio, parada_fin, arranque_inicio, arranque_fin) in enumerate(EVENTOS_OPERACION, start=1):
        eventos.append(
            {
                "arranque_id": f"arranque-{indice:02d}",
                "parada_id": f"parada-{indice:02d}",
                "indice": indice,
                "parada_inicio": pd.Timestamp(parada_inicio),
                "parada_fin": pd.Timestamp(parada_fin),
                "arranque_inicio": pd.Timestamp(arranque_inicio) if arranque_inicio else None,
                "arranque_fin": pd.Timestamp(arranque_fin) if arranque_fin else None,
            }
        )
    return eventos


def formatear_timestamp_corto(valor):
    if valor is None or pd.isna(valor):
        return "-"
    return pd.Timestamp(valor).strftime("%Y-%m-%d %H:%M")


def construir_opciones_arranques():
    opciones = []
    for evento in obtener_eventos_operacion():
        if evento["arranque_inicio"] is None or evento["arranque_fin"] is None:
            continue
        opciones.append(
            {
                "label": (
                    f"Arranque {evento['indice']:02d}: "
                    f"{formatear_timestamp_corto(evento['arranque_inicio'])} a "
                    f"{formatear_timestamp_corto(evento['arranque_fin'])}"
                ),
                "value": evento["arranque_id"],
            }
        )
    return opciones


def construir_opciones_paradas():
    opciones = []
    for evento in obtener_eventos_operacion():
        if evento["parada_inicio"] is None or evento["parada_fin"] is None:
            continue
        opciones.append(
            {
                "label": (
                    f"Parada {evento['indice']:02d}: "
                    f"{formatear_timestamp_corto(evento['parada_inicio'])} a "
                    f"{formatear_timestamp_corto(evento['parada_fin'])}"
                ),
                "value": evento["parada_id"],
            }
        )
    return opciones


@lru_cache(maxsize=2)
def get_operational_reference_index():
    df_5min = load_combined_dataset("5min")
    return df_5min.index


@lru_cache(maxsize=1)
def get_downtime_mask_5min():
    indice_5min = get_operational_reference_index()
    mask = pd.Series(False, index=indice_5min)
    if mask.empty:
        return mask

    ultimo_timestamp = indice_5min.max()
    for evento in obtener_eventos_operacion():
        inicio = evento["parada_fin"]
        fin = evento["arranque_inicio"] if evento["arranque_inicio"] is not None else ultimo_timestamp
        if inicio is None or fin is None or fin <= inicio:
            continue
        mask |= (indice_5min >= inicio) & (indice_5min < fin)
    return mask


def construir_mascara_contexto_operacion(df, modo_operacion="toda", arranque_id=None, parada_id=None):
    if df.empty:
        return None

    mascara = None

    if modo_operacion == "normal":
        downtime_mask = get_downtime_mask_5min().reindex(df.index, fill_value=False)
        mascara = ~downtime_mask

    if arranque_id:
        evento = next(
            (item for item in obtener_eventos_operacion() if item["arranque_id"] == arranque_id),
            None,
        )
        if evento is None or evento["arranque_inicio"] is None or evento["arranque_fin"] is None:
            arranque_mask = pd.Series(False, index=df.index)
        else:
            indice_5min = get_operational_reference_index()
            arranque_mask_5min = pd.Series(
                (indice_5min >= evento["arranque_inicio"]) & (indice_5min <= evento["arranque_fin"]),
                index=indice_5min,
            )
            arranque_mask = arranque_mask_5min.reindex(df.index, fill_value=False)
        mascara = arranque_mask if mascara is None else (mascara & arranque_mask)

    if parada_id:
        evento = next(
            (item for item in obtener_eventos_operacion() if item["parada_id"] == parada_id),
            None,
        )
        if evento is None or evento["parada_inicio"] is None or evento["parada_fin"] is None:
            parada_mask = pd.Series(False, index=df.index)
        else:
            indice_5min = get_operational_reference_index()
            parada_mask_5min = pd.Series(
                (indice_5min >= evento["parada_inicio"]) & (indice_5min <= evento["parada_fin"]),
                index=indice_5min,
            )
            parada_mask = parada_mask_5min.reindex(df.index, fill_value=False)
        mascara = parada_mask if mascara is None else (mascara & parada_mask)

    return mascara


def cargar_dataset_para_columnas(freq, columnas_requeridas, cargar_todo_si_vacio=False):
    columnas = list(dict.fromkeys(columnas_requeridas or []))
    if not columnas:
        if cargar_todo_si_vacio:
            return load_combined_dataset(freq)
        return pd.DataFrame()
    return load_combined_dataset(freq, columns=columnas)

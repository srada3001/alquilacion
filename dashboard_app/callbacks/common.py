from functools import lru_cache

import pandas as pd

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.data import formatear_nombre_fase, obtener_columnas_fase
from dashboard_app.domain.filters import (
    construir_rango_fecha,
    normalizar_filtros_guardados,
    obtener_filtros_fecha,
)
from dashboard_app.domain.operation_events import obtener_eventos_operacion, obtener_operaciones


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
    {"label": "Operación completa", "value": "completa"},
]

UMBRAL_REESCALADO = pd.Timedelta(days=365)

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

        # Merge PI and PD pressure groups
        pi_count = conteos_grupo.get("PI", 0)
        pd_count = conteos_grupo.get("PD", 0)
        grupos_merged = set(conteos_grupo.keys()) - {"PI", "PD"}
        
        # Add other groups with 2+ variables
        grupos = [
            prefijo
            for prefijo in sorted(grupos_merged)
            if conteos_grupo[prefijo] >= 2
        ]
        
        # Add merged pressure group if either PI or PD has 2+ variables
        if pi_count + pd_count >= 2:
            grupos.append("P")
        
        for grupo in sorted(grupos):
            if grupo == "P":
                opciones.append({"label": "Presiones", "value": f"{GRUPO_PREFIX}P"})
            else:
                opciones.append({"label": GRUPOS_VARIABLES[grupo], "value": f"{GRUPO_PREFIX}{grupo}"})

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
        
        # Handle merged pressure group (P matches both PI and PD)
        if grupo == "P":
            return [
                construir_valor_columna(fase, columna)
                for columna in columnas
                if columna.startswith("PI") or columna.startswith("PD")
            ]
        
        return [
            construir_valor_columna(fase, columna)
            for columna in columnas
            if columna.startswith(grupo)
        ]
    return [valor]


def normalizar_lista_unica(valores):
    return sorted(set(valores), key=lambda x: x.lower())


def resolver_freq_desde_rango(rango, freq_por_defecto="1h"):
    if not rango or len(rango) < 2:
        return freq_por_defecto

    inicio_dt = pd.to_datetime(rango[0], errors="coerce")
    fin_dt = pd.to_datetime(rango[1], errors="coerce")
    return resolver_freq_por_periodo(inicio_dt, fin_dt, freq_por_defecto)


def resolver_freq_por_periodo(inicio_dt, fin_dt, freq_por_defecto="1h"):
    if inicio_dt is None or fin_dt is None:
        return freq_por_defecto
    if pd.isna(inicio_dt) or pd.isna(fin_dt):
        return freq_por_defecto
    if fin_dt < inicio_dt:
        inicio_dt, fin_dt = fin_dt, inicio_dt
    return "5min" if (fin_dt - inicio_dt) < UMBRAL_REESCALADO else "1h"


def obtener_freq_desde_relayout(relayout_data):
    if not relayout_data:
        return "1h"

    rango = obtener_rango_desde_relayout(relayout_data)
    if rango is None:
        return "1h"
    return resolver_freq_desde_rango(rango)


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
    return resolver_freq_desde_rango(
        estado_grafico.get("range"),
        estado_grafico.get("freq", "1h"),
    )


def obtener_freq_desde_filtros_fecha(filtros_guardados):
    filtros_fecha = obtener_filtros_fecha(normalizar_filtros_guardados(filtros_guardados))
    if not filtros_fecha:
        return None

    frecuencias = []
    for filtro in filtros_fecha:
        inicio_dt, fin_dt = construir_rango_fecha(filtro)
        if inicio_dt is None or fin_dt is None:
            continue
        frecuencias.append(resolver_freq_por_periodo(inicio_dt, fin_dt))

    if not frecuencias:
        return None
    return "5min" if all(freq == "5min" for freq in frecuencias) else "1h"


def obtener_freq_efectiva(
    estado_grafico,
    filtros_guardados=None,
    modo_operacion="toda",
    arranque_id=None,
    parada_id=None,
    operacion_id=None,
):
    if arranque_id or parada_id or operacion_id:
        return "5min"
    freq_filtros = obtener_freq_desde_filtros_fecha(filtros_guardados)
    if freq_filtros is not None:
        return freq_filtros
    return obtener_freq_desde_estado_grafico(estado_grafico)


def obtener_rango_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return None
    return estado_grafico.get("range")


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


def construir_opciones_operaciones():
    opciones = []
    for operacion in obtener_operaciones():
        opciones.append(
            {
                "label": (
                    f"Operación {operacion['indice']:02d}: "
                    f"{formatear_timestamp_corto(operacion['operacion_inicio'])} a "
                    f"{formatear_timestamp_corto(operacion['operacion_fin'])}"
                ),
                "value": operacion["operacion_id"],
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


def construir_mascara_contexto_operacion(
    df,
    modo_operacion="toda",
    arranque_id=None,
    parada_id=None,
    operacion_id=None,
):
    if df.empty:
        return None

    mascara = None

    if modo_operacion == "completa":
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

    if operacion_id:
        operacion = next(
            (item for item in obtener_operaciones() if item["operacion_id"] == operacion_id),
            None,
        )
        if operacion is None or operacion["operacion_inicio"] is None or operacion["operacion_fin"] is None:
            operacion_mask = pd.Series(False, index=df.index)
        else:
            indice_5min = get_operational_reference_index()
            operacion_mask_5min = pd.Series(
                (indice_5min >= operacion["operacion_inicio"]) & (indice_5min <= operacion["operacion_fin"]),
                index=indice_5min,
            )
            operacion_mask = operacion_mask_5min.reindex(df.index, fill_value=False)
        mascara = operacion_mask if mascara is None else (mascara & operacion_mask)

    return mascara


def cargar_dataset_para_columnas(
    freq,
    columnas_requeridas,
    cargar_todo_si_vacio=False,
    rango_tiempo=None,
):
    columnas = list(dict.fromkeys(columnas_requeridas or []))
    if not columnas:
        if cargar_todo_si_vacio:
            return load_combined_dataset(freq, time_range=rango_tiempo)
        return pd.DataFrame()
    return load_combined_dataset(freq, columns=columnas, time_range=rango_tiempo)

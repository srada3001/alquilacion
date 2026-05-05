from functools import lru_cache

import pandas as pd

from analysis_core.operation_events import obtener_eventos_operacion, obtener_operaciones
from data_processing.analysis_dataset import load_combined_dataset


@lru_cache(maxsize=1)
def get_operational_reference_index():
    return load_combined_dataset("5min").index


def _construir_mascara_intervalo(df_index, inicio, fin):
    if inicio is None or fin is None or fin <= inicio:
        return pd.Series(False, index=df_index)

    indice_5min = get_operational_reference_index()
    mascara_5min = pd.Series(
        (indice_5min >= inicio) & (indice_5min <= fin),
        index=indice_5min,
    )
    return mascara_5min.reindex(df_index, fill_value=False)


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
    modo_operacion=None,
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
        arranque_mask = _construir_mascara_intervalo(
            df.index,
            evento["arranque_inicio"] if evento else None,
            evento["arranque_fin"] if evento else None,
        )
        mascara = arranque_mask if mascara is None else (mascara & arranque_mask)

    if parada_id:
        evento = next(
            (item for item in obtener_eventos_operacion() if item["parada_id"] == parada_id),
            None,
        )
        parada_mask = _construir_mascara_intervalo(
            df.index,
            evento["parada_inicio"] if evento else None,
            evento["parada_fin"] if evento else None,
        )
        mascara = parada_mask if mascara is None else (mascara & parada_mask)

    if operacion_id:
        operacion = next(
            (item for item in obtener_operaciones() if item["operacion_id"] == operacion_id),
            None,
        )
        operacion_mask = _construir_mascara_intervalo(
            df.index,
            operacion["operacion_inicio"] if operacion else None,
            operacion["operacion_fin"] if operacion else None,
        )
        mascara = operacion_mask if mascara is None else (mascara & operacion_mask)

    return mascara


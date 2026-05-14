import pandas as pd
import plotly.graph_objects as go

from dashboard_app.callbacks.common import construir_etiqueta_columna, normalizar_serie
from dashboard_app.data import obtener_unidad_columna

UNIDAD_SIN_DEFINIR = "Sin unidad definida"
UNIDAD_NORMALIZADA = "Valor normalizado"
EJE_RESERVA_POR_LADO = 0.09


def completar_indice_temporal(df, freq, rango_tiempo=None):
    if df.empty:
        return df

    inicio = df.index.min()
    fin = df.index.max()
    if rango_tiempo and len(rango_tiempo) >= 2:
        inicio_rango = pd.to_datetime(rango_tiempo[0], errors="coerce")
        fin_rango = pd.to_datetime(rango_tiempo[1], errors="coerce")
        if not pd.isna(inicio_rango) and not pd.isna(fin_rango):
            if fin_rango < inicio_rango:
                inicio_rango, fin_rango = fin_rango, inicio_rango
            inicio = min(inicio, inicio_rango)
            fin = max(fin, fin_rango)

    if pd.isna(inicio) or pd.isna(fin):
        return df

    indice_completo = pd.date_range(
        start=inicio.floor(freq),
        end=fin.ceil(freq),
        freq=freq,
    )
    return df.reindex(indice_completo)


def construir_clave_eje(columna, normalizar=False):
    if normalizar:
        return UNIDAD_NORMALIZADA

    unidad = obtener_unidad_columna(columna)
    return unidad or UNIDAD_SIN_DEFINIR


def resolver_configuracion_ejes(unidades):
    unidades = list(dict.fromkeys(unidades))
    if not unidades:
        return {}, {}

    layout_updates = {}
    referencias = {}
    lado_extra_por_indice = {}
    conteo_lados = {"left": 0, "right": 0}

    for indice, unidad in enumerate(unidades, start=1):
        referencia_traza = "y" if indice == 1 else f"y{indice}"
        referencia_layout = "yaxis" if indice == 1 else f"yaxis{indice}"
        lado = "left" if indice == 1 or indice % 2 == 1 else "right"
        referencias[unidad] = referencia_traza
        lado_extra_por_indice[indice] = lado

        config = {
            "title": {"text": unidad, "standoff": 12},
            "automargin": True,
            "showgrid": indice == 1,
            "zeroline": False,
        }
        if indice == 1:
            config["side"] = "left"
        else:
            config["overlaying"] = "y"
            config["anchor"] = "free"
            config["side"] = lado
            config["shift"] = -12 if lado == "left" else 12
            conteo_lados[lado] += 1
            orden_lateral = conteo_lados[lado]
            config["_orden_lateral"] = orden_lateral

        layout_updates[referencia_layout] = config

    dominio_x_inicio = EJE_RESERVA_POR_LADO * conteo_lados["left"]
    dominio_x_fin = 1 - (EJE_RESERVA_POR_LADO * conteo_lados["right"])

    for indice, _unidad in enumerate(unidades, start=1):
        if indice == 1:
            continue

        referencia_layout = "yaxis" if indice == 1 else f"yaxis{indice}"
        config = layout_updates[referencia_layout]
        orden_lateral = config.pop("_orden_lateral")
        lado = lado_extra_por_indice[indice]
        if lado == "left":
            config["position"] = EJE_RESERVA_POR_LADO * (orden_lateral - 0.5)
        else:
            config["position"] = dominio_x_fin + (
                EJE_RESERVA_POR_LADO * (orden_lateral - 0.5)
            )

    layout_updates["xaxis"] = {
        "type": "date",
        "domain": [dominio_x_inicio, dominio_x_fin],
    }
    layout_updates["margin"] = {
        "l": 85 + (65 * conteo_lados["left"]),
        "r": 85 + (65 * conteo_lados["right"]),
        "t": 40,
        "b": 40,
    }
    return referencias, layout_updates


def agrupar_columnas_por_unidad(columnas, normalizar=False):
    grupos = {}
    for columna in columnas:
        clave = construir_clave_eje(columna, normalizar=normalizar)
        grupos.setdefault(clave, []).append(columna)
    return grupos


def construir_figura_series_temporales(
    df_grafico,
    columnas,
    normalizar=False,
    multi_eje=True,
    uirevision=None,
    rango_visible=None,
):
    fig = go.Figure()
    columnas_visibles = [col for col in columnas if col in df_grafico.columns]
    if not columnas_visibles:
        return fig

    grupos_unidad = agrupar_columnas_por_unidad(columnas_visibles, normalizar=normalizar)
    unidades_visibles = list(grupos_unidad.keys())
    referencias_eje, layout_ejes = resolver_configuracion_ejes(
        unidades_visibles if multi_eje else unidades_visibles[:1]
    )
    eje_unico = referencias_eje.get(unidades_visibles[0], "y") if unidades_visibles else "y"

    for col in columnas_visibles:
        serie = normalizar_serie(df_grafico[col]) if normalizar else df_grafico[col]
        clave_eje = construir_clave_eje(col, normalizar=normalizar)
        fig.add_trace(
            go.Scatter(
                x=df_grafico.index,
                y=serie,
                mode="lines",
                name=construir_etiqueta_columna(col),
                connectgaps=False,
                yaxis=referencias_eje.get(clave_eje, "y") if multi_eje else eje_unico,
            )
        )

    fig.update_layout(
        hovermode="x unified",
        showlegend=True,
        uirevision=uirevision,
        **layout_ejes,
    )
    if rango_visible is not None:
        fig.update_layout(xaxis_range=rango_visible)
    return fig

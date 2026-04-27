from dash import Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard_app.callbacks.common import (
    cargar_dataset_para_columnas,
    construir_mascara_contexto_operacion,
    construir_etiqueta_columna,
    normalizar_serie,
    obtener_freq_efectiva,
    obtener_freq_desde_relayout,
    obtener_rango_desde_estado_grafico,
    obtener_rango_desde_relayout,
)
from dashboard_app.data import obtener_unidad_columna
from dashboard_app.domain.filters import combinar_mascaras
from dashboard_app.domain.filters import construir_mascara_desde_df
from dashboard_app.domain.filters import obtener_filtros_variable
from dashboard_app.domain.filters import normalizar_filtros_guardados


UNIDAD_SIN_DEFINIR = "Sin unidad definida"
UNIDAD_NORMALIZADA = "Valor normalizado"
EJE_RESERVA_POR_LADO = 0.06


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
            "title": unidad,
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
            conteo_lados[lado] += 1
            orden_lateral = conteo_lados[lado]
            config["_orden_lateral"] = orden_lateral

        layout_updates[referencia_layout] = config

    dominio_x_inicio = EJE_RESERVA_POR_LADO * conteo_lados["left"]
    dominio_x_fin = 1 - (EJE_RESERVA_POR_LADO * conteo_lados["right"])

    for indice, unidad in enumerate(unidades, start=1):
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
        "l": 70 + (45 * conteo_lados["left"]),
        "r": 70 + (45 * conteo_lados["right"]),
        "t": 40,
        "b": 40,
    }
    return referencias, layout_updates


def register_timeseries_callbacks(app):
    @app.callback(
        Output("estado-grafico-store", "data", allow_duplicate=True),
        Input("grafico", "relayoutData"),
        State("estado-grafico-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_estado_grafico(relayout_data, estado_grafico):
        estado_grafico = dict(estado_grafico or {"freq": "1h", "range": None})
        if not relayout_data:
            return no_update

        if relayout_data.get("xaxis.autorange"):
            nuevo_estado = {"freq": "1h", "range": None}
            return no_update if nuevo_estado == estado_grafico else nuevo_estado

        rango = obtener_rango_desde_relayout(relayout_data)
        if rango is None:
            return no_update

        nuevo_estado = {
            "freq": obtener_freq_desde_relayout(relayout_data),
            "range": rango,
        }
        return no_update if nuevo_estado == estado_grafico else nuevo_estado

    @app.callback(
        Output("grafico", "figure"),
        Input("estado-grafico-store", "data"),
        Input("normalizar-checklist", "value"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtros-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
        Input("filtro-operacion-dropdown", "value"),
    )
    def actualizar_grafico(
        estado_grafico,
        normalizar_opciones,
        variables_seleccionadas,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
    ):
        rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
        columnas = list(variables_seleccionadas or [])
        if not columnas:
            return go.Figure()

        filtros_guardados = normalizar_filtros_guardados(filtros_guardados)
        columnas_requeridas = columnas + [
            filtro["columna"]
            for filtro in obtener_filtros_variable(filtros_guardados)
            if filtro.get("columna")
        ]
        freq = obtener_freq_efectiva(
            estado_grafico,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )
        df_combinado = cargar_dataset_para_columnas(
            freq,
            columnas_requeridas,
            cargar_todo_si_vacio=modo_operacion != "toda" or bool(arranque_id) or bool(parada_id) or bool(operacion_id),
            rango_tiempo=rango_visible,
        )
        mascara = combinar_mascaras(
            construir_mascara_desde_df(df_combinado, filtros_guardados),
            construir_mascara_contexto_operacion(df_combinado, modo_operacion, arranque_id, parada_id, operacion_id),
        )
        if mascara is not None:
            mascara = mascara.reindex(df_combinado.index, fill_value=False)
            df_grafico = df_combinado.loc[mascara].copy()
        else:
            df_grafico = df_combinado

        normalizar = "normalizar" in (normalizar_opciones or [])
        fig = go.Figure()
        unidades_visibles = []

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            clave_eje = construir_clave_eje(col, normalizar=normalizar)
            unidades_visibles.append(clave_eje)
        referencias_eje, layout_ejes = resolver_configuracion_ejes(unidades_visibles)

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            serie = normalizar_serie(df_grafico[col]) if normalizar else df_grafico[col]
            clave_eje = construir_clave_eje(col, normalizar=normalizar)
            fig.add_trace(
                go.Scatter(
                    x=df_grafico.index,
                    y=serie,
                    mode="lines",
                    name=construir_etiqueta_columna(col),
                    connectgaps=False,
                    yaxis=referencias_eje.get(clave_eje, "y"),
                )
            )

        fig.update_layout(
            hovermode="x unified",
            showlegend=True,
            uirevision=(
                f"grafico-principal::{modo_operacion}::"
                f"{arranque_id or 'sin-arranque'}::{parada_id or 'sin-parada'}::"
                f"{operacion_id or 'sin-operacion'}"
            ),
            **layout_ejes,
        )
        if rango_visible is not None and modo_operacion == "toda" and not arranque_id and not parada_id and not operacion_id:
            fig.update_layout(xaxis_range=rango_visible)
        return fig

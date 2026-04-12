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
from dashboard_app.domain.filters import combinar_mascaras
from dashboard_app.domain.filters import construir_mascara_desde_df
from dashboard_app.domain.filters import obtener_filtros_variable
from dashboard_app.domain.filters import normalizar_filtros_guardados


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
    )
    def actualizar_grafico(
        estado_grafico,
        normalizar_opciones,
        variables_seleccionadas,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
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
        )
        df_combinado = cargar_dataset_para_columnas(
            freq,
            columnas_requeridas,
            cargar_todo_si_vacio=modo_operacion != "toda" or bool(arranque_id) or bool(parada_id),
            rango_tiempo=rango_visible,
        )
        mascara = combinar_mascaras(
            construir_mascara_desde_df(df_combinado, filtros_guardados),
            construir_mascara_contexto_operacion(df_combinado, modo_operacion, arranque_id, parada_id),
        )
        if mascara is not None:
            mascara = mascara.reindex(df_combinado.index, fill_value=False)
            df_grafico = df_combinado.loc[mascara].copy()
        else:
            df_grafico = df_combinado

        normalizar = "normalizar" in (normalizar_opciones or [])
        fig = go.Figure()

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            serie = normalizar_serie(df_grafico[col]) if normalizar else df_grafico[col]
            fig.add_trace(
                go.Scatter(
                    x=df_grafico.index,
                    y=serie,
                    mode="lines",
                    name=construir_etiqueta_columna(col),
                    connectgaps=False,
                )
            )

        fig.update_layout(
            hovermode="x unified",
            xaxis=dict(type="date"),
            showlegend=True,
            uirevision=(
                f"grafico-principal::{modo_operacion}::"
                f"{arranque_id or 'sin-arranque'}::{parada_id or 'sin-parada'}"
            ),
        )
        if rango_visible is not None and modo_operacion == "toda" and not arranque_id and not parada_id:
            fig.update_layout(xaxis_range=rango_visible)
        return fig

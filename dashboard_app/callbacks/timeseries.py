from dash import Input, Output, State
import plotly.graph_objects as go

from dashboard_app.callbacks.common import (
    cargar_dataset_para_columnas,
    construir_etiqueta_columna,
    normalizar_serie,
    obtener_freq_desde_estado_grafico,
    obtener_freq_desde_relayout,
    obtener_rango_desde_estado_grafico,
    obtener_rango_desde_relayout,
)
from dashboard_app.domain.filters import construir_mascara_desde_df


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
            return estado_grafico

        if relayout_data.get("xaxis.autorange"):
            return {"freq": "1h", "range": None}

        rango = obtener_rango_desde_relayout(relayout_data)
        if rango is None:
            return estado_grafico

        return {
            "freq": obtener_freq_desde_relayout(relayout_data),
            "range": rango,
        }

    @app.callback(
        Output("grafico", "figure"),
        Input("estado-grafico-store", "data"),
        Input("normalizar-checklist", "value"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtros-store", "data"),
    )
    def actualizar_grafico(estado_grafico, normalizar_opciones, variables_seleccionadas, filtros_guardados):
        rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
        columnas = list(variables_seleccionadas or [])
        if not columnas:
            return go.Figure()

        filtros_guardados = list(filtros_guardados or [])
        columnas_requeridas = columnas + [
            filtro["columna"] for filtro in filtros_guardados if filtro.get("columna")
        ]
        freq = obtener_freq_desde_estado_grafico(estado_grafico)
        df_combinado = cargar_dataset_para_columnas(freq, columnas_requeridas)
        mascara = construir_mascara_desde_df(df_combinado, filtros_guardados)
        df_grafico = df_combinado.where(mascara) if mascara is not None else df_combinado

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
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            showlegend=True,
            uirevision="grafico-principal",
        )
        if rango_visible is not None:
            fig.update_layout(xaxis_range=rango_visible)
        return fig

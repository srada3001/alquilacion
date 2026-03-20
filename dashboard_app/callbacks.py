from dash import Input, Output, html
import plotly.graph_objects as go

from dashboard_app.data import (
    GRUPOS,
    cargar_dataframes,
    combinar_dataframes_por_fase,
)


def normalizar_serie(serie):
    rango = serie.max() - serie.min()
    if rango == 0:
        return serie * 0
    return (serie - serie.min()) / rango


def construir_tabla_correlacion(columna, correlaciones):
    filas = [
        html.Tr(
            [
                html.Th("Variable"),
                html.Th("Correlacion"),
            ]
        )
    ]

    for variable, valor in correlaciones.items():
        filas.append(
            html.Tr(
                [
                    html.Td(variable),
                    html.Td(f"{valor:.4f}"),
                ]
            )
        )

    return html.Div(
        [
            html.H4(columna),
            html.Table(filas),
        ]
    )


def obtener_columnas_por_grupo(dataframes, grupo):
    columnas = []

    for fase, df in dataframes.items():
        columnas.extend(
            [
                f"{fase} | {columna}"
                for columna in GRUPOS[grupo](df)
            ]
        )

    return columnas


def register_callbacks(app):
    @app.callback(
        Output("grupo-dropdown", "style"),
        Output("columnas-checklist", "style"),
        Input("modo-dropdown", "value"),
    )
    def mostrar_controles(modo):
        if modo == "grupo":
            return {"display": "block"}, {"display": "none"}
        return {"display": "none"}, {"display": "block"}

    @app.callback(
        Output("columnas-checklist", "options"),
        Output("correlacion-columnas-checklist", "options"),
        Input("fases-checklist", "value"),
        Input("freq-dropdown", "value"),
    )
    def actualizar_checklist(fases, freq):
        if not fases:
            return [], []

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        opciones = [{"label": c, "value": c} for c in df_combinado.columns]
        return opciones, opciones

    @app.callback(
        Output("grafico", "figure"),
        Input("fases-checklist", "value"),
        Input("freq-dropdown", "value"),
        Input("modo-dropdown", "value"),
        Input("grupo-dropdown", "value"),
        Input("normalizar-checklist", "value"),
        Input("columnas-checklist", "value"),
    )
    def actualizar_grafico(
        fases,
        freq,
        modo,
        grupo,
        normalizar_opciones,
        columnas_manual,
    ):
        if not fases:
            return go.Figure()

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        normalizar = "normalizar" in (normalizar_opciones or [])

        if modo == "grupo":
            columnas = obtener_columnas_por_grupo(dataframes, grupo)
        else:
            columnas = columnas_manual

        columnas = [c for c in columnas if c in df_combinado.columns]
        if not columnas:
            return go.Figure()

        fig = go.Figure()

        for col in columnas:
            y = df_combinado[col]
            if normalizar:
                y = normalizar_serie(y)

            fig.add_trace(
                go.Scatter(
                    x=df_combinado.index,
                    y=y,
                    mode="lines",
                    name=col,
                )
            )

        titulo = grupo if modo == "grupo" else "Seleccion manual"
        fig.update_layout(
            title=f"{', '.join(fases)} - {titulo}",
            hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
            ),
        )

        return fig

    @app.callback(
        Output("correlaciones-container", "children"),
        Input("fases-checklist", "value"),
        Input("freq-dropdown", "value"),
        Input("correlacion-columnas-checklist", "value"),
    )
    def actualizar_correlaciones(fases, freq, columnas_correlacion):
        if not fases or not columnas_correlacion:
            return []

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        correlacion_df = df_combinado.corr(numeric_only=True)

        tablas = []
        for columna in columnas_correlacion:
            if columna not in correlacion_df.columns:
                continue

            correlaciones = correlacion_df[columna].drop(labels=[columna]).dropna()
            correlaciones = correlaciones.sort_values(ascending=False)
            tablas.append(construir_tabla_correlacion(columna, correlaciones))

        return tablas

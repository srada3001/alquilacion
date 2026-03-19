from dash import Input, Output, html
import plotly.graph_objects as go

from dashboard_app.data import GRUPOS, aplicar_downsampling, cargar_df


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
        Input("fase-dropdown", "value"),
    )
    def actualizar_checklist(fase):
        if fase is None:
            return [], []

        df = cargar_df(fase)
        opciones = [{"label": c, "value": c} for c in df.columns]
        return opciones, opciones

    @app.callback(
        Output("grafico", "figure"),
        Input("fase-dropdown", "value"),
        Input("freq-dropdown", "value"),
        Input("modo-dropdown", "value"),
        Input("grupo-dropdown", "value"),
        Input("normalizar-checklist", "value"),
        Input("columnas-checklist", "value"),
    )
    def actualizar_grafico(
        fase,
        freq,
        modo,
        grupo,
        normalizar_opciones,
        columnas_manual,
    ):
        if fase is None:
            return go.Figure()

        df = cargar_df(fase)
        df = aplicar_downsampling(df, freq)
        normalizar = "normalizar" in (normalizar_opciones or [])

        if modo == "grupo":
            columnas = GRUPOS[grupo](df)
        else:
            columnas = columnas_manual

        columnas = [c for c in columnas if c in df.columns]
        if not columnas:
            return go.Figure()

        fig = go.Figure()

        for col in columnas:
            y = df[col]
            if normalizar:
                y = normalizar_serie(y)

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=y,
                    mode="lines",
                    name=col,
                )
            )

        fig.update_layout(
            title=f"{fase} - {grupo if modo == 'grupo' else 'Seleccion manual'}",
            hovermode="x unified",
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date",
            ),
        )

        return fig

    @app.callback(
        Output("correlaciones-container", "children"),
        Input("fase-dropdown", "value"),
        Input("freq-dropdown", "value"),
        Input("correlacion-columnas-checklist", "value"),
    )
    def actualizar_correlaciones(fase, freq, columnas_correlacion):
        if fase is None or not columnas_correlacion:
            return []

        df = cargar_df(fase)
        df = aplicar_downsampling(df, freq)
        correlacion_df = df.corr(numeric_only=True)

        tablas = []
        for columna in columnas_correlacion:
            if columna not in correlacion_df.columns:
                continue

            correlaciones = correlacion_df[columna].drop(labels=[columna]).dropna()
            correlaciones = correlaciones.sort_values(ascending=False)
            tablas.append(construir_tabla_correlacion(columna, correlaciones))

        return tablas

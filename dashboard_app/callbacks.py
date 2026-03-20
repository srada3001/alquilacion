from dash import Input, Output, html
import plotly.graph_objects as go

from dashboard_app.data import (
    GRUPOS,
    cargar_dataframes,
    combinar_dataframes_por_fase,
)

CHECKLIST_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "8px 16px",
}

FILTRO_CONTENEDOR_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "8px 16px",
    "alignItems": "end",
}


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


def aplicar_filtro(df, filtro_activo, columna, operador, valor):
    if "filtrar" not in (filtro_activo or []):
        return df
    if columna is None or operador is None or valor is None:
        return df
    if columna not in df.columns:
        return df

    serie = df[columna]
    if operador == ">":
        return df.loc[serie > valor]
    if operador == ">=":
        return df.loc[serie >= valor]
    if operador == "<":
        return df.loc[serie < valor]
    if operador == "<=":
        return df.loc[serie <= valor]
    return df


def register_callbacks(app):
    @app.callback(
        Output("grupo-dropdown", "style"),
        Output("columnas-checklist", "style"),
        Output("filtro-container", "style"),
        Input("modo-dropdown", "value"),
        Input("activar-filtro-checklist", "value"),
    )
    def mostrar_controles(modo, filtro_activo):
        filtro_style = FILTRO_CONTENEDOR_STYLE if "filtrar" in (filtro_activo or []) else {"display": "none"}
        if modo == "grupo":
            return {"display": "block"}, {"display": "none"}, filtro_style
        return {"display": "none"}, CHECKLIST_GRID_STYLE, filtro_style

    @app.callback(
        Output("columnas-checklist", "options"),
        Output("correlacion-columnas-checklist", "options"),
        Output("filtro-columna-dropdown", "options"),
        Input("fases-checklist", "value"),
        Input("freq-dropdown", "value"),
    )
    def actualizar_checklist(fases, freq):
        if not fases:
            return [], [], []

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        opciones = [{"label": c, "value": c} for c in df_combinado.columns]
        opciones_numericas = [
            {"label": c, "value": c}
            for c in df_combinado.select_dtypes(include="number").columns
        ]
        return opciones, opciones, opciones_numericas

    @app.callback(
        Output("grafico", "figure"),
        Input("fases-checklist", "value"),
        Input("freq-dropdown", "value"),
        Input("modo-dropdown", "value"),
        Input("grupo-dropdown", "value"),
        Input("normalizar-checklist", "value"),
        Input("activar-filtro-checklist", "value"),
        Input("filtro-columna-dropdown", "value"),
        Input("filtro-operador-dropdown", "value"),
        Input("filtro-valor-input", "value"),
        Input("columnas-checklist", "value"),
    )
    def actualizar_grafico(
        fases,
        freq,
        modo,
        grupo,
        normalizar_opciones,
        filtro_activo,
        filtro_columna,
        filtro_operador,
        filtro_valor,
        columnas_manual,
    ):
        if not fases:
            return go.Figure()

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        df_combinado = aplicar_filtro(
            df_combinado,
            filtro_activo,
            filtro_columna,
            filtro_operador,
            filtro_valor,
        )
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
        Input("activar-filtro-checklist", "value"),
        Input("filtro-columna-dropdown", "value"),
        Input("filtro-operador-dropdown", "value"),
        Input("filtro-valor-input", "value"),
        Input("correlacion-columnas-checklist", "value"),
    )
    def actualizar_correlaciones(
        fases,
        freq,
        filtro_activo,
        filtro_columna,
        filtro_operador,
        filtro_valor,
        columnas_correlacion,
    ):
        if not fases or not columnas_correlacion:
            return []

        dataframes = cargar_dataframes(fases, freq)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        df_combinado = aplicar_filtro(
            df_combinado,
            filtro_activo,
            filtro_columna,
            filtro_operador,
            filtro_valor,
        )
        correlacion_df = df_combinado.corr(numeric_only=True)

        tablas = []
        for columna in columnas_correlacion:
            if columna not in correlacion_df.columns:
                continue

            correlaciones = correlacion_df[columna].drop(labels=[columna]).dropna()
            correlaciones = correlaciones.sort_values(ascending=False)
            tablas.append(construir_tabla_correlacion(columna, correlaciones))

        return tablas

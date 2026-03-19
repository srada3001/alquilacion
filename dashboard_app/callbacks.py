from dash import Input, Output
import plotly.graph_objects as go

from dashboard_app.data import GRUPOS, aplicar_downsampling, cargar_df


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
        Input("fase-dropdown", "value"),
    )
    def actualizar_checklist(fase):
        if fase is None:
            return []

        df = cargar_df(fase)
        return [{"label": c, "value": c} for c in df.columns]

    @app.callback(
        Output("grafico", "figure"),
        Input("fase-dropdown", "value"),
        Input("freq-dropdown", "value"),
        Input("modo-dropdown", "value"),
        Input("grupo-dropdown", "value"),
        Input("columnas-checklist", "value"),
    )
    def actualizar_grafico(fase, freq, modo, grupo, columnas_manual):
        if fase is None:
            return go.Figure()

        df = cargar_df(fase)
        df = aplicar_downsampling(df, freq)

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
            y = (y - y.min()) / (y.max() - y.min())

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

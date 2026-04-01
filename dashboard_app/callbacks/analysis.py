from dash import Input, Output, State, dcc, html
import plotly.graph_objects as go

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.callbacks.common import (
    RESULTADOS_GRID_STYLE,
    construir_etiqueta_columna,
)
from dashboard_app.callbacks.filters import construir_mascara_global
from dashboard_app.data import obtener_columnas_numericas_dataset
from dashboard_app.domain.analysis import (
    calcular_influencias_para_variable,
    calcular_correlaciones_para_variable,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)


def construir_tabla_influencias(summary, etiquetar_columna, top_n=12):
    filas = [
        html.Tr(
            [
                html.Th("Variable"),
                html.Th("Lag"),
                html.Th("Corr"),
                html.Th("MI"),
                html.Th("TE"),
                html.Th("RF"),
                html.Th("Consenso"),
            ]
        )
    ]

    for row in summary.head(top_n).itertuples(index=False):
        filas.append(
            html.Tr(
                [
                    html.Td(etiquetar_columna(row.feature)),
                    html.Td(row.best_lag_label),
                    html.Td(f"{row.pearson:.4f}"),
                    html.Td(f"{getattr(row, 'mutual_information', 0.0) or 0.0:.4f}"),
                    html.Td(f"{getattr(row, 'transfer_entropy', 0.0) or 0.0:.4f}"),
                    html.Td(f"{getattr(row, 'importance_mean', 0.0) or 0.0:.4f}"),
                    html.Td(f"{row.consensus_score:.4f}"),
                ]
            )
        )

    return html.Div([html.H5("Influencias principales"), html.Table(filas)])


def construir_grafico_influencias(summary, etiquetar_columna, top_n=10):
    if summary is None or summary.empty:
        return html.Div("No hubo suficientes datos para calcular influencias.")

    top = summary.head(top_n).iloc[::-1]
    fig = go.Figure(
        data=[
            go.Bar(
                x=top["consensus_score"],
                y=[etiquetar_columna(valor) for valor in top["feature"]],
                orientation="h",
            )
        ]
    )
    fig.update_layout(
        title="Top influencias por consenso",
        margin=dict(l=20, r=20, t=40, b=20),
        height=360,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def construir_resumen_metricas(metrics):
    if not metrics:
        return html.Div("Random Forest no pudo entrenarse con suficientes datos.")

    filas = [
        html.Tr([html.Th("Metrica"), html.Th("Valor")]),
        html.Tr([html.Td("Filas train"), html.Td(str(metrics["train_rows"]))]),
        html.Tr([html.Td("Filas test"), html.Td(str(metrics["test_rows"]))]),
        html.Tr([html.Td("R2 test"), html.Td(f"{metrics['test_r2']:.4f}")]),
        html.Tr([html.Td("MAE test"), html.Td(f"{metrics['test_mae']:.4f}")]),
    ]
    return html.Div([html.H5("Metricas del modelo"), html.Table(filas)])


def construir_bloque_influencias(columna_objetivo, influence_result):
    summary = influence_result["summary"]
    metrics = influence_result["metrics"]

    return html.Div(
        [
            html.H5("Influence analysis", style={"marginTop": "20px"}),
            html.Div(
                [
                    construir_tabla_influencias(summary, construir_etiqueta_columna),
                    construir_resumen_metricas(metrics),
                    construir_grafico_influencias(summary, construir_etiqueta_columna),
                ],
                style=RESULTADOS_GRID_STYLE,
            ),
        ]
    )


def construir_bloque_resultado(columna_objetivo, correlaciones, serie_objetivo, influence_result):
    return html.Div(
        [
            html.H4(construir_etiqueta_columna(columna_objetivo)),
            html.Div(
                [
                    construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                    construir_tabla_describe(serie_objetivo.dropna()),
                    construir_histograma(serie_objetivo, columna_objetivo, construir_etiqueta_columna),
                ],
                style=RESULTADOS_GRID_STYLE,
            ),
            construir_bloque_influencias(columna_objetivo, influence_result),
        ],
        style={"marginBottom": "24px"},
    )


def register_analysis_callbacks(app):
    @app.callback(
        Output("correlacion-seleccion-checklist", "options"),
        Input("variables-seleccionadas-store", "data"),
    )
    def sincronizar_variables_correlacion(variables_seleccionadas):
        variables = list(variables_seleccionadas or [])
        return [
            {"label": construir_etiqueta_columna(columna), "value": columna}
            for columna in variables
        ]

    @app.callback(
        Output("correlaciones-container", "children", allow_duplicate=True),
        Input("calcular-correlaciones-btn", "n_clicks"),
        State("correlacion-seleccion-checklist", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_correlaciones(n_clicks, columnas_correlacion, filtros_guardados):
        if not n_clicks or not columnas_correlacion:
            return []

        freq = "1h"
        filtros_guardados = list(filtros_guardados or [])
        mascara_global = construir_mascara_global(freq, filtros_guardados)
        mascara_global_5m = construir_mascara_global("5min", filtros_guardados)
        df_influence_base = load_dataset_influence(mascara_global_5m, columnas_correlacion)
        resultados = []

        for columna in columnas_correlacion:
            correlaciones, serie_objetivo = calcular_correlaciones_para_variable(
                freq,
                columna,
                mascara_global,
            )
            influence_result = calcular_influencias_para_variable(df_influence_base, columna)
            resultados.append(construir_bloque_resultado(columna, correlaciones, serie_objetivo, influence_result))

        return resultados


def load_dataset_influence(mascara_global_5m, columnas_objetivo):
    columnas = obtener_columnas_numericas_dataset("5min")
    for columna_objetivo in columnas_objetivo:
        if columna_objetivo not in columnas:
            columnas.append(columna_objetivo)

    df = load_combined_dataset("5min", columns=columnas)
    if mascara_global_5m is not None:
        mascara = mascara_global_5m.reindex(df.index, fill_value=False)
        df = df.loc[mascara]
    return df

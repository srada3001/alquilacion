from dash import Input, Output, State, dcc, html
import plotly.graph_objects as go

from dashboard_app.callbacks.common import (
    construir_etiqueta_columna,
)
from dashboard_app.repositories.analysis_cache import (
    get_precomputed_analysis_columns,
    load_precomputed_analysis_result,
)


ANALISIS_PROFUNDO_STACK_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr)",
    "gap": "16px",
    "alignItems": "start",
}


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

    return html.Div([html.Table(filas)])


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
    return html.Div([html.Table(filas)])


def construir_bloque_analisis_profundo(influence_result):
    summary = influence_result["summary"]
    metrics = influence_result["metrics"]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Influencias principales"),
                            construir_tabla_influencias(summary, construir_etiqueta_columna),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Metricas del modelo"),
                            construir_resumen_metricas(metrics),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Top influencias por consenso"),
                            construir_grafico_influencias(summary, construir_etiqueta_columna),
                        ]
                    ),
                ],
                style=ANALISIS_PROFUNDO_STACK_STYLE,
            ),
        ]
    )


def construir_bloque_resultado_profundo(influence_result):
    return html.Div(
        [
            construir_bloque_analisis_profundo(influence_result),
        ],
        style={"marginBottom": "24px"},
    )


def register_deep_analysis_callbacks(app):
    @app.callback(
        Output("deep-analysis-container", "children", allow_duplicate=True),
        Input("deep-analysis-dropdown", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_analisis_profundo(columna_objetivo, filtros_guardados):
        if not columna_objetivo:
            return []

        filtros_guardados = list(filtros_guardados or [])
        if filtros_guardados:
            return [
                html.Div(
                    "El analisis profundo solo esta disponible sin filtros y para variables precomputadas."
                )
            ]

        if columna_objetivo not in get_precomputed_analysis_columns():
            return [
                html.Div(
                    "Selecciona una variable con analisis profundo precomputado."
                )
            ]

        cached = load_precomputed_analysis_result(columna_objetivo)
        if cached is None:
            return [
                html.Div(
                    "No se encontraron resultados precomputados para la variable seleccionada."
                )
            ]

        return [
            construir_bloque_resultado_profundo(
                cached["influence_result"],
            )
        ]

from dash import Input, Output, State, html

from dashboard_app.callbacks.analysis_views import construir_bloque_analisis_exploratorio
from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.callbacks.filters import construir_mascara_global
from dashboard_app.domain.analysis import calcular_correlaciones_para_variable


def construir_bloque_resultado(columna_objetivo, correlaciones, serie_objetivo):
    return html.Div(
        [
            html.H4(construir_etiqueta_columna(columna_objetivo)),
            construir_bloque_analisis_exploratorio(
                columna_objetivo,
                correlaciones,
                serie_objetivo,
            ),
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
        Output("analysis-container", "children", allow_duplicate=True),
        Input("calcular-analysis-btn", "n_clicks"),
        State("correlacion-seleccion-checklist", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_analisis(n_clicks, columnas_correlacion, filtros_guardados):
        if not n_clicks or not columnas_correlacion:
            return []

        mascara_global = construir_mascara_global("1h", list(filtros_guardados or []))
        resultados = []

        for columna in columnas_correlacion:
            correlaciones, serie_objetivo = calcular_correlaciones_para_variable(
                "1h",
                columna,
                mascara_global,
            )
            resultados.append(
                construir_bloque_resultado(
                    columna,
                    correlaciones,
                    serie_objetivo,
                )
            )

        return resultados

from dash import Input, Output, State, html

from dashboard_app.callbacks.common import (
    RESULTADOS_GRID_STYLE,
    construir_etiqueta_columna,
)
from dashboard_app.callbacks.filters import construir_mascara_global
from dashboard_app.domain.analysis import (
    calcular_correlaciones_para_variable,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)


def construir_bloque_resultado(columna_objetivo, correlaciones, serie_objetivo):
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
        resultados = []

        for columna in columnas_correlacion:
            correlaciones, serie_objetivo = calcular_correlaciones_para_variable(
                freq,
                columna,
                mascara_global,
            )
            resultados.append(construir_bloque_resultado(columna, correlaciones, serie_objetivo))

        return resultados

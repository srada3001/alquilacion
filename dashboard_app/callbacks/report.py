from dash import Input, Output, State, html

from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.callbacks.filters import construir_mascara_global
from dashboard_app.callbacks.report_views import construir_bloque_reporte
from dashboard_app.domain.report import calcular_correlaciones_para_variable


def construir_bloque_resultado(correlaciones, serie_objetivo, df_numerico):
    return html.Div(
        [
            construir_bloque_reporte(
                correlaciones,
                serie_objetivo,
                df_numerico,
            ),
        ],
        style={"marginBottom": "24px"},
    )


def register_report_callbacks(app):
    @app.callback(
        Output("report-variable-dropdown", "options"),
        Output("report-variable-dropdown", "value"),
        Input("variables-seleccionadas-store", "data"),
        State("report-variable-dropdown", "value"),
    )
    def sincronizar_variables_reporte(variables_seleccionadas, valor_actual):
        variables = list(variables_seleccionadas or [])
        opciones = [
            {"label": construir_etiqueta_columna(columna), "value": columna}
            for columna in variables
        ]
        valores_validos = {opcion["value"] for opcion in opciones}
        valor = valor_actual if valor_actual in valores_validos else None
        return opciones, valor

    @app.callback(
        Output("report-container", "children", allow_duplicate=True),
        Input("report-variable-dropdown", "value"),
        Input("filtros-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
        prevent_initial_call=True,
    )
    def actualizar_reporte(columna_reporte, filtros_guardados, modo_operacion, arranque_id, parada_id):
        if not columna_reporte:
            return []

        mascara_global = construir_mascara_global(
            "1h",
            filtros_guardados,
            columnas_base=[columna_reporte],
            modo_operacion=modo_operacion,
            arranque_id=arranque_id,
            parada_id=parada_id,
        )
        correlaciones, serie_objetivo, df_numerico = calcular_correlaciones_para_variable(
            "1h",
            columna_reporte,
            mascara_global,
        )
        return [
            construir_bloque_resultado(
                correlaciones,
                serie_objetivo,
                df_numerico,
            )
        ]

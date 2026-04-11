from dash import Input, Output, State, html

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.callbacks.common import (
    construir_etiqueta_columna,
    construir_opciones_variables_por_fase,
)
from dashboard_app.callbacks.filters import construir_mascara_global
from dashboard_app.callbacks.report_views import (
    construir_bloque_reporte,
    construir_bloque_relaciones_personalizadas,
)
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


def construir_bloque_relaciones_extra(correlaciones, columna_objetivo, df_numerico):
    return html.Div(
        [
            construir_bloque_relaciones_personalizadas(
                correlaciones,
                columna_objetivo,
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

    @app.callback(
        Output("selected-relationship-variable-dropdown", "options"),
        Output("selected-relationship-variable-dropdown", "value"),
        Input("selected-relationship-phase-dropdown", "value"),
        State("selected-relationship-variable-dropdown", "value"),
    )
    def actualizar_opciones_relacion_personalizada(fase, valor_actual):
        opciones = construir_opciones_variables_por_fase("1h", fase, incluir_grupos=False)
        valores_validos = {opcion["value"] for opcion in opciones}
        valor = valor_actual if valor_actual in valores_validos else None
        return opciones, valor

    @app.callback(
        Output("selected-relationships-container", "children"),
        Input("report-variable-dropdown", "value"),
        Input("selected-relationship-variable-dropdown", "value"),
        Input("filtros-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
    )
    def actualizar_relaciones_seleccionadas(
        columna_reporte,
        columna_relacion,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
    ):
        if not columna_reporte:
            return html.Div("Selecciona una variable objetivo en Reporte para ver relaciones personalizadas.")
        if not columna_relacion:
            return html.Div("Selecciona una variable de comparacion en esta seccion.")
        if columna_relacion == columna_reporte:
            return html.Div("Selecciona una variable distinta a la variable objetivo del reporte.")

        columnas_consulta = [columna_reporte, columna_relacion]
        mascara_global = construir_mascara_global(
            "1h",
            filtros_guardados,
            columnas_base=columnas_consulta,
            modo_operacion=modo_operacion,
            arranque_id=arranque_id,
            parada_id=parada_id,
        )

        df_numerico = load_combined_dataset("1h", columns=columnas_consulta)
        if df_numerico.empty or columna_reporte not in df_numerico.columns:
            return html.Div("No se pudieron cargar datos para las variables seleccionadas.")

        if mascara_global is not None:
            mascara = mascara_global.reindex(df_numerico.index, fill_value=False)
            df_numerico = df_numerico.loc[mascara]

        if df_numerico.empty:
            return html.Div("No hay datos disponibles con los filtros actuales para las variables seleccionadas.")

        serie_objetivo = df_numerico[columna_reporte]
        correlaciones = (
            df_numerico.corrwith(serie_objetivo)
            .dropna()
            .drop(labels=[columna_reporte], errors="ignore")
        )
        correlaciones = correlaciones.reindex([columna_relacion]).dropna()

        if correlaciones.empty:
            return html.Div("No se pudo calcular la relacion con la variable seleccionada.")

        return construir_bloque_relaciones_extra(
            correlaciones,
            columna_reporte,
            df_numerico,
        )

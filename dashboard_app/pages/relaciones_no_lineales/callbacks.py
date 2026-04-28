from dash import Input, Output, html

from dashboard_app.repositories.analysis_cache import (
    get_precomputed_analysis_columns,
    load_precomputed_analysis_result,
)
from dashboard_app.pages.relaciones_no_lineales.views import (
    construir_bloque_resultado_profundo,
)


def register_callbacks(app):
    @app.callback(
        Output("deep-analysis-container", "children", allow_duplicate=True),
        Input("deep-analysis-dropdown", "value"),
        Input("deep-analysis-context-dropdown", "value"),
        prevent_initial_call=True,
    )
    def actualizar_analisis_profundo(
        columna_objetivo,
        context_key,
    ):
        if not columna_objetivo:
            return []
        if not context_key:
            return [html.Div("Selecciona un contexto disponible para consultar el analisis profundo.")]

        if columna_objetivo not in get_precomputed_analysis_columns():
            return [
                html.Div(
                    "Selecciona una variable con analisis profundo precomputado."
                )
            ]

        cached = load_precomputed_analysis_result(columna_objetivo, context_key)
        if cached is None:
            return [
                html.Div(
                    "No se encontraron resultados precomputados para la variable seleccionada."
                )
            ]

        return [
            construir_bloque_resultado_profundo(
                cached,
            )
        ]

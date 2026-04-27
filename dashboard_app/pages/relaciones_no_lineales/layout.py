from dash import dcc, html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.shared import (
    APP_PAGE_STYLE,
    DESCRIPCION_SECCION_STYLE,
    construir_links_secundarios,
)
from dashboard_app.repositories.analysis_cache import (
    get_precomputed_analysis_columns,
    get_precomputed_analysis_contexts,
)

ANALISIS_PROFUNDO_SELECTORES_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(320px, 2fr) minmax(240px, 1fr)",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}


def build_page():
    contextos = get_precomputed_analysis_contexts()
    contexto_inicial = contextos[0]["key"] if contextos else None
    return html.Div(
        [
            construir_links_secundarios(),
            html.H1("Relaciones no lineales", style=TITULO_CENTRADO_STYLE),
            html.Div(
                "Analisis profundo precomputado para explorar relaciones no lineales entre variables.",
                style=DESCRIPCION_SECCION_STYLE,
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id="deep-analysis-dropdown",
                        options=[
                            {"label": columna, "value": columna}
                            for columna in get_precomputed_analysis_columns()
                        ],
                        value=None,
                        placeholder="Seleccionar variable objetivo",
                    ),
                    dcc.Dropdown(
                        id="deep-analysis-context-dropdown",
                        options=[
                            {"label": contexto["label"], "value": contexto["key"]}
                            for contexto in contextos
                        ],
                        value=contexto_inicial,
                        placeholder="Seleccionar contexto",
                    ),
                ],
                style=ANALISIS_PROFUNDO_SELECTORES_STYLE,
            ),
            html.Div(
                "Selecciona una variable precomputada y un contexto disponible para cargar el analisis profundo.",
                style={"marginBottom": "12px"},
            ),
            html.Div(id="deep-analysis-container"),
        ],
        style=APP_PAGE_STYLE,
    )

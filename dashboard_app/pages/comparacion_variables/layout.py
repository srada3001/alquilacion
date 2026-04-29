from dash import html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, DESCRIPCION_SECCION_STYLE, construir_links_secundarios
from dashboard_app.pages.variables_controls import build_shared_variable_controls

COMPARACION_VARIABLES_VIEWS_SCOPE = "comparacion_variables"


def build_page(fases):
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Comparacion de variables", style=TITULO_CENTRADO_STYLE),
            html.Div(
                "Selecciona variables en orden. Cada par consecutivo genera un bloque de comparacion debajo.",
                style=DESCRIPCION_SECCION_STYLE,
            ),
            *build_shared_variable_controls(fases, COMPARACION_VARIABLES_VIEWS_SCOPE),
            html.Div(id="pair-graphs-container"),
        ],
        style=APP_PAGE_STYLE,
    )

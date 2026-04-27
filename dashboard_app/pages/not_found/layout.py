from dash import html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, construir_link_boton


def build_page():
    return html.Div(
        [
            html.H1("Pagina no encontrada", style=TITULO_CENTRADO_STYLE),
            html.Div(
                [construir_link_boton("Volver al inicio", HOME_ROUTE)],
                style={"display": "flex", "justifyContent": "center"},
            ),
        ],
        style=APP_PAGE_STYLE,
    )

from dash import Input, Output, dcc, html

from dashboard_app.pages.comparacion_variables.layout import (
    build_page as build_comparacion_variables_page,
)
from dashboard_app.pages.home.layout import build_page as build_home_page
from dashboard_app.pages.not_found.layout import build_page as build_not_found_page
from dashboard_app.pages.relaciones_no_lineales.layout import (
    build_page as build_relaciones_no_lineales_page,
)
from dashboard_app.pages.routes import (
    COMPARACION_VARIABLES_ROUTE,
    HOME_ROUTE,
    RELACIONES_NO_LINEALES_ROUTE,
    SERIES_TEMPORALES_ROUTE,
)
from dashboard_app.pages.series_temporales.layout import build_page as build_series_temporales_page


def build_layout(_fases):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content"),
        ]
    )


def register_page_callback(app, fases):
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
    )
    def render_page(pathname):
        if pathname in (None, HOME_ROUTE):
            return build_home_page()
        if pathname == SERIES_TEMPORALES_ROUTE:
            return build_series_temporales_page(fases)
        if pathname == COMPARACION_VARIABLES_ROUTE:
            return build_comparacion_variables_page(fases)
        if pathname == RELACIONES_NO_LINEALES_ROUTE:
            return build_relaciones_no_lineales_page()
        return build_not_found_page()

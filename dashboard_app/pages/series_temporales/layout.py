from dash import dcc, html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, construir_links_secundarios
from dashboard_app.pages.variables_controls import build_shared_variable_controls

VISTAS_TEMPORALES_OPCIONES = [
    {"label": "Vista 1", "value": "vista_1"},
]


def build_page(fases):
    return html.Div(
        [
            construir_links_secundarios(
                [("Inicio", HOME_ROUTE)]
            ),
            html.Div(
                [
                    html.Div(
                        "Vistas temporales",
                        style={"fontWeight": "600", "marginBottom": "8px"},
                    ),
                    dcc.Dropdown(
                        id="vistas-temporales-dropdown",
                        options=VISTAS_TEMPORALES_OPCIONES,
                        value=None,
                        placeholder="Seleccionar vista temporal",
                        clearable=True,
                    ),
                ],
                style={"marginBottom": "16px"},
            ),
            *build_shared_variable_controls(fases),
            html.H1("Evolucion temporal", style=TITULO_CENTRADO_STYLE),
            html.Div(
                [
                    dcc.Checklist(
                        id="normalizar-checklist",
                        options=[{"label": "Normalizar variables", "value": "normalizar"}],
                        value=[],
                    ),
                ],
                style={"marginBottom": "12px"},
            ),
            dcc.Graph(id="grafico"),
            html.Div(
                [
                    html.H1("Reporte", style=TITULO_CENTRADO_STYLE),
                    dcc.Dropdown(
                        id="report-variable-dropdown",
                        options=[],
                        value=None,
                        placeholder="Seleccionar variable para reporte",
                    ),
                    html.Div(id="report-container"),
                ]
            ),
        ],
        style=APP_PAGE_STYLE,
    )

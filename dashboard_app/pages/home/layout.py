from dash import html

from dashboard_app.data import obtener_data_uri_imagen_planta
from dashboard_app.pages.routes import RELACIONES_NO_LINEALES_ROUTE, SERIES_TEMPORALES_ROUTE
from dashboard_app.pages.shared import (
    APP_PAGE_STYLE,
    ESTADO_IMAGEN_STYLE,
    HOME_TITLE_STYLE,
    IMAGEN_PREVIEW_STYLE,
    SECCION_IMAGEN_STYLE,
    construir_link_boton,
)

HOME_LAYOUT_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(320px, 3fr) minmax(240px, 2fr)",
    "gap": "24px",
    "alignItems": "center",
}

HOME_ACTIONS_STYLE = {
    "display": "grid",
    "gap": "16px",
    "alignContent": "center",
}


def construir_bloque_imagen_planta():
    planta_src = obtener_data_uri_imagen_planta()
    if planta_src:
        return html.Div(
            [
                html.Img(
                    src=planta_src,
                    alt="Planta de alquilacion",
                    style=IMAGEN_PREVIEW_STYLE,
                )
            ],
            style=SECCION_IMAGEN_STYLE,
        )
    return html.Div(
        "No se encontro la imagen principal de la planta.",
        style={**SECCION_IMAGEN_STYLE, **ESTADO_IMAGEN_STYLE},
    )


def build_page():
    return html.Div(
        [
            html.H1("Dashboard U-044", style=HOME_TITLE_STYLE),
            html.Div(
                [
                    construir_bloque_imagen_planta(),
                    html.Div(
                        [
                            construir_link_boton("Series temporales", SERIES_TEMPORALES_ROUTE),
                            construir_link_boton("Relaciones no lineales", RELACIONES_NO_LINEALES_ROUTE),
                        ],
                        style=HOME_ACTIONS_STYLE,
                    ),
                ],
                style=HOME_LAYOUT_STYLE,
            ),
        ],
        style=APP_PAGE_STYLE,
    )

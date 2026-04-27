from dash import dcc, html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE

from dashboard_app.pages.routes import HOME_ROUTE, SERIES_TEMPORALES_ROUTE

APP_PAGE_STYLE = {
    "maxWidth": "1440px",
    "margin": "0 auto",
    "padding": "24px",
}

HOME_TITLE_STYLE = {
    **TITULO_CENTRADO_STYLE,
    "marginBottom": "24px",
}

BUTTON_LINK_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "justifyContent": "center",
    "minHeight": "56px",
    "padding": "0 20px",
    "borderRadius": "8px",
    "backgroundColor": "#1f77b4",
    "color": "#ffffff",
    "fontWeight": "600",
    "textDecoration": "none",
    "textAlign": "center",
}

PAGE_LINKS_STYLE = {
    "display": "flex",
    "gap": "12px",
    "justifyContent": "flex-end",
    "flexWrap": "wrap",
    "marginBottom": "20px",
}

SECCION_IMAGEN_STYLE = {
    "marginBottom": "24px",
    "padding": "16px",
    "border": "1px solid #d9d9d9",
    "borderRadius": "12px",
    "backgroundColor": "#fafafa",
}

IMAGEN_PREVIEW_STYLE = {
    "display": "block",
    "width": "100%",
    "maxWidth": "540px",
    "height": "auto",
    "margin": "0 auto",
    "borderRadius": "10px",
    "boxShadow": "0 4px 14px rgba(0, 0, 0, 0.08)",
}

DESCRIPCION_SECCION_STYLE = {
    "textAlign": "center",
    "marginBottom": "16px",
    "color": "#555555",
}

ESTADO_IMAGEN_STYLE = {
    "textAlign": "center",
    "padding": "16px",
    "color": "#666666",
}


def construir_link_boton(texto, href):
    return dcc.Link(texto, href=href, style=BUTTON_LINK_STYLE)


def construir_links_secundarios():
    return html.Div(
        [
            construir_link_boton("Inicio", HOME_ROUTE),
            construir_link_boton("Series temporales", SERIES_TEMPORALES_ROUTE),
        ],
        style=PAGE_LINKS_STYLE,
    )

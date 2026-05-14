from dash import dcc, html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.indicator_utils import EMPTY_STATE_STYLE
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import (
    APP_PAGE_STYLE,
    construir_links_secundarios,
)
from dashboard_app.pages.variables_controls import (
    CONTENEDOR_IMAGEN_FASE_STYLE,
    SELECTORES_STYLE,
    construir_boton_agregar,
    construir_dropdown_fases,
    construir_placeholder_imagen_fase,
)
from dashboard_app.repositories.saved_views import load_saved_views

VISTAS_GUARDADAS_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(320px, 1fr) auto auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

EDITOR_VISTA_GUARDADA_VISIBLE_STYLE = {
    "display": "grid",
    "gap": "16px",
    "marginBottom": "24px",
    "padding": "20px",
    "border": "1px solid #d7e3f4",
    "borderRadius": "12px",
    "backgroundColor": "#f8fbff",
}

EDITOR_VISTA_GUARDADA_OCULTO_STYLE = {
    **EDITOR_VISTA_GUARDADA_VISIBLE_STYLE,
    "display": "none",
}

EDITOR_ENCABEZADO_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(220px, 360px) auto",
    "gap": "12px",
    "alignItems": "center",
}

ESTADO_VISTA_GUARDADA_STYLE = {
    "marginBottom": "16px",
    "color": "#555555",
}

SECCION_STYLE = {
    "marginTop": "24px",
}


def build_page(fases):
    vistas_guardadas = load_saved_views()
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Monitoreo por secciones", style=TITULO_CENTRADO_STYLE),
            html.Div(
                [
                    dcc.Dropdown(
                        id="monitoreo-vistas-dropdown",
                        options=[
                            {"label": vista["name"], "value": vista["name"]}
                            for vista in vistas_guardadas
                        ],
                        value=None,
                        placeholder="Seleccionar vista guardada",
                        clearable=True,
                    ),
                    html.Button("Crear nueva vista", id="monitoreo-crear-vista-btn", n_clicks=0),
                    html.Button("Eliminar vista", id="monitoreo-eliminar-vista-btn", n_clicks=0),
                ],
                style=VISTAS_GUARDADAS_STYLE,
            ),
            html.Div(id="monitoreo-vista-estado", style=ESTADO_VISTA_GUARDADA_STYLE),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Input(
                                id="monitoreo-vista-nombre-input",
                                type="text",
                                value="",
                                placeholder="Nombre de la vista",
                            ),
                            html.Button("Guardar", id="monitoreo-guardar-vista-btn", n_clicks=0),
                        ],
                        style=EDITOR_ENCABEZADO_STYLE,
                    ),
                    html.Div(
                        [
                            construir_dropdown_fases(
                                fases,
                                "monitoreo-fase-dropdown",
                                value=None,
                                multi=False,
                            ),
                            dcc.Dropdown(
                                id="monitoreo-variable-dropdown",
                                options=[],
                                value=None,
                                placeholder="Seleccionar variables",
                            ),
                            construir_boton_agregar("monitoreo-anadir-variable-btn"),
                        ],
                        style=SELECTORES_STYLE,
                    ),
                    html.Div(
                        [
                            html.Div(
                                id="monitoreo-fase-imagen-container",
                                children=construir_placeholder_imagen_fase(),
                            ),
                        ],
                        style=CONTENEDOR_IMAGEN_FASE_STYLE,
                    ),
                    html.Div(id="monitoreo-editor-variables-container"),
                ],
                id="monitoreo-editor-container",
                style=EDITOR_VISTA_GUARDADA_OCULTO_STYLE,
            ),
            html.Div(
                [
                    html.Div(
                        id="monitoreo-semaforos-container",
                    ),
                ],
                style=SECCION_STYLE,
            ),
            html.Div(
                [
                    dcc.Graph(id="monitoreo-grafico"),
                    html.Div(id="monitoreo-graficas-por-unidad"),
                ],
                style=SECCION_STYLE,
            ),
            dcc.Store(id="monitoreo-vistas-store", data=vistas_guardadas),
            dcc.Store(id="monitoreo-editor-store", data={"visible": False}),
            dcc.Store(id="monitoreo-editor-variables-store", data=[]),
        ],
        style=APP_PAGE_STYLE,
    )

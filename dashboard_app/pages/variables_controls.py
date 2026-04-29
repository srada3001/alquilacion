from dash import dcc, html

from dashboard_app.callbacks.common import (
    ACCION_AGREGAR_STYLE,
    ACCION_RETIRAR_STYLE,
    FILTRO_PERIODO_OPCIONES,
)
from dashboard_app.data import formatear_nombre_fase
from dashboard_app.pages.shared import ESTADO_IMAGEN_STYLE
from dashboard_app.repositories.saved_views import load_saved_views

SELECTORES_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(240px, 1fr) minmax(320px, 2fr) auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

FILTROS_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(320px, 2fr) minmax(160px, 1fr) minmax(160px, 1fr) auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

FILTROS_FECHA_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr) minmax(0, 1fr) auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

FILTRO_PERIODO_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(240px, 1fr) minmax(320px, 2fr)",
    "gap": "12px",
    "alignItems": "end",
    "marginBottom": "16px",
}

FILTRO_FECHA_CAMPO_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr) 120px",
    "gap": "8px",
    "alignItems": "center",
}

CONTENEDOR_IMAGEN_FASE_STYLE = {
    "marginBottom": "24px",
}

VISTAS_GUARDADAS_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(220px, 1fr) auto auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

EDITOR_VISTA_GUARDADA_STYLE = {
    "display": "none",
    "gridTemplateColumns": "minmax(220px, 360px) auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

ESTADO_VISTA_GUARDADA_STYLE = {
    "marginBottom": "16px",
    "color": "#555555",
}


def construir_boton_agregar(button_id):
    return html.Button("+", id=button_id, n_clicks=0, style=ACCION_AGREGAR_STYLE)


def construir_boton_eliminar(button_id):
    return html.Button("-", id=button_id, n_clicks=0, style=ACCION_RETIRAR_STYLE)


def construir_placeholder_imagen_fase():
    return html.Div(
        "Selecciona una fase para ver su plano de proceso aqui.",
        style=ESTADO_IMAGEN_STYLE,
    )


def build_shared_variable_controls(fases, views_scope):
    vistas_guardadas = load_saved_views(views_scope)
    return [
        html.Div(
            [
                dcc.Dropdown(
                    id="vistas-guardadas-dropdown",
                    options=[
                        {"label": vista["name"], "value": vista["name"]}
                        for vista in vistas_guardadas
                    ],
                    value=None,
                    placeholder="Seleccionar vista guardada",
                    clearable=True,
                ),
                construir_boton_agregar("mostrar-guardar-vista-btn"),
                construir_boton_eliminar("eliminar-vista-btn"),
            ],
            style=VISTAS_GUARDADAS_STYLE,
        ),
        html.Div(
            [
                dcc.Input(
                    id="nombre-vista-guardada-input",
                    type="text",
                    value="",
                    placeholder="Nombre de la vista",
                ),
                html.Button("Guardar vista", id="guardar-vista-btn", n_clicks=0),
            ],
            id="editor-vista-guardada-container",
            style=EDITOR_VISTA_GUARDADA_STYLE,
        ),
        html.Div(id="vista-guardada-estado", style=ESTADO_VISTA_GUARDADA_STYLE),
        html.Div(
            [
                dcc.Dropdown(
                    id="seleccion-fases-dropdown",
                    options=[{"label": formatear_nombre_fase(fase), "value": fase} for fase in fases],
                    value=None,
                    placeholder="Seleccionar fases",
                ),
                dcc.Dropdown(
                    id="seleccion-variables-dropdown",
                    options=[],
                    value=None,
                    placeholder="Seleccionar variables",
                ),
                construir_boton_agregar("anadir-variable-btn"),
            ],
            style=SELECTORES_STYLE,
        ),
        html.Div(
            [
                html.Div(
                    id="fase-imagen-container",
                    children=construir_placeholder_imagen_fase(),
                ),
            ],
            style=CONTENEDOR_IMAGEN_FASE_STYLE,
        ),
        dcc.Store(id="variables-seleccionadas-store", data=[]),
        html.Div(id="variables-seleccionadas-container"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Filtro por periodos", style={"fontWeight": "600", "marginBottom": "8px"}),
                        dcc.Dropdown(
                            id="filtro-periodo-tipo-dropdown",
                            options=FILTRO_PERIODO_OPCIONES,
                            value=None,
                            placeholder="Sin filtro de periodo",
                            clearable=True,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Div(
                            id="filtro-periodo-detalle-label",
                            style={"fontWeight": "600", "marginBottom": "8px", "display": "none"},
                        ),
                        dcc.Dropdown(
                            id="filtro-periodo-detalle-dropdown",
                            options=[],
                            value=None,
                            placeholder="Seleccionar periodo",
                            clearable=True,
                            style={"display": "none"},
                        ),
                    ]
                ),
            ],
            style=FILTRO_PERIODO_STYLE,
        ),
        html.Div(
            [
                html.Div(
                    "Fecha en particular",
                    id="filtro-periodo-fecha-titulo",
                    style={"fontWeight": "600", "marginBottom": "8px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.DatePickerSingle(
                                    id="filtro-fecha-inicio-input",
                                    date=None,
                                    display_format="YYYY-MM-DD",
                                    placeholder="Fecha inicio",
                                    clearable=True,
                                ),
                                dcc.Input(
                                    id="filtro-hora-inicio-input",
                                    type="text",
                                    value="00:00",
                                    placeholder="HH:MM",
                                ),
                            ],
                            style=FILTRO_FECHA_CAMPO_STYLE,
                        ),
                        html.Div(
                            [
                                dcc.DatePickerSingle(
                                    id="filtro-fecha-fin-input",
                                    date=None,
                                    display_format="YYYY-MM-DD",
                                    placeholder="Fecha fin",
                                    clearable=True,
                                ),
                                dcc.Input(
                                    id="filtro-hora-fin-input",
                                    type="text",
                                    value="23:59",
                                    placeholder="HH:MM",
                                ),
                            ],
                            style=FILTRO_FECHA_CAMPO_STYLE,
                        ),
                        construir_boton_agregar("anadir-filtro-fecha-btn"),
                    ],
                    style=FILTROS_FECHA_STYLE,
                ),
            ],
            id="filtro-periodo-fecha-container",
            style={"marginBottom": "16px", "display": "none"},
        ),
        html.Div(
            [
                html.Div(
                    "Filtros por variable",
                    style={"fontWeight": "600", "marginBottom": "8px"},
                ),
                html.Div(
                    [
                        dcc.Dropdown(id="filtro-variable-crear-dropdown", options=[], value=None, placeholder="Variable"),
                        dcc.Dropdown(
                            id="filtro-operador-crear-dropdown",
                            options=[
                                {"label": "Mayor que", "value": ">"},
                                {"label": "Mayor o igual que", "value": ">="},
                                {"label": "Menor que", "value": "<"},
                                {"label": "Menor o igual que", "value": "<="},
                            ],
                            value=">",
                            placeholder="Operador",
                        ),
                        dcc.Input(
                            id="filtro-valor-crear-input",
                            type="number",
                            placeholder="Valor del filtro",
                        ),
                        construir_boton_agregar("anadir-filtro-btn"),
                    ],
                    style=FILTROS_STYLE,
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        html.Div(id="filtros-variable-container"),
        html.Div(id="filtro-periodo-container"),
        html.Div(id="filtros-resumen"),
        dcc.Store(id="estado-grafico-store", data={"freq": "1h", "range": None}),
        dcc.Store(id="filtros-store", data={"variables": [], "periodo": None}),
        dcc.Store(id="vistas-guardadas-store", data=vistas_guardadas),
        dcc.Store(id="editor-vista-guardada-store", data={"visible": False}),
        dcc.Store(id="vistas-guardadas-scope-store", data=views_scope),
    ]

from dash import dcc, html

from dashboard_app.callbacks.common import (
    ACCION_AGREGAR_STYLE,
    MODO_OPERACION_OPCIONES,
    TITULO_CENTRADO_STYLE,
    construir_opciones_arranques,
    construir_opciones_operaciones,
    construir_opciones_paradas,
)
from dashboard_app.data import formatear_nombre_fase, obtener_data_uri_imagen_planta
from dashboard_app.repositories.analysis_cache import get_precomputed_analysis_columns

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

CONTEXTO_OPERACION_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(220px, auto) minmax(240px, 1fr) minmax(240px, 1fr) minmax(240px, 1fr)",
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


ANALISIS_SECTIONS_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 2fr) minmax(0, 1fr)",
    "gap": "24px",
    "alignItems": "start",
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

TITULO_SECCION_STYLE = {
    "fontSize": "24px",
    "fontWeight": "700",
    "textAlign": "center",
    "marginBottom": "12px",
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


def construir_boton_agregar(button_id):
    return html.Button("+", id=button_id, n_clicks=0, style=ACCION_AGREGAR_STYLE)


def construir_seccion_planta():
    planta_src = obtener_data_uri_imagen_planta()
    contenido = [html.Div("Dashboard para el análisis de datos Planta de Alquilación", style=TITULO_SECCION_STYLE)]
    if planta_src:
        contenido.append(
            html.Img(
                src=planta_src,
                alt="Planta de alquilación",
                style=IMAGEN_PREVIEW_STYLE,
            )
        )
    else:
        contenido.append(
            html.Div(
                "No se encontro la imagen principal de la planta.",
                style=ESTADO_IMAGEN_STYLE,
            )
        )
    return html.Div(contenido, style=SECCION_IMAGEN_STYLE)


def construir_placeholder_imagen_fase():
    return html.Div(
        "Selecciona una fase para ver su plano de proceso aqui.",
        style=ESTADO_IMAGEN_STYLE,
    )


def build_layout(fases):
    return html.Div(
        [
            construir_seccion_planta(),
            html.H1("Variables", style=TITULO_CENTRADO_STYLE),
            html.Div(
                [
                    html.Div(
                        id="fase-imagen-container",
                        children=construir_placeholder_imagen_fase(),
                    ),
                ],
                style=SECCION_IMAGEN_STYLE,
            ),
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
            dcc.Store(id="variables-seleccionadas-store", data=[]),
            html.Div(id="variables-seleccionadas-container"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Modo de datos", style={"fontWeight": "600", "marginBottom": "8px"}),
                            dcc.RadioItems(
                                id="modo-operacion-radio",
                                options=MODO_OPERACION_OPCIONES,
                                value="toda",
                                inline=True,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("Filtro por arranque", style={"fontWeight": "600", "marginBottom": "8px"}),
                            dcc.Dropdown(
                                id="filtro-arranque-dropdown",
                                options=construir_opciones_arranques(),
                                value=None,
                                placeholder="Seleccionar arranque",
                                clearable=True,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("Filtro por parada", style={"fontWeight": "600", "marginBottom": "8px"}),
                            dcc.Dropdown(
                                id="filtro-parada-dropdown",
                                options=construir_opciones_paradas(),
                                value=None,
                                placeholder="Seleccionar parada",
                                clearable=True,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("Filtro por operación", style={"fontWeight": "600", "marginBottom": "8px"}),
                            dcc.Dropdown(
                                id="filtro-operacion-dropdown",
                                options=construir_opciones_operaciones(),
                                value=None,
                                placeholder="Seleccionar operación",
                                clearable=True,
                            ),
                        ]
                    ),
                ],
                style=CONTEXTO_OPERACION_STYLE,
            ),
            html.Details(
                [
                    html.Summary(
                        "Filtros por variable",
                        style={"cursor": "pointer", "fontWeight": "600"},
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
                            html.Button("Anadir", id="anadir-filtro-btn", n_clicks=0),
                        ],
                        style=FILTROS_STYLE,
                    ),
                ],
                style={"marginBottom": "16px"},
            ),
            html.Div(id="filtros-variable-container"),
            html.Details(
                [
                    html.Summary(
                        "Filtros por fecha",
                        style={"cursor": "pointer", "fontWeight": "600"},
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
                style={"marginBottom": "16px"},
            ),
            html.Div(id="filtros-fecha-container"),
            html.Div(id="filtros-resumen"),
            dcc.Store(id="estado-grafico-store", data={"freq": "1h", "range": None}),
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
            dcc.Store(id="filtros-store", data={"variables": [], "fechas": []}),
            dcc.Graph(id="grafico"),
            html.Div(
                [
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
                    html.Div(
                        [
                            html.H1("Analisis profundo", style=TITULO_CENTRADO_STYLE),
                            dcc.Dropdown(
                                id="deep-analysis-dropdown",
                                options=[
                                    {"label": columna, "value": columna}
                                    for columna in get_precomputed_analysis_columns()
                                ],
                                value=None,
                                placeholder="Seleccionar analisis profundo precomputado",
                            ),
                            html.Div(
                                "Solo disponible para Operación completa, arranques y operaciones sin filtros extra.",
                                style={"marginBottom": "12px"},
                            ),
                            html.Div(id="deep-analysis-container"),
                        ]
                    ),
                ],
                style=ANALISIS_SECTIONS_STYLE,
            ),
            html.Div(
                [
                    html.H1("Relaciones personalizadas", style=TITULO_CENTRADO_STYLE),
                    html.Div(
                        "Usa la variable seleccionada en Reporte como objetivo y elige aqui una sola variable de comparacion.",
                        style={"marginBottom": "12px"},
                    ),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="selected-relationship-phase-dropdown",
                                options=[{"label": formatear_nombre_fase(fase), "value": fase} for fase in fases],
                                value=None,
                                placeholder="Seleccionar fase",
                            ),
                            dcc.Dropdown(
                                id="selected-relationship-variable-dropdown",
                                options=[],
                                value=None,
                                placeholder="Seleccionar variable de comparacion",
                            ),
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "minmax(240px, 1fr) minmax(320px, 2fr)",
                            "gap": "12px",
                            "alignItems": "center",
                            "marginBottom": "16px",
                        },
                    ),
                    html.Div(id="selected-relationships-container"),
                ],
                style={"marginTop": "24px"},
            ),
        ]
    )

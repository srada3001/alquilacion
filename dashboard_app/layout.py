from dash import dcc, html

from dashboard_app.data import formatear_nombre_fase

CHECKLIST_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "8px 16px",
}


CHECKLIST_LABEL_STYLE = {
    "display": "block",
}


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


RESULTADOS_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
}


def build_layout(fases):
    return html.Div(
        [
            html.H1("Alquilacion", style={"textAlign": "center"}),
            html.H2("Variables"),
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
                    html.Button("Anadir", id="anadir-variable-btn", n_clicks=0),
                ],
                style=SELECTORES_STYLE,
            ),
            dcc.Store(id="variables-seleccionadas-store", data=[]),
            html.Div(id="variables-seleccionadas-container"),
            dcc.Store(id="estado-grafico-store", data={"freq": "1h", "range": None}),
            html.H2("Evolucion temporal de variables"),
            html.Div(
                [
                    dcc.Checklist(
                        id="normalizar-checklist",
                        options=[{"label": "Normalizar variables", "value": "normalizar"}],
                        value=[],
                    ),
                    html.Details(
                        [
                            html.Summary("Filtros", style={"cursor": "pointer", "fontWeight": "600"}),
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
                            html.Div(id="filtros-container"),
                            html.Div(id="filtros-resumen"),
                        ]
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "12px",
                    "alignItems": "flex-start",
                    "marginBottom": "12px",
                },
            ),
            dcc.Store(id="filtros-store", data=[]),
            dcc.Graph(id="grafico"),
            html.H3("Relaciones lineales, descripcion, histograma e influencias"),
            dcc.Checklist(
                id="correlacion-seleccion-checklist",
                options=[],
                value=[],
                style=CHECKLIST_GRID_STYLE,
                labelStyle=CHECKLIST_LABEL_STYLE,
            ),
            html.Button("Calcular", id="calcular-correlaciones-btn", n_clicks=0),
            html.Div(id="correlaciones-container"),
        ]
    )

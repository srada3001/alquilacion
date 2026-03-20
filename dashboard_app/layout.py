from dash import dcc, html

from dashboard_app.data import GRUPOS


CHECKLIST_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "8px 16px",
}


CHECKLIST_LABEL_STYLE = {
    "display": "block",
}


FILTRO_CONTENEDOR_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "8px 16px",
    "alignItems": "end",
}


def build_layout(fases):
    return html.Div(
        [
            html.H1("Alquilacion", style={"textAlign": "center"}),
            dcc.Checklist(
                id="fases-checklist",
                options=[{"label": f, "value": f} for f in fases],
                value=fases[:1],
                style=CHECKLIST_GRID_STYLE,
                labelStyle=CHECKLIST_LABEL_STYLE,
            ),
            html.H2("Evolucion temporal de variables"),
            dcc.Checklist(
                id="normalizar-checklist",
                options=[{"label": "Normalizar variables", "value": "normalizar"}],
                value=[],
            ),
            dcc.Checklist(
                id="activar-filtro-checklist",
                options=[{"label": "Aplicar filtro", "value": "filtrar"}],
                value=[],
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id="filtro-columna-dropdown",
                        options=[],
                        value=None,
                        placeholder="Variable para filtrar",
                    ),
                    dcc.Dropdown(
                        id="filtro-operador-dropdown",
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
                        id="filtro-valor-input",
                        type="number",
                        placeholder="Valor del filtro",
                    ),
                ],
                id="filtro-container",
                style={"display": "none"},
            ),
            dcc.Dropdown(
                id="freq-dropdown",
                options=[
                    {"label": "5 minutos", "value": "5min"},
                    {"label": "1 hora", "value": "1h"},
                ],
                value="1h",
            ),
            dcc.Dropdown(
                id="modo-dropdown",
                options=[
                    {"label": "Por grupo", "value": "grupo"},
                    {"label": "Seleccion manual", "value": "manual"},
                ],
                value="grupo",
            ),
            dcc.Dropdown(
                id="grupo-dropdown",
                options=[{"label": k, "value": k} for k in GRUPOS.keys()],
                value="Temperatura",
            ),
            dcc.Checklist(
                id="columnas-checklist",
                options=[],
                value=[],
                style=CHECKLIST_GRID_STYLE,
                labelStyle=CHECKLIST_LABEL_STYLE,
            ),
            dcc.Graph(id="grafico"),
            html.H3("Relaciones lineales entre variables"),
            dcc.Checklist(
                id="correlacion-columnas-checklist",
                options=[],
                value=[],
                style=CHECKLIST_GRID_STYLE,
                labelStyle=CHECKLIST_LABEL_STYLE,
            ),
            html.Div(id="correlaciones-container"),
        ]
    )

from dash import dcc, html

from dashboard_app.data import GRUPOS


def build_layout(fases):
    return html.Div(
        [
            html.H2("Visualizacion de Variables de Proceso"),
            dcc.Checklist(
                id="fases-checklist",
                options=[{"label": f, "value": f} for f in fases],
                value=fases[:1],
            ),
            dcc.Dropdown(
                id="freq-dropdown",
                options=[
                    {"label": "1 minuto (sin downsample)", "value": "1m"},
                    {"label": "10 minutos", "value": "10min"},
                    {"label": "30 minutos", "value": "30min"},
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
                id="normalizar-checklist",
                options=[{"label": "Normalizar variables", "value": "normalizar"}],
                value=[],
            ),
            dcc.Checklist(
                id="columnas-checklist",
                options=[],
                value=[],
            ),
            dcc.Graph(id="grafico"),
            html.H3("Relaciones lineales entre variables"),
            dcc.Checklist(
                id="correlacion-columnas-checklist",
                options=[],
                value=[],
            ),
            html.Div(id="correlaciones-container"),
        ]
    )

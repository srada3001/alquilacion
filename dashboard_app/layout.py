from dash import dcc, html

from dashboard_app.data import GRUPOS


def build_layout(fases):
    return html.Div(
        [
            html.H2("Visualizacion de Variables de Proceso"),
            dcc.Dropdown(
                id="fase-dropdown",
                options=[{"label": f, "value": f} for f in fases],
                value=fases[0] if fases else None,
                placeholder="Selecciona una fase",
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
                id="columnas-checklist",
                options=[],
                value=[],
            ),
            dcc.Graph(id="grafico"),
        ]
    )

import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

from config import DATA_PATH, PROCESSED_DATA_FOLDER, get_processed_output_path

# =========================
# Grupos de variables
# =========================
GRUPOS = {
    "Temperatura": lambda df: [c for c in df.columns if c.startswith("TI")],
    "Flujo": lambda df: [c for c in df.columns if c.startswith("FI")],
    "Presión": lambda df: [c for c in df.columns if c.startswith("P")],
    "Oxígeno": lambda df: [c for c in df.columns if c.startswith("AI")],
}

# =========================
# Obtener fases y cargar data
# =========================
def obtener_fases():
    outputs_path = os.path.join(DATA_PATH, PROCESSED_DATA_FOLDER)
    if not os.path.isdir(outputs_path):
        return []

    fases = []
    for archivo in os.listdir(outputs_path):
        archivo_path = os.path.join(outputs_path, archivo)
        if not os.path.isfile(archivo_path) or not archivo.endswith(".parquet"):
            continue
        fases.append(os.path.splitext(archivo)[0])

    return sorted(fases)

def cargar_df(fase):
    carga_path = get_processed_output_path(fase)
    df = pd.read_parquet(carga_path)

    # Asegurar índice datetime
    df.index = pd.to_datetime(df.index)

    return df

# =========================
# Downsampling
# =========================
def aplicar_downsampling(df, freq):
    if freq == "1m":
        return df
    return df.resample(freq).mean()

# =========================
# App Dash
# =========================
app = dash.Dash(__name__)

fases = obtener_fases()

app.layout = html.Div([

    html.H2("Visualización de Variables de Proceso"),

    # =========================
    # Selección de fase
    # =========================
    dcc.Dropdown(
        id="fase-dropdown",
        options=[{"label": f, "value": f} for f in fases],
        value=fases[0] if fases else None,
        placeholder="Selecciona una fase"
    ),

    # =========================
    # Downsampling
    # =========================
    dcc.Dropdown(
        id="freq-dropdown",
        options=[
            {"label": "1 minuto (sin downsample)", "value": "1m"},
            {"label": "10 minutos", "value": "10min"},
            {"label": "30 minutos", "value": "30min"},
            {"label": "1 hora", "value": "1h"},
        ],
        value="1h"
    ),

    # =========================
    # Modo de selección
    # =========================
    dcc.Dropdown(
        id="modo-dropdown",
        options=[
            {"label": "Por grupo", "value": "grupo"},
            {"label": "Selección manual", "value": "manual"},
        ],
        value="grupo"
    ),

    # =========================
    # Selector de grupo
    # =========================
    dcc.Dropdown(
        id="grupo-dropdown",
        options=[{"label": k, "value": k} for k in GRUPOS.keys()],
        value="Temperatura"
    ),

    # =========================
    # Checklist de columnas
    # =========================
    dcc.Checklist(
        id="columnas-checklist",
        options=[],
        value=[]
    ),

    # =========================
    # Gráfico
    # =========================
    dcc.Graph(id="grafico")
])

# =========================
# Mostrar / ocultar controles
# =========================
@app.callback(
    Output("grupo-dropdown", "style"),
    Output("columnas-checklist", "style"),
    Input("modo-dropdown", "value"),
)
def mostrar_controles(modo):
    if modo == "grupo":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}

# =========================
# Llenar checklist dinámicamente
# =========================
@app.callback(
    Output("columnas-checklist", "options"),
    Input("fase-dropdown", "value"),
)
def actualizar_checklist(fase):
    if fase is None:
        return []

    df = cargar_df(fase)

    return [{"label": c, "value": c} for c in df.columns]

# =========================
# Callback principal
# =========================
@app.callback(
    Output("grafico", "figure"),
    Input("fase-dropdown", "value"),
    Input("freq-dropdown", "value"),
    Input("modo-dropdown", "value"),
    Input("grupo-dropdown", "value"),
    Input("columnas-checklist", "value"),
)
def actualizar_grafico(fase, freq, modo, grupo, columnas_manual):

    if fase is None:
        return go.Figure()

    df = cargar_df(fase)
    df = aplicar_downsampling(df, freq)

    # =========================
    # Selección de columnas
    # =========================
    if modo == "grupo":
        columnas = GRUPOS[grupo](df)
    else:
        columnas = columnas_manual

    # Filtrar columnas válidas
    columnas = [c for c in columnas if c in df.columns]

    if not columnas:
        return go.Figure()

    fig = go.Figure()

    for col in columnas:
        y = df[col]

        # Normalización
        y = (y - y.min()) / (y.max() - y.min())

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=y,
                mode="lines",
                name=col
            )
        )

    fig.update_layout(
        title=f"{fase} - {grupo if modo=='grupo' else 'Selección manual'}",
        hovermode="x unified",
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        )
    )

    return fig

# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(debug=True)

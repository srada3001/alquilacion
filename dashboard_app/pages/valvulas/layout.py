from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from config import get_metadata_path
from dashboard_app.data import formatear_nombre_fase
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, construir_links_secundarios
from dashboard_app.pages.variables_controls import (
    construir_selector_fases_activos,
    resolver_fases_activos_desde_registros,
)

VALVES_METADATA_PATH = Path(get_metadata_path("valvulas.csv"))

TABLE_WRAPPER_STYLE = {
    "overflowX": "auto",
}

TABLE_STYLE = {
    "width": "100%",
    "borderCollapse": "collapse",
    "backgroundColor": "#ffffff",
    "borderRadius": "12px",
    "overflow": "hidden",
    "boxShadow": "0 4px 14px rgba(0, 0, 0, 0.08)",
}

HEADER_CELL_STYLE = {
    "padding": "14px 16px",
    "textAlign": "left",
    "backgroundColor": "#1f77b4",
    "color": "#ffffff",
    "fontWeight": "700",
    "borderBottom": "1px solid #d7e3f4",
    "whiteSpace": "nowrap",
}

BODY_CELL_STYLE = {
    "padding": "12px 16px",
    "borderBottom": "1px solid #e8eef5",
    "whiteSpace": "nowrap",
    "verticalAlign": "middle",
}

GAUGE_CELL_STYLE = {
    **BODY_CELL_STYLE,
    "whiteSpace": "normal",
    "minWidth": "420px",
}

GAUGE_GRAPH_STYLE = {
    "height": "120px",
    "minWidth": "360px",
}

EMPTY_STATE_STYLE = {
    "padding": "24px",
    "textAlign": "center",
    "color": "#666666",
    "border": "1px dashed #cbd5e1",
    "borderRadius": "12px",
    "backgroundColor": "#f8fafc",
}

STATUS_STYLES = {
    "normal": {
        "backgroundColor": "#ffffff",
        "color": "#1f2937",
    },
    "advertencia": {
        "backgroundColor": "#fff7d6",
        "color": "#7a5d00",
    },
    "critico": {
        "backgroundColor": "#fde2e2",
        "color": "#8f1d1d",
    },
    "sin_datos": {
        "backgroundColor": "#f3f4f6",
        "color": "#6b7280",
    },
}

SEMANTIC_COLORS = {
    "critico": "#dc2626",
    "advertencia": "#d97706",
    "normal": "#16a34a",
    "texto": "#111827",
    "suave": "#cbd5e1",
}


def _formatear_numero(valor):
    if valor is None:
        return "-"
    try:
        if pd.isna(valor):
            return "-"
    except TypeError:
        return str(valor)

    numero = float(valor)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.2f}"


def _formatear_texto(valor, es_fase=False):
    if valor is None:
        return "-"
    try:
        if pd.isna(valor):
            return "-"
    except TypeError:
        pass

    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return "-"
    if es_fase:
        return formatear_nombre_fase(texto)
    return texto


def _calcular_estado_valvula(pressure, operating_pressure, max_pressure):
    if pd.isna(pressure) or pd.isna(operating_pressure) or pd.isna(max_pressure):
        return "sin_datos"
    if max_pressure <= operating_pressure:
        return "sin_datos"
    if pressure < operating_pressure or pressure > max_pressure:
        return "critico"

    amplitud = max_pressure - operating_pressure
    umbral_amarillo = operating_pressure + amplitud * 0.8
    umbral_rojo = operating_pressure + amplitud * 0.9
    if pressure < umbral_amarillo:
        return "normal"
    if pressure < umbral_rojo:
        return "advertencia"
    return "critico"


def _calcular_rango_grafico(registro):
    valores = [
        registro.get("pressure"),
        registro.get("operating_pressure"),
        registro.get("max_pressure"),
    ]
    valores = [float(valor) for valor in valores if not pd.isna(valor)]
    if not valores:
        return (0.0, 1.0)

    minimo = min(valores)
    maximo = max(valores)
    amplitud = maximo - minimo
    padding = amplitud * 0.1 if amplitud > 0 else max(abs(maximo) * 0.1, 1.0)
    return minimo - padding, maximo + padding


def _construir_grafico_valvula(registro):
    pressure = registro.get("pressure")
    operating_pressure = registro.get("operating_pressure")
    max_pressure = registro.get("max_pressure")

    if pd.isna(pressure) or pd.isna(operating_pressure) or pd.isna(max_pressure) or max_pressure <= operating_pressure:
        return html.Div("Sin datos suficientes para construir el indicador.", style={"color": "#6b7280"})

    amplitud = max_pressure - operating_pressure
    umbral_amarillo = operating_pressure + amplitud * 0.8
    umbral_rojo = operating_pressure + amplitud * 0.9
    figura = go.Figure()

    figura.add_shape(
        type="line",
        x0=operating_pressure,
        x1=max_pressure,
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["suave"], "width": 12},
        layer="below",
    )
    figura.add_shape(
        type="line",
        x0=operating_pressure,
        x1=umbral_amarillo,
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["normal"], "width": 12},
        layer="below",
    )
    figura.add_shape(
        type="line",
        x0=umbral_amarillo,
        x1=umbral_rojo,
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["advertencia"], "width": 12},
        layer="below",
    )
    figura.add_shape(
        type="line",
        x0=umbral_rojo,
        x1=max_pressure,
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["critico"], "width": 12},
        layer="below",
    )

    for valor in (operating_pressure, umbral_amarillo, umbral_rojo, max_pressure):
        figura.add_shape(
            type="line",
            x0=valor,
            x1=valor,
            y0=-0.2,
            y1=0.2,
            line={"color": "#ffffff", "width": 1},
            layer="below",
        )

    figura.add_trace(
        go.Scatter(
            x=[pressure],
            y=[0],
            mode="markers+text",
            text=[_formatear_numero(pressure)],
            textposition="top center",
            marker={
                "size": 12,
                "symbol": "diamond",
                "color": SEMANTIC_COLORS["texto"],
                "line": {"color": "#ffffff", "width": 1},
            },
            hovertemplate="Pressure: %{x:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    figura.add_annotation(
        x=umbral_amarillo,
        y=0.52,
        text="80%",
        showarrow=False,
        font={"size": 10, "color": SEMANTIC_COLORS["advertencia"]},
        xanchor="center",
    )
    figura.add_annotation(
        x=umbral_rojo,
        y=0.52,
        text="90%",
        showarrow=False,
        font={"size": 10, "color": SEMANTIC_COLORS["critico"]},
        xanchor="center",
    )

    rango_x = _calcular_rango_grafico(registro)
    figura.update_layout(
        margin={"l": 8, "r": 8, "t": 28, "b": 24},
        height=110,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "range": list(rango_x),
            "showgrid": False,
            "zeroline": False,
            "tickfont": {"size": 10},
        },
        yaxis={
            "range": [-0.6, 0.8],
            "visible": False,
        },
    )

    return dcc.Graph(
        figure=figura,
        config={"displayModeBar": False, "responsive": True},
        style=GAUGE_GRAPH_STYLE,
    )


def _construir_celda(texto, row_style):
    return html.Td(texto, style={**BODY_CELL_STYLE, **row_style})


def _construir_celda_grafico(grafico, row_style):
    return html.Td(grafico, style={**GAUGE_CELL_STYLE, **row_style})


def _construir_fila_valvula(registro):
    estado = registro.get("status", "normal")
    row_style = STATUS_STYLES.get(estado, STATUS_STYLES["normal"])
    return html.Tr(
        [
            _construir_celda(_formatear_texto(registro.get("fase"), es_fase=True), row_style),
            _construir_celda(_formatear_texto(registro.get("tag")), row_style),
            _construir_celda(_formatear_texto(registro.get("location")), row_style),
            _construir_celda(_formatear_texto(registro.get("pi_tag")), row_style),
            _construir_celda_grafico(_construir_grafico_valvula(registro), row_style),
        ]
    )


def cargar_valvulas():
    if not VALVES_METADATA_PATH.exists():
        return pd.DataFrame(
            columns=[
                "fase",
                "tag",
                "location",
                "pi_tag",
                "comments",
                "pressure",
                "operating_pressure",
                "max_pressure",
                "status",
            ]
        )

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            valvulas = pd.read_csv(VALVES_METADATA_PATH, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        valvulas = pd.read_csv(VALVES_METADATA_PATH)

    valvulas = valvulas.copy()
    columnas_requeridas = {
        "fase",
        "tag",
        "location",
        "pi_tag",
        "comments",
        "pressure",
        "operating_pressure",
        "max_pressure",
    }
    faltantes = columnas_requeridas.difference(valvulas.columns)
    if faltantes:
        raise ValueError(
            "El archivo de valvulas no contiene las columnas requeridas: "
            + ", ".join(sorted(faltantes))
        )

    valvulas["pressure"] = pd.to_numeric(valvulas["pressure"], errors="coerce")
    valvulas["operating_pressure"] = pd.to_numeric(valvulas["operating_pressure"], errors="coerce")
    valvulas["max_pressure"] = pd.to_numeric(valvulas["max_pressure"], errors="coerce")
    valvulas["status"] = valvulas.apply(
        lambda row: _calcular_estado_valvula(
            row["pressure"],
            row["operating_pressure"],
            row["max_pressure"],
        ),
        axis=1,
    )
    return valvulas.sort_values(["location", "tag"], kind="stable").reset_index(drop=True)


def construir_tabla_valvulas(valvulas=None):
    if valvulas is None:
        valvulas = cargar_valvulas()
    if valvulas.empty:
        return html.Div(
            "No hay valvulas configuradas en data/metadata/valvulas.csv.",
            style=EMPTY_STATE_STYLE,
        )

    encabezados = [
        "Fase",
        "Tag",
        "Location",
        "PI tag",
        "Indicador de presion",
    ]
    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(texto, style=HEADER_CELL_STYLE) for texto in encabezados])),
                html.Tbody(
                    [_construir_fila_valvula(registro) for registro in valvulas.to_dict("records")]
                ),
            ],
            style=TABLE_STYLE,
        ),
        style=TABLE_WRAPPER_STYLE,
    )


def build_page(fases):
    valvulas = cargar_valvulas()
    fases_disponibles = resolver_fases_activos_desde_registros(valvulas, fases)
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Valvulas", style=TITULO_CENTRADO_STYLE),
            construir_selector_fases_activos(
                fases_disponibles,
                "valvulas-fases-dropdown",
                value=[],
            ),
            html.Div(
                construir_tabla_valvulas(valvulas),
                id="valvulas-tabla-container",
            ),
        ],
        style=APP_PAGE_STYLE,
    )

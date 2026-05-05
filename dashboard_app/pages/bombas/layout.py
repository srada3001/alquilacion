from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from config import get_metadata_path
from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.data import formatear_nombre_fase
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, DESCRIPCION_SECCION_STYLE, construir_links_secundarios
from dashboard_app.pages.variables_controls import (
    construir_selector_fases_activos,
    resolver_fases_activos_desde_registros,
)

PUMPS_METADATA_PATH = Path(get_metadata_path("bombas.csv"))

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


def _normalizar_columnas_bombas(df):
    columnas_requeridas = {
        "fase",
        "tag",
        "fi_tag",
        "actual",
        "min ventana",
        "min guia",
        "max guia",
        "max ventana",
        "units",
    }
    faltantes = columnas_requeridas.difference(df.columns)
    if faltantes:
        raise ValueError(
            "El archivo de bombas no contiene las columnas requeridas: "
            + ", ".join(sorted(faltantes))
        )

    return df.rename(
        columns={
            "min ventana": "min_ventana",
            "min guia": "min_guia",
            "max guia": "max_guia",
            "max ventana": "max_ventana",
        }
    ).copy()


def _tiene_rangos_validos(registro):
    valores = [
        registro.get("min_ventana"),
        registro.get("min_guia"),
        registro.get("max_guia"),
        registro.get("max_ventana"),
    ]
    if any(pd.isna(valor) for valor in valores):
        return False
    return valores == sorted(valores)


def _calcular_estado_bomba(actual, min_ventana, min_guia, max_guia, max_ventana):
    registro = {
        "min_ventana": min_ventana,
        "min_guia": min_guia,
        "max_guia": max_guia,
        "max_ventana": max_ventana,
    }
    if pd.isna(actual) or not _tiene_rangos_validos(registro):
        return "sin_datos"

    if actual < min_ventana:
        return "critico"
    if actual < min_guia:
        return "advertencia"
    if actual <= max_guia:
        return "normal"
    if actual <= max_ventana:
        return "advertencia"
    return "critico"


def _calcular_rango_grafico(registro):
    valores = [
        registro.get("actual"),
        registro.get("min_ventana"),
        registro.get("min_guia"),
        registro.get("max_guia"),
        registro.get("max_ventana"),
    ]
    valores = [float(valor) for valor in valores if not pd.isna(valor)]
    if not valores:
        return (0.0, 1.0)

    minimo = min(valores)
    maximo = max(valores)
    amplitud = maximo - minimo
    padding = amplitud * 0.06 if amplitud > 0 else max(abs(maximo) * 0.1, 1.0)
    return minimo - padding, maximo + padding


def _construir_grafico_bomba(registro):
    if pd.isna(registro.get("actual")) or not _tiene_rangos_validos(registro):
        return html.Div("Sin datos suficientes para construir el indicador.", style={"color": "#6b7280"})

    figura = go.Figure()
    segmentos = [
        ("advertencia", registro["min_ventana"], registro["min_guia"]),
        ("normal", registro["min_guia"], registro["max_guia"]),
        ("advertencia", registro["max_guia"], registro["max_ventana"]),
    ]

    figura.add_shape(
        type="line",
        x0=registro["min_ventana"],
        x1=registro["max_ventana"],
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["suave"], "width": 12},
        layer="below",
    )

    for estado, inicio, fin in segmentos:
        if fin <= inicio:
            continue
        figura.add_shape(
            type="line",
            x0=inicio,
            x1=fin,
            y0=0,
            y1=0,
            line={"color": SEMANTIC_COLORS[estado], "width": 12},
            layer="below",
        )

    for limite in ("min_ventana", "min_guia", "max_guia", "max_ventana"):
        valor = registro[limite]
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
            x=[registro["actual"]],
            y=[0],
            mode="markers+text",
            text=[_formatear_numero(registro["actual"])],
            textposition="top center",
            marker={
                "size": 12,
                "symbol": "diamond",
                "color": SEMANTIC_COLORS["texto"],
                "line": {"color": "#ffffff", "width": 1},
            },
            hovertemplate="Actual: %{x:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    rango_x = _calcular_rango_grafico(registro)
    figura.update_layout(
        margin={"l": 8, "r": 8, "t": 28, "b": 32},
        height=110,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "range": list(rango_x),
            "title": {
                "text": _formatear_texto(registro.get("units")),
                "font": {"size": 11},
            },
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


def _construir_fila_bomba(registro):
    estado = registro.get("status", "normal")
    row_style = STATUS_STYLES.get(estado, STATUS_STYLES["normal"])
    return html.Tr(
        [
            _construir_celda(_formatear_texto(registro.get("fase"), es_fase=True), row_style),
            _construir_celda(_formatear_texto(registro.get("tag")), row_style),
            _construir_celda(_formatear_texto(registro.get("fi_tag")), row_style),
            _construir_celda_grafico(_construir_grafico_bomba(registro), row_style),
        ]
    )


def cargar_bombas():
    if not PUMPS_METADATA_PATH.exists():
        return pd.DataFrame(
            columns=[
                "fase",
                "tag",
                "fi_tag",
                "actual",
                "min_ventana",
                "min_guia",
                "max_guia",
                "max_ventana",
                "units",
                "comments",
            ]
        )

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            bombas = pd.read_csv(PUMPS_METADATA_PATH, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        bombas = pd.read_csv(PUMPS_METADATA_PATH)

    bombas = _normalizar_columnas_bombas(bombas)

    fase_parece_tag = bombas["fase"].astype(str).str.contains(r"^P-", na=False)
    tag_parece_fase = bombas["tag"].astype(str).str.contains(r"_", na=False)
    if fase_parece_tag.any() and tag_parece_fase.any():
        bombas[["fase", "tag"]] = bombas[["tag", "fase"]]

    for columna in (
        "actual",
        "min_ventana",
        "min_guia",
        "max_guia",
        "max_ventana",
    ):
        bombas[columna] = pd.to_numeric(bombas[columna], errors="coerce")

    bombas["status"] = bombas.apply(
        lambda row: _calcular_estado_bomba(
            row["actual"],
            row["min_ventana"],
            row["min_guia"],
            row["max_guia"],
            row["max_ventana"],
        ),
        axis=1,
    )
    return bombas.sort_values(["fase", "tag"], kind="stable").reset_index(drop=True)


def construir_tabla_bombas(bombas=None):
    if bombas is None:
        bombas = cargar_bombas()
    if bombas.empty:
        return html.Div(
            "No hay bombas configuradas en data/metadata/bombas.csv.",
            style=EMPTY_STATE_STYLE,
        )

    encabezados = [
        "Fase",
        "Tag",
        "FI tag",
        "Indicador de caudal",
    ]
    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(texto, style=HEADER_CELL_STYLE) for texto in encabezados])),
                html.Tbody(
                    [_construir_fila_bomba(registro) for registro in bombas.to_dict("records")]
                ),
            ],
            style=TABLE_STYLE,
        ),
        style=TABLE_WRAPPER_STYLE,
    )


def build_page(fases):
    bombas = cargar_bombas()
    fases_disponibles = resolver_fases_activos_desde_registros(bombas, fases)
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Bombas", style=TITULO_CENTRADO_STYLE),
            html.Div(
                "La tabla conserva fase, tag y fi_tag. A la derecha se muestra un indicador unidimensional del caudal actual con semaforo por rangos y la linea de rat guia.",
                style=DESCRIPCION_SECCION_STYLE,
            ),
            construir_selector_fases_activos(
                fases_disponibles,
                "bombas-fases-dropdown",
                value=[],
            ),
            html.Div(
                construir_tabla_bombas(bombas),
                id="bombas-tabla-container",
            ),
        ],
        style=APP_PAGE_STYLE,
    )

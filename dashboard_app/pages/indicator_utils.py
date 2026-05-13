from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go

from dashboard_app.data import formatear_nombre_fase

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


def leer_csv_con_codificaciones(path):
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def formatear_numero(valor):
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


def formatear_texto(valor, es_fase=False):
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


def calcular_rango_grafico(valores, padding_ratio=0.1):
    valores_numericos = [float(valor) for valor in valores if not pd.isna(valor)]
    if not valores_numericos:
        return (0.0, 1.0)

    minimo = min(valores_numericos)
    maximo = max(valores_numericos)
    amplitud = maximo - minimo
    padding = amplitud * padding_ratio if amplitud > 0 else max(abs(maximo) * 0.1, 1.0)
    return minimo - padding, maximo + padding


def construir_celda(texto, row_style):
    return html.Td(texto, style={**BODY_CELL_STYLE, **row_style})


def construir_celda_grafico(grafico, row_style):
    return html.Td(grafico, style={**GAUGE_CELL_STYLE, **row_style})


def construir_grafico_semaforo(
    actual,
    segmentos,
    limites,
    hover_label="Actual",
    unidad=None,
    padding_ratio=0.1,
    mostrar_zonas_rojas_externas=False,
    annotations=None,
    bottom_margin=24,
):
    if pd.isna(actual) or not segmentos:
        return html.Div(
            "Sin datos suficientes para construir el indicador.",
            style={"color": "#6b7280"},
        )

    limites_validos = [float(valor) for valor in limites if not pd.isna(valor)]
    if not limites_validos:
        return html.Div(
            "Sin datos suficientes para construir el indicador.",
            style={"color": "#6b7280"},
        )

    valores_rango = [actual, *limites_validos]
    rango_x = calcular_rango_grafico(valores_rango, padding_ratio=padding_ratio)
    inicio_total = min(limites_validos)
    fin_total = max(limites_validos)

    figura = go.Figure()
    figura.add_shape(
        type="line",
        x0=rango_x[0] if mostrar_zonas_rojas_externas else inicio_total,
        x1=rango_x[1] if mostrar_zonas_rojas_externas else fin_total,
        y0=0,
        y1=0,
        line={"color": SEMANTIC_COLORS["suave"], "width": 12},
        layer="below",
    )

    if mostrar_zonas_rojas_externas and rango_x[0] < inicio_total:
        figura.add_shape(
            type="line",
            x0=rango_x[0],
            x1=inicio_total,
            y0=0,
            y1=0,
            line={"color": SEMANTIC_COLORS["critico"], "width": 12},
            layer="below",
        )
    if mostrar_zonas_rojas_externas and fin_total < rango_x[1]:
        figura.add_shape(
            type="line",
            x0=fin_total,
            x1=rango_x[1],
            y0=0,
            y1=0,
            line={"color": SEMANTIC_COLORS["critico"], "width": 12},
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

    for valor in limites_validos:
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
            x=[actual],
            y=[0],
            mode="markers+text",
            text=[formatear_numero(actual)],
            textposition="top center",
            marker={
                "size": 12,
                "symbol": "diamond",
                "color": SEMANTIC_COLORS["texto"],
                "line": {"color": "#ffffff", "width": 1},
            },
            hovertemplate=f"{hover_label}: %{{x:.2f}}<extra></extra>",
            showlegend=False,
        )
    )

    for annotation in annotations or []:
        figura.add_annotation(
            x=annotation["x"],
            y=annotation.get("y", 0.52),
            text=annotation["text"],
            showarrow=False,
            font={
                "size": annotation.get("size", 10),
                "color": annotation.get("color", SEMANTIC_COLORS["texto"]),
            },
            xanchor=annotation.get("xanchor", "center"),
        )

    xaxis = {
        "range": list(rango_x),
        "showgrid": False,
        "zeroline": False,
        "tickfont": {"size": 10},
    }
    if unidad:
        xaxis["title"] = {
            "text": formatear_texto(unidad),
            "font": {"size": 11},
        }

    figura.update_layout(
        margin={"l": 8, "r": 8, "t": 28, "b": bottom_margin},
        height=110,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=xaxis,
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

from pathlib import Path
import unicodedata

import pandas as pd
from dash import html

from config import get_metadata_path
from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, DESCRIPCION_SECCION_STYLE, construir_links_secundarios

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
    "whiteSpace": "normal",
    "verticalAlign": "top",
    "color": "#1f2937",
}

EMPTY_STATE_STYLE = {
    "padding": "24px",
    "textAlign": "center",
    "color": "#666666",
    "border": "1px dashed #cbd5e1",
    "borderRadius": "12px",
    "backgroundColor": "#f8fafc",
}


def _remover_acentos(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(caracter)
    )


def _normalizar_texto(texto):
    limpio = _remover_acentos(texto).strip().lower()
    reemplazos = {
        "¢": "o",
        "›": "o",
    }
    for origen, destino in reemplazos.items():
        limpio = limpio.replace(origen, destino)
    return " ".join(limpio.split())


def _resolver_metadata_path():
    return Path(get_metadata_path("variables_criticas.csv"))


def _leer_csv_variables_criticas(path):
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _resolver_columna(columnas_normalizadas, aliases):
    for alias in aliases:
        if alias in columnas_normalizadas:
            return columnas_normalizadas[alias]
    raise ValueError(
        "No se encontraron las columnas requeridas para variables criticas: "
        + ", ".join(aliases)
    )


def cargar_variables_criticas():
    metadata_path = _resolver_metadata_path()
    if not metadata_path.exists():
        return pd.DataFrame(columns=["tag", "descripcion", "valor_medido", "maximo"])

    variables_criticas = _leer_csv_variables_criticas(metadata_path).copy()
    columnas_normalizadas = {
        _normalizar_texto(columna): columna for columna in variables_criticas.columns
    }

    columna_tag = _resolver_columna(columnas_normalizadas, ["tag"])
    columna_descripcion = _resolver_columna(columnas_normalizadas, ["descripcion", "description"])
    columna_valor_medido = _resolver_columna(
        columnas_normalizadas,
        ["meassured value", "measured value", "valor medido"],
    )
    columna_maximo = _resolver_columna(columnas_normalizadas, ["max", "maximo", "valor maximo"])

    resultado = pd.DataFrame(
        {
            "tag": variables_criticas[columna_tag],
            "descripcion": variables_criticas[columna_descripcion],
            "valor_medido": variables_criticas[columna_valor_medido],
            "maximo": variables_criticas[columna_maximo],
        }
    )
    return resultado.fillna("").reset_index(drop=True)


def _formatear_celda(valor):
    if valor is None:
        return "-"
    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return "-"
    return texto


def _construir_fila(registro):
    return html.Tr(
        [
            html.Td(_formatear_celda(registro.get("tag")), style=BODY_CELL_STYLE),
            html.Td(_formatear_celda(registro.get("descripcion")), style=BODY_CELL_STYLE),
            html.Td(_formatear_celda(registro.get("valor_medido")), style=BODY_CELL_STYLE),
            html.Td(_formatear_celda(registro.get("maximo")), style=BODY_CELL_STYLE),
        ]
    )


def construir_tabla_variables_criticas(variables_criticas=None):
    if variables_criticas is None:
        variables_criticas = cargar_variables_criticas()
    if variables_criticas.empty:
        return html.Div(
            "No hay variables criticas configuradas en data/metadata/variables_criticas.csv.",
            style=EMPTY_STATE_STYLE,
        )

    encabezados = [
        "TAG",
        "Descripcion",
        "Valor medido",
        "Max",
    ]
    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(texto, style=HEADER_CELL_STYLE) for texto in encabezados])),
                html.Tbody(
                    [_construir_fila(registro) for registro in variables_criticas.to_dict("records")]
                ),
            ],
            style=TABLE_STYLE,
        ),
        style=TABLE_WRAPPER_STYLE,
    )


def build_page():
    variables_criticas = cargar_variables_criticas()
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Variables criticas", style=TITULO_CENTRADO_STYLE),
            html.Div(
                "Por ahora el valor medido se toma directamente desde la tabla de metadata. Mas adelante podremos conectarlo a actualizacion en tiempo real.",
                style=DESCRIPCION_SECCION_STYLE,
            ),
            construir_tabla_variables_criticas(variables_criticas),
        ],
        style=APP_PAGE_STYLE,
    )

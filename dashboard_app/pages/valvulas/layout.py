from pathlib import Path

import pandas as pd
from dash import html

from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from config import get_metadata_path
from dashboard_app.pages.indicator_utils import (
    EMPTY_STATE_STYLE,
    HEADER_CELL_STYLE,
    STATUS_STYLES,
    TABLE_STYLE,
    TABLE_WRAPPER_STYLE,
    construir_celda,
    construir_celda_grafico,
    construir_grafico_semaforo,
    formatear_texto,
    leer_csv_con_codificaciones,
)
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.shared import APP_PAGE_STYLE, construir_links_secundarios
from dashboard_app.pages.variables_controls import (
    construir_selector_fases_activos,
    resolver_fases_activos_desde_registros,
)

VALVES_METADATA_PATH = Path(get_metadata_path("valvulas.csv"))


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


def _construir_grafico_valvula(registro):
    pressure = registro.get("pressure")
    operating_pressure = registro.get("operating_pressure")
    max_pressure = registro.get("max_pressure")

    if (
        pd.isna(pressure)
        or pd.isna(operating_pressure)
        or pd.isna(max_pressure)
        or max_pressure <= operating_pressure
    ):
        return html.Div(
            "Sin datos suficientes para construir el indicador.",
            style={"color": "#6b7280"},
        )

    amplitud = max_pressure - operating_pressure
    umbral_amarillo = operating_pressure + amplitud * 0.8
    umbral_rojo = operating_pressure + amplitud * 0.9
    return construir_grafico_semaforo(
        actual=pressure,
        segmentos=[
            ("normal", operating_pressure, umbral_amarillo),
            ("advertencia", umbral_amarillo, umbral_rojo),
            ("critico", umbral_rojo, max_pressure),
        ],
        limites=[operating_pressure, umbral_amarillo, umbral_rojo, max_pressure],
        hover_label="Pressure",
        annotations=[
            {"x": umbral_amarillo, "text": "80%", "color": "#d97706"},
            {"x": umbral_rojo, "text": "90%", "color": "#dc2626"},
        ],
    )


def _construir_fila_valvula(registro):
    estado = registro.get("status", "normal")
    row_style = STATUS_STYLES.get(estado, STATUS_STYLES["normal"])
    return html.Tr(
        [
            construir_celda(formatear_texto(registro.get("fase"), es_fase=True), row_style),
            construir_celda(formatear_texto(registro.get("tag")), row_style),
            construir_celda(formatear_texto(registro.get("location")), row_style),
            construir_celda(formatear_texto(registro.get("pi_tag")), row_style),
            construir_celda_grafico(_construir_grafico_valvula(registro), row_style),
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

    valvulas = leer_csv_con_codificaciones(VALVES_METADATA_PATH)

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

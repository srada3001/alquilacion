from pathlib import Path

import pandas as pd
from dash import html

from config import get_metadata_path
from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
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

PUMPS_METADATA_PATH = Path(get_metadata_path("bombas.csv"))


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


def _construir_grafico_bomba(registro):
    if pd.isna(registro.get("actual")) or not _tiene_rangos_validos(registro):
        return html.Div(
            "Sin datos suficientes para construir el indicador.",
            style={"color": "#6b7280"},
        )

    return construir_grafico_semaforo(
        actual=registro["actual"],
        segmentos=[
            ("advertencia", registro["min_ventana"], registro["min_guia"]),
            ("normal", registro["min_guia"], registro["max_guia"]),
            ("advertencia", registro["max_guia"], registro["max_ventana"]),
        ],
        limites=[
            registro["min_ventana"],
            registro["min_guia"],
            registro["max_guia"],
            registro["max_ventana"],
        ],
        hover_label="Actual",
        unidad=registro.get("units"),
        padding_ratio=0.06,
        mostrar_zonas_rojas_externas=True,
        bottom_margin=32,
    )


def _construir_fila_bomba(registro):
    estado = registro.get("status", "normal")
    row_style = STATUS_STYLES.get(estado, STATUS_STYLES["normal"])
    return html.Tr(
        [
            construir_celda(formatear_texto(registro.get("fase"), es_fase=True), row_style),
            construir_celda(formatear_texto(registro.get("tag")), row_style),
            construir_celda(formatear_texto(registro.get("fi_tag")), row_style),
            construir_celda_grafico(_construir_grafico_bomba(registro), row_style),
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

    bombas = leer_csv_con_codificaciones(PUMPS_METADATA_PATH)

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

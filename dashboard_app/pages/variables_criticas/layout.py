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

METADATA_PATH = Path(get_metadata_path("variables_criticas.csv"))
COLUMNAS = ["tag", "descripcion", "valor_medido", "minimo", "normal", "normal_sor", "normal_eor", "maximo"]


def _rangos(registro):
    minimo = registro["minimo"]
    normal = registro["normal"]
    normal_sor = registro["normal_sor"]
    normal_eor = registro["normal_eor"]
    maximo = registro["maximo"]

    if pd.isna(minimo) and pd.isna(normal) and pd.notna(normal_sor) and pd.notna(normal_eor) and pd.notna(maximo):
        if normal_sor < normal_eor < maximo:
            return [("normal", normal_sor, normal_eor), ("advertencia", normal_eor, maximo)], normal_sor, maximo

    if pd.notna(minimo) and pd.notna(normal) and pd.notna(maximo) and pd.isna(normal_sor) and pd.isna(normal_eor):
        if minimo < normal < maximo:
            return [
                ("advertencia", minimo, minimo + (normal - minimo) * 0.2),
                ("normal", minimo + (normal - minimo) * 0.2, maximo - (maximo - normal) * 0.2),
                ("advertencia", maximo - (maximo - normal) * 0.2, maximo),
            ], minimo, maximo

    if pd.isna(minimo) and pd.notna(normal) and pd.notna(maximo) and pd.isna(normal_sor) and pd.isna(normal_eor):
        if normal < maximo:
            return [("normal", normal, maximo - (maximo - normal) * 0.2), ("advertencia", maximo - (maximo - normal) * 0.2, maximo)], normal, maximo

    return None, None, None


def _estado(registro):
    segmentos, limite_inferior, limite_superior = _rangos(registro)
    valor = registro["valor_medido"]
    if pd.isna(valor) or not segmentos:
        return "sin_datos"
    if valor < limite_inferior or valor > limite_superior:
        return "critico"
    return next((estado for estado, inicio, fin in segmentos if inicio <= valor <= fin), "sin_datos")


def cargar_variables_criticas():
    if not METADATA_PATH.exists():
        return pd.DataFrame(columns=[*COLUMNAS, "status"])

    df = leer_csv_con_codificaciones(METADATA_PATH)
    resultado = df.rename(
        columns={
            "TAG": "tag",
            "Descripción": "descripcion",
            "Valor medido": "valor_medido",
            "Mínimo": "minimo",
            "Normal": "normal",
            "Normal SOR": "normal_sor",
            "Normal EOR": "normal_eor",
            "Máximo": "maximo",
        }
    )

    faltantes = {"tag", "descripcion", "valor_medido", "maximo"}.difference(resultado.columns)
    if faltantes:
        raise ValueError(
            "El archivo de variables criticas no contiene las columnas requeridas: "
            + ", ".join(sorted(faltantes))
        )

    resultado = resultado.reindex(columns=COLUMNAS)
    for columna in COLUMNAS[2:]:
        resultado[columna] = pd.to_numeric(resultado[columna], errors="coerce")
    resultado["status"] = resultado.apply(_estado, axis=1)
    return resultado.reset_index(drop=True)


def _grafico(registro):
    segmentos, _, _ = _rangos(registro)
    if not segmentos:
        return html.Div("Sin datos suficientes para construir el indicador.", style={"color": "#6b7280"})
    limites = [inicio for _, inicio, _ in segmentos] + [segmentos[-1][2]]
    return construir_grafico_semaforo(
        actual=registro["valor_medido"],
        segmentos=segmentos,
        limites=limites,
        hover_label="Valor medido",
        padding_ratio=0.08,
        mostrar_zonas_rojas_externas=True,
    )


def construir_tabla_variables_criticas(variables_criticas=None):
    variables_criticas = cargar_variables_criticas() if variables_criticas is None else variables_criticas
    if variables_criticas.empty:
        return html.Div(
            "No hay variables criticas configuradas en data/metadata/variables_criticas.csv.",
            style=EMPTY_STATE_STYLE,
        )

    filas = []
    for registro in variables_criticas.to_dict("records"):
        row_style = STATUS_STYLES.get(registro["status"], STATUS_STYLES["normal"])
        filas.append(
            html.Tr(
                [
                    construir_celda(formatear_texto(registro["tag"]), row_style),
                    construir_celda(formatear_texto(registro["descripcion"]), row_style),
                    construir_celda_grafico(_grafico(registro), row_style),
                ]
            )
        )

    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(texto, style=HEADER_CELL_STYLE) for texto in ("TAG", "Descripción", "Indicador")])),
                html.Tbody(filas),
            ],
            style=TABLE_STYLE,
        ),
        style=TABLE_WRAPPER_STYLE,
    )


def build_page():
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Variables críticas", style=TITULO_CENTRADO_STYLE),
            construir_tabla_variables_criticas(),
        ],
        style=APP_PAGE_STYLE,
    )

import pandas as pd
from dash import html

from analysis_core.dataset_catalog import obtener_columnas_dataset
from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.callbacks.common import TITULO_CENTRADO_STYLE
from dashboard_app.pages.indicator_utils import EMPTY_STATE_STYLE
from dashboard_app.pages.monitoreo_por_secciones.domain import (
    MONITOREO_FREQ,
    describir_rango_monitoreo,
    obtener_rango_monitoreo_serializado,
)
from dashboard_app.pages.routes import HOME_ROUTE
from dashboard_app.pages.semaforos import construir_tabla_semaforos
from dashboard_app.pages.shared import (
    APP_PAGE_STYLE,
    DESCRIPCION_SECCION_STYLE,
    construir_links_secundarios,
)
from dashboard_app.repositories.lab_views import load_lab_views


SECCION_LABORATORIO_STYLE = {
    "marginTop": "28px",
    "paddingTop": "20px",
    "borderTop": "1px solid #d7e3f4",
}

SECCION_TITULO_STYLE = {
    "margin": "0 0 12px",
    "fontSize": "22px",
    "lineHeight": "1.25",
}


def obtener_columnas_vistas(vistas):
    columnas = []
    for vista in vistas:
        for variable in vista.get("variables") or []:
            columna = variable.get("column")
            if columna:
                columnas.append(columna)
    return list(dict.fromkeys(columnas))


def cargar_dataframe_laboratorio(vistas, columnas_disponibles):
    columnas_vistas = obtener_columnas_vistas(vistas)
    columnas_presentes = [
        columna
        for columna in columnas_vistas
        if columna in columnas_disponibles
    ]
    if not columnas_presentes:
        return pd.DataFrame()

    return load_combined_dataset(
        MONITOREO_FREQ,
        columns=columnas_presentes,
        time_range=obtener_rango_monitoreo_serializado(),
    )


def construir_seccion_laboratorio(vista, dataframe, columnas_disponibles):
    semaforos = construir_tabla_semaforos(vista, dataframe, columnas_disponibles)
    semaforos_lista = semaforos if isinstance(semaforos, list) else [semaforos]
    return html.Section(
        [
            html.H2(vista["name"], style=SECCION_TITULO_STYLE),
            *semaforos_lista,
        ],
        style=SECCION_LABORATORIO_STYLE,
    )


def build_page():
    vistas_laboratorio = load_lab_views()
    if not vistas_laboratorio:
        contenido = html.Div(
            "No hay vistas de laboratorio configuradas.",
            style=EMPTY_STATE_STYLE,
        )
    else:
        columnas_disponibles = set(obtener_columnas_dataset(MONITOREO_FREQ))
        dataframe = cargar_dataframe_laboratorio(vistas_laboratorio, columnas_disponibles)
        contenido = [
            construir_seccion_laboratorio(vista, dataframe, columnas_disponibles)
            for vista in vistas_laboratorio
        ]

    contenido_lista = contenido if isinstance(contenido, list) else [contenido]
    return html.Div(
        [
            construir_links_secundarios([("Inicio", HOME_ROUTE)]),
            html.H1("Laboratorio", style=TITULO_CENTRADO_STYLE),
            html.Div(
                f"Semaforos evaluados con datos del {describir_rango_monitoreo()}.",
                style=DESCRIPCION_SECCION_STYLE,
            ),
            *contenido_lista,
        ],
        style=APP_PAGE_STYLE,
    )

from dash import html

from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.domain.analysis import (
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)

ANALISIS_EXPLORATORIO_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
}

CORRELACIONES_EXPANDIDAS_STYLE = {
    "gridColumn": "1 / -1",
}


def construir_bloque_analisis_exploratorio(
    columna_objetivo,
    correlaciones,
    serie_objetivo,
):
    return html.Div(
        [
            html.H5("Analisis exploratorio"),
            html.Div(
                [
                    construir_tabla_describe(serie_objetivo.dropna()),
                    construir_histograma(serie_objetivo, columna_objetivo, construir_etiqueta_columna),
                    html.Div(
                        construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                        style=CORRELACIONES_EXPANDIDAS_STYLE,
                    ),
                ],
                style=ANALISIS_EXPLORATORIO_GRID_STYLE,
            ),
        ]
    )

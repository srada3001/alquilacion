from dash import html

from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.domain.report import (
    construir_bloque_dispersiones,
    construir_boxplot_relaciones,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)

REPORTE_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
}

CORRELACIONES_EXPANDIDAS_STYLE = {
    "gridColumn": "1 / -1",
}


def construir_bloque_reporte(
    correlaciones,
    serie_objetivo,
    df_numerico,
):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Descripcion estadistica"),
                            construir_tabla_describe(serie_objetivo.dropna()),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Histograma"),
                            construir_histograma(serie_objetivo, serie_objetivo.name, construir_etiqueta_columna),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Boxplot comparativo"),
                            construir_boxplot_relaciones(
                                df_numerico,
                                serie_objetivo.name,
                                correlaciones,
                                construir_etiqueta_columna,
                            ),
                        ],
                        style=CORRELACIONES_EXPANDIDAS_STYLE,
                    ),
                    html.Div(
                        [
                            html.H2("Correlaciones lineales"),
                            construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                        ],
                        style=CORRELACIONES_EXPANDIDAS_STYLE,
                    ),
                    html.Div(
                        [
                            html.H2("Relaciones principales"),
                            construir_bloque_dispersiones(
                                df_numerico,
                                serie_objetivo.name,
                                correlaciones,
                                construir_etiqueta_columna,
                            ),
                        ],
                        style=CORRELACIONES_EXPANDIDAS_STYLE,
                    ),
                ],
                style=REPORTE_GRID_STYLE,
            ),
        ]
    )

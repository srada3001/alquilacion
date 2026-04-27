from dash import html

from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.domain.report import (
    construir_boxplot_relacion,
    construir_grafico_dispersion,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
    obtener_top_variables_correlacion,
)

REPORTE_RESUMEN_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
    "marginBottom": "24px",
}

CORRELACIONES_EXPANDIDAS_STYLE = {
    "gridColumn": "1 / -1",
}

RELACIONES_STACK_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr)",
    "gap": "16px",
}

RELACION_FILA_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 2fr) minmax(320px, 1fr)",
    "gap": "16px",
    "alignItems": "start",
}

RELACION_TITULO_STYLE = {
    "gridColumn": "1 / -1",
}


def construir_fila_relacion(
    df_numerico,
    columna_objetivo,
    columna_relacion,
    valor_correlacion,
):
    return html.Div(
        [
            html.H3(
                f"{construir_etiqueta_columna(columna_relacion)} (r={valor_correlacion:.4f})",
                style=RELACION_TITULO_STYLE,
            ),
            html.Div(
                [
                    html.H4("Variable vs variable"),
                    construir_grafico_dispersion(
                        df_numerico,
                        columna_objetivo,
                        columna_relacion,
                        construir_etiqueta_columna,
                    ),
                ]
            ),
            html.Div(
                [
                    html.H4("Boxplot comparativo"),
                    construir_boxplot_relacion(
                        df_numerico,
                        columna_objetivo,
                        columna_relacion,
                        construir_etiqueta_columna,
                    ),
                ]
            ),
        ],
        style=RELACION_FILA_STYLE,
    )


def construir_bloque_relaciones_principales(
    correlaciones,
    columna_objetivo,
    df_numerico,
    top_n=4,
):
    top_variables = obtener_top_variables_correlacion(correlaciones, top_n=top_n)
    if not top_variables:
        return html.Div("No hay suficientes correlaciones para mostrar relaciones principales.")

    return html.Div(
        [
            construir_fila_relacion(
                df_numerico,
                columna_objetivo,
                variable,
                correlaciones[variable],
            )
            for variable in top_variables
        ],
        style=RELACIONES_STACK_STYLE,
    )


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
                            html.H2("Correlaciones lineales"),
                            construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                        ],
                        style=CORRELACIONES_EXPANDIDAS_STYLE,
                    ),
                ],
                style=REPORTE_RESUMEN_STYLE,
            ),
            html.Div(
                [
                    html.H2("Relaciones principales"),
                    construir_bloque_relaciones_principales(
                        correlaciones,
                        serie_objetivo.name,
                        df_numerico,
                    ),
                ]
            ),
        ]
    )


def construir_bloque_relaciones_personalizadas(
    correlacion,
    columna_objetivo,
    df_numerico,
):
    if correlacion is None:
        return html.Div("No hay suficientes datos para mostrar la relacion seleccionada.")

    top_variables = obtener_top_variables_correlacion(correlacion, top_n=1)
    if not top_variables:
        return html.Div("No hay suficientes datos para mostrar la relacion seleccionada.")

    variable = top_variables[0]
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Relaciones seleccionadas"),
                    construir_fila_relacion(
                        df_numerico,
                        columna_objetivo,
                        variable,
                        correlacion[variable],
                    ),
                ],
                style=CORRELACIONES_EXPANDIDAS_STYLE,
            ),
        ],
    )

from dash import html

from dashboard_app.callbacks.common import (
    ACCION_RETIRAR_STYLE,
    BADGE_CONTAINER_STYLE,
    BADGE_STYLE,
    construir_etiqueta_columna,
    formatear_timestamp_corto,
)
from dashboard_app.data import formatear_nombre_fase, obtener_data_uri_imagen_fase
from dashboard_app.domain.operation_events import obtener_eventos_operacion, obtener_operaciones
from dashboard_app.pages.series_temporales.domain import (
    construir_boxplot_relacion,
    construir_grafico_dispersion,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)

IMAGEN_FASE_STYLE = {
    "display": "block",
    "width": "100%",
    "maxWidth": "1080px",
    "height": "auto",
    "margin": "0 auto",
    "borderRadius": "10px",
    "boxShadow": "0 4px 14px rgba(0, 0, 0, 0.08)",
}

ESTADO_IMAGEN_STYLE = {
    "textAlign": "center",
    "padding": "16px",
    "color": "#666666",
}

DESCRIPCION_IMAGEN_STYLE = {
    "textAlign": "center",
    "marginTop": "12px",
    "color": "#555555",
}

REPORTE_RESUMEN_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
    "marginBottom": "24px",
}

REPORTE_HISTOGRAMA_STYLE = {
    "gridColumn": "2 / 4",
}

REPORTE_CORRELACIONES_STYLE = {
    "gridColumn": "1 / -1",
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


def construir_chip_variable(variable):
    return html.Div(
        [
            html.Span(construir_etiqueta_columna(variable)),
            html.Button(
                "-",
                id={"type": "retirar-variable-btn", "value": variable},
                n_clicks=0,
                style=ACCION_RETIRAR_STYLE,
            ),
        ],
        style=BADGE_STYLE,
    )


def construir_imagen_fase(fase):
    if not fase:
        return html.Div(
            "Selecciona una fase para ver su plano de proceso aqui.",
            style=ESTADO_IMAGEN_STYLE,
        )

    image_src = obtener_data_uri_imagen_fase(fase)
    if not image_src:
        return html.Div(
            f"No se encontro una imagen para la fase {formatear_nombre_fase(fase)}.",
            style=ESTADO_IMAGEN_STYLE,
        )

    etiqueta_fase = formatear_nombre_fase(fase)
    return html.Div(
        [
            html.Img(
                src=image_src,
                alt=f"Plano de proceso de {etiqueta_fase}",
                style=IMAGEN_FASE_STYLE,
            ),
            html.Div(
                f"Plano de proceso de {etiqueta_fase}. Usa esta vista para ubicar los tags antes de elegir la variable.",
                style=DESCRIPCION_IMAGEN_STYLE,
            ),
        ]
    )


def construir_chip_filtro_variable(filtro):
    texto = f"{construir_etiqueta_columna(filtro['columna'])} {filtro['operador']} {filtro['valor']}"
    return html.Div(
        [
            html.Span(texto),
            html.Button(
                "Eliminar",
                id={"type": "retirar-filtro-variable-btn", "value": filtro["id"]},
                n_clicks=0,
            ),
        ],
        style=BADGE_STYLE,
    )


def construir_chip_filtro_fecha(filtro):
    texto = f"{str(filtro['inicio']).replace('T', ' ')} a {str(filtro['fin']).replace('T', ' ')}"
    return html.Div(
        [
            html.Span(texto),
            html.Button(
                "Eliminar",
                id={"type": "retirar-filtro-fecha-btn", "value": filtro["id"]},
                n_clicks=0,
            ),
        ],
        style=BADGE_STYLE,
    )


def construir_chip_contexto_operacion(modo_operacion, arranque_id, parada_id, operacion_id):
    chips = []
    if modo_operacion == "completa":
        chips.append(html.Div([html.Span("Modo: Operacion completa")], style=BADGE_STYLE))

    if arranque_id:
        evento = next((item for item in obtener_eventos_operacion() if item["arranque_id"] == arranque_id), None)
        if evento is not None and evento["arranque_inicio"] is not None and evento["arranque_fin"] is not None:
            chips.append(
                html.Div(
                    [
                        html.Span(
                            f"Arranque {evento['indice']:02d}: "
                            f"{formatear_timestamp_corto(evento['arranque_inicio'])} a "
                            f"{formatear_timestamp_corto(evento['arranque_fin'])}"
                        )
                    ],
                    style=BADGE_STYLE,
                )
            )

    if parada_id:
        evento = next((item for item in obtener_eventos_operacion() if item["parada_id"] == parada_id), None)
        if evento is not None and evento["parada_inicio"] is not None and evento["parada_fin"] is not None:
            chips.append(
                html.Div(
                    [
                        html.Span(
                            f"Parada {evento['indice']:02d}: "
                            f"{formatear_timestamp_corto(evento['parada_inicio'])} a "
                            f"{formatear_timestamp_corto(evento['parada_fin'])}"
                        )
                    ],
                    style=BADGE_STYLE,
                )
            )

    if operacion_id:
        operacion = next((item for item in obtener_operaciones() if item["operacion_id"] == operacion_id), None)
        if operacion is not None and operacion["operacion_inicio"] is not None and operacion["operacion_fin"] is not None:
            chips.append(
                html.Div(
                    [
                        html.Span(
                            f"Operacion {operacion['indice']:02d}: "
                            f"{formatear_timestamp_corto(operacion['operacion_inicio'])} a "
                            f"{formatear_timestamp_corto(operacion['operacion_fin'])}"
                        )
                    ],
                    style=BADGE_STYLE,
                )
            )

    if not chips:
        return html.Div("Contexto operacional: toda la data.")
    return html.Div(chips, style=BADGE_CONTAINER_STYLE)


def construir_bloque_reporte(
    correlaciones,
    serie_objetivo,
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
                        ],
                        style=REPORTE_HISTOGRAMA_STYLE,
                    ),
                    html.Div(
                        [
                            html.H2("Correlaciones lineales"),
                            construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                        ],
                        style=REPORTE_CORRELACIONES_STYLE,
                    ),
                ],
                style=REPORTE_RESUMEN_STYLE,
            ),
        ]
    )


def construir_bloque_resultado(correlaciones, serie_objetivo):
    return html.Div(
        [
            construir_bloque_reporte(
                correlaciones,
                serie_objetivo,
            ),
        ],
        style={"marginBottom": "24px"},
    )


def construir_bloque_comparacion_variables(
    df_numerico,
    variable_x,
    variable_y,
    correlacion=None,
    titulo=None,
):
    descripcion_correlacion = (
        f"r={correlacion:.4f}" if correlacion is not None else "r no disponible"
    )
    encabezado = (
        f"{construir_etiqueta_columna(variable_x)} vs "
        f"{construir_etiqueta_columna(variable_y)}"
    )

    return html.Div(
        [
            html.H2(titulo or "Comparacion"),
            html.Div(
                f"{encabezado} ({descripcion_correlacion})",
                style={"marginBottom": "12px", "fontWeight": "600"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Variable vs variable"),
                            construir_grafico_dispersion(
                                df_numerico,
                                variable_y,
                                variable_x,
                                construir_etiqueta_columna,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.H4("Boxplot comparativo"),
                            construir_boxplot_relacion(
                                df_numerico,
                                variable_y,
                                variable_x,
                                construir_etiqueta_columna,
                            ),
                        ]
                    ),
                ],
                style=RELACION_FILA_STYLE,
            ),
        ],
        style={"marginBottom": "24px"},
    )

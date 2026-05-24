from dash import html

from dashboard_app.domain.semaforo import (
    calcular_estado_semaforo,
    construir_anotaciones_umbral,
    construir_configuracion_semaforo,
    parsear_valor_numerico,
)
from dashboard_app.pages.indicator_utils import (
    EMPTY_STATE_STYLE,
    HEADER_CELL_STYLE,
    STATUS_STYLES,
    TABLE_STYLE,
    TABLE_WRAPPER_STYLE,
    construir_celda,
    construir_celda_grafico,
    construir_grafico_semaforo,
    formatear_numero,
    formatear_texto,
)


def construir_estado_vacio(texto):
    return html.Div(texto, style=EMPTY_STATE_STYLE)


def obtener_ultimo_valor(serie):
    if serie is None:
        return None
    serie_valida = serie.dropna()
    if serie_valida.empty:
        return None
    return float(serie_valida.iloc[-1])


def construir_indicador_variable(variable, valor_actual):
    configuracion = construir_configuracion_semaforo(variable)
    segmentos = configuracion["segmentos"]
    actual = parsear_valor_numerico(valor_actual)
    if actual is None or not segmentos:
        return html.Div("Sin datos suficientes para construir el indicador.", style={"color": "#6b7280"})

    limites = [inicio for _, inicio, _ in segmentos] + [segmentos[-1][2]]
    return construir_grafico_semaforo(
        actual=actual,
        segmentos=segmentos,
        limites=limites,
        hover_label="Ultimo valor",
        padding_ratio=0.08,
        mostrar_zonas_rojas_externas=True,
        annotations=construir_anotaciones_umbral(configuracion["umbrales"]),
    )


def construir_tabla_semaforos(vista, dataframe, columnas_disponibles):
    variables = list((vista or {}).get("variables") or [])
    if not variables:
        return construir_estado_vacio("La vista seleccionada no tiene variables configuradas.")

    filas = []
    faltantes = []
    for variable in variables:
        columna = variable.get("column")
        valor_actual = None
        if columna and columna in dataframe.columns:
            valor_actual = obtener_ultimo_valor(dataframe[columna])
        elif columna and columna not in columnas_disponibles:
            faltantes.append(columna)

        configuracion = construir_configuracion_semaforo(variable)
        estado = calcular_estado_semaforo(valor_actual, configuracion)
        row_style = STATUS_STYLES.get(estado, STATUS_STYLES["normal"])
        filas.append(
            html.Tr(
                [
                    construir_celda(formatear_texto(variable.get("tag")), row_style),
                    construir_celda(formatear_texto(variable.get("descripcion")), row_style),
                    construir_celda(formatear_texto(variable.get("scope"), es_fase=True), row_style),
                    construir_celda(formatear_numero(valor_actual), row_style),
                    construir_celda_grafico(construir_indicador_variable(variable, valor_actual), row_style),
                ]
            )
        )

    contenido = [
        html.Div(
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(texto, style=HEADER_CELL_STYLE)
                                for texto in ("TAG", "Descripcion", "Fase", "Ultimo valor", "Indicador")
                            ]
                        )
                    ),
                    html.Tbody(filas),
                ],
                style=TABLE_STYLE,
            ),
            style=TABLE_WRAPPER_STYLE,
        )
    ]

    if faltantes:
        contenido.insert(
            0,
            html.Div(
                "No se encontro data para algunas variables de la vista: "
                + ", ".join(sorted(set(faltantes))),
                style={"marginBottom": "12px", "color": "#8f1d1d"},
            ),
        )

    return contenido

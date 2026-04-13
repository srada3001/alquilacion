from dash import ALL, Input, Output, State, callback_context, html

from dashboard_app.callbacks.common import (
    ACCION_RETIRAR_STYLE,
    BADGE_CONTAINER_STYLE,
    BADGE_STYLE,
    construir_etiqueta_columna,
    construir_opciones_variables_por_fase,
    expandir_valor_variable,
    normalizar_lista_unica,
    obtener_freq_efectiva,
)
from dashboard_app.data import formatear_nombre_fase, obtener_data_uri_imagen_fase


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


def register_selectors_callbacks(app):
    @app.callback(
        Output("fase-imagen-container", "children"),
        Input("seleccion-fases-dropdown", "value"),
    )
    def actualizar_imagen_fase(fase):
        return construir_imagen_fase(fase)

    @app.callback(
        Output("seleccion-variables-dropdown", "options"),
        Output("seleccion-variables-dropdown", "value"),
        Input("estado-grafico-store", "data"),
        Input("filtros-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
        Input("filtro-operacion-dropdown", "value"),
        Input("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
    )
    def actualizar_variables_selector(
        estado_grafico,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
        fase,
        valor_actual,
    ):
        freq = obtener_freq_efectiva(
            estado_grafico,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )
        opciones = construir_opciones_variables_por_fase(freq, fase, incluir_grupos=True)
        valores_validos = {opcion["value"] for opcion in opciones}
        return opciones, valor_actual if valor_actual in valores_validos else None

    @app.callback(
        Output("variables-seleccionadas-store", "data", allow_duplicate=True),
        Input("anadir-variable-btn", "n_clicks"),
        Input({"type": "retirar-variable-btn", "value": ALL}, "n_clicks"),
        State("estado-grafico-store", "data"),
        State("filtros-store", "data"),
        State("modo-operacion-radio", "value"),
        State("filtro-arranque-dropdown", "value"),
        State("filtro-parada-dropdown", "value"),
        State("filtro-operacion-dropdown", "value"),
        State("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_variables_agregadas(
        _,
        __,
        estado_grafico,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
        fase,
        valor_variable,
        variables_agregadas,
    ):
        variables_agregadas = list(variables_agregadas or [])
        disparador = callback_context.triggered_id
        freq = obtener_freq_efectiva(
            estado_grafico,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )

        if disparador == "anadir-variable-btn":
            nuevas = expandir_valor_variable(freq, fase, valor_variable)
            variables_agregadas.extend(nuevas)
            return normalizar_lista_unica(variables_agregadas)

        if isinstance(disparador, dict) and disparador.get("type") == "retirar-variable-btn":
            variable = disparador["value"]
            return [v for v in variables_agregadas if v != variable]

        return variables_agregadas

    @app.callback(
        Output("variables-seleccionadas-container", "children"),
        Input("variables-seleccionadas-store", "data"),
    )
    def mostrar_variables_agregadas(variables_agregadas):
        if not variables_agregadas:
            return html.Div("No hay variables anadidas.")
        return html.Div(
            [construir_chip_variable(variable) for variable in variables_agregadas],
            style=BADGE_CONTAINER_STYLE,
        )

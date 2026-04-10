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


def register_selectors_callbacks(app):
    @app.callback(
        Output("seleccion-variables-dropdown", "options"),
        Output("seleccion-variables-dropdown", "value"),
        Input("estado-grafico-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
        Input("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
    )
    def actualizar_variables_selector(estado_grafico, modo_operacion, arranque_id, parada_id, fase, valor_actual):
        freq = obtener_freq_efectiva(estado_grafico, modo_operacion, arranque_id, parada_id)
        opciones = construir_opciones_variables_por_fase(freq, fase, incluir_grupos=True)
        valores_validos = {opcion["value"] for opcion in opciones}
        return opciones, valor_actual if valor_actual in valores_validos else None

    @app.callback(
        Output("variables-seleccionadas-store", "data", allow_duplicate=True),
        Input("anadir-variable-btn", "n_clicks"),
        Input({"type": "retirar-variable-btn", "value": ALL}, "n_clicks"),
        State("estado-grafico-store", "data"),
        State("modo-operacion-radio", "value"),
        State("filtro-arranque-dropdown", "value"),
        State("filtro-parada-dropdown", "value"),
        State("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_variables_agregadas(
        _,
        __,
        estado_grafico,
        modo_operacion,
        arranque_id,
        parada_id,
        fase,
        valor_variable,
        variables_agregadas,
    ):
        variables_agregadas = list(variables_agregadas or [])
        disparador = callback_context.triggered_id
        freq = obtener_freq_efectiva(estado_grafico, modo_operacion, arranque_id, parada_id)

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

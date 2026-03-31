from dash import ALL, Input, Output, State, callback_context, html

from dashboard_app.callbacks.common import (
    BADGE_CONTAINER_STYLE,
    BADGE_STYLE,
    cargar_dataset_para_columnas,
    construir_etiqueta_columna,
    obtener_freq_desde_estado_grafico,
)
from dashboard_app.domain.filters import (
    construir_mascara_desde_df,
    construir_mascara_rechazo_desde_df,
)


def construir_chip_filtro(filtro):
    texto = f"{construir_etiqueta_columna(filtro['columna'])} {filtro['operador']} {filtro['valor']}"
    return html.Div(
        [
            html.Span(texto),
            html.Button("Eliminar", id={"type": "retirar-filtro-btn", "value": filtro["id"]}, n_clicks=0),
        ],
        style=BADGE_STYLE,
    )


def construir_mascara_global(freq, filtros):
    columnas_filtro = [filtro["columna"] for filtro in filtros if filtro.get("columna")]
    if not columnas_filtro:
        return None

    df_filtros = cargar_dataset_para_columnas(freq, columnas_filtro)
    return construir_mascara_desde_df(df_filtros, filtros)


def register_filters_callbacks(app):
    @app.callback(
        Output("filtro-variable-crear-dropdown", "options"),
        Output("filtro-variable-crear-dropdown", "value"),
        Input("variables-seleccionadas-store", "data"),
        State("filtro-variable-crear-dropdown", "value"),
    )
    def actualizar_variables_filtro(variables_seleccionadas, valor_actual):
        opciones = [
            {"label": construir_etiqueta_columna(variable), "value": variable}
            for variable in list(variables_seleccionadas or [])
        ]
        valores_validos = {opcion["value"] for opcion in opciones}
        valor = valor_actual if valor_actual in valores_validos else None
        return opciones, valor

    @app.callback(
        Output("filtros-store", "data", allow_duplicate=True),
        Output("filtro-valor-crear-input", "value"),
        Input("anadir-filtro-btn", "n_clicks"),
        Input({"type": "retirar-filtro-btn", "value": ALL}, "n_clicks"),
        State("estado-grafico-store", "data"),
        State("filtro-variable-crear-dropdown", "value"),
        State("filtro-operador-crear-dropdown", "value"),
        State("filtro-valor-crear-input", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_filtros_agregados(_, __, estado_grafico, valor_variable, operador, valor, filtros_guardados):
        filtros_guardados = list(filtros_guardados or [])
        disparador = callback_context.triggered_id
        _ = obtener_freq_desde_estado_grafico(estado_grafico)

        if disparador == "anadir-filtro-btn":
            columnas = [valor_variable] if valor_variable else []
            siguiente_id = max((filtro.get("id", -1) for filtro in filtros_guardados), default=-1) + 1
            for columna in columnas:
                filtros_guardados.append(
                    {
                        "id": siguiente_id,
                        "columna": columna,
                        "operador": operador,
                        "valor": valor,
                    }
                )
                siguiente_id += 1
            return filtros_guardados, None

        if isinstance(disparador, dict) and disparador.get("type") == "retirar-filtro-btn":
            restantes = [
                filtro
                for filtro in filtros_guardados
                if filtro.get("id") != disparador["value"]
            ]
            return restantes, valor

        return filtros_guardados, valor

    @app.callback(
        Output("filtros-container", "children"),
        Output("filtros-resumen", "children"),
        Input("estado-grafico-store", "data"),
        Input("filtros-store", "data"),
        Input("variables-seleccionadas-store", "data"),
    )
    def mostrar_filtros(estado_grafico, filtros_guardados, variables_seleccionadas):
        filtros_guardados = list(filtros_guardados or [])
        if filtros_guardados:
            chips = html.Div(
                [construir_chip_filtro(filtro) for filtro in filtros_guardados],
                style=BADGE_CONTAINER_STYLE,
            )
        else:
            chips = html.Div("No hay filtros anadidos.")

        if not variables_seleccionadas:
            return chips, html.Div("Muestras eliminadas: 0 (0.00% del dataframe total).")

        columnas_requeridas = list(variables_seleccionadas) + [
            filtro["columna"] for filtro in filtros_guardados if filtro.get("columna")
        ]
        freq = obtener_freq_desde_estado_grafico(estado_grafico)
        df_combinado = cargar_dataset_para_columnas(freq, columnas_requeridas)
        total = len(df_combinado.index)
        rechazo = construir_mascara_rechazo_desde_df(df_combinado, filtros_guardados)
        eliminadas = int(rechazo.sum()) if rechazo is not None else 0
        porcentaje = (eliminadas / total * 100) if total else 0

        resumen = html.Div(
            f"Muestras eliminadas: {eliminadas} ({porcentaje:.2f}% del dataframe total)."
        )
        return chips, resumen

from dash import ALL, Input, Output, State, callback_context, html
import re

from dashboard_app.callbacks.common import (
    BADGE_CONTAINER_STYLE,
    BADGE_STYLE,
    cargar_dataset_para_columnas,
    construir_mascara_modo_datos,
    construir_etiqueta_columna,
    obtener_freq_desde_estado_grafico,
)
from dashboard_app.domain.filters import (
    combinar_mascaras,
    construir_mascara_desde_df,
    normalizar_filtros_guardados,
    obtener_filtros_fecha,
    obtener_filtros_variable,
)


HORA_REGEX = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def normalizar_hora(hora, hora_por_defecto):
    hora_texto = str(hora or "").strip()
    return hora_texto if HORA_REGEX.match(hora_texto) else hora_por_defecto


def construir_fecha_hora(fecha, hora, hora_por_defecto):
    if not fecha:
        return None
    return f"{fecha}T{normalizar_hora(hora, hora_por_defecto)}"


def formatear_fecha_hora(valor):
    return str(valor).replace("T", " ")


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
    texto = f"{formatear_fecha_hora(filtro['inicio'])} a {formatear_fecha_hora(filtro['fin'])}"
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


def construir_mascara_global(freq, filtros, modo_datos="todo", columnas_base=None):
    filtros_normalizados = normalizar_filtros_guardados(filtros)
    filtros_fecha = obtener_filtros_fecha(filtros_normalizados)
    columnas_filtro = [
        filtro["columna"]
        for filtro in obtener_filtros_variable(filtros_normalizados)
        if filtro.get("columna")
    ]
    columnas_requeridas = list(columnas_base or []) + columnas_filtro
    if not columnas_requeridas and not filtros_fecha and modo_datos == "todo":
        return None

    df_filtros = cargar_dataset_para_columnas(
        freq,
        columnas_requeridas,
        cargar_todo_si_vacio=bool(filtros_fecha) or modo_datos != "todo",
    )
    return combinar_mascaras(
        construir_mascara_desde_df(df_filtros, filtros_normalizados),
        construir_mascara_modo_datos(df_filtros, modo_datos, freq),
    )


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
        Output("filtro-fecha-inicio-input", "date"),
        Output("filtro-hora-inicio-input", "value"),
        Output("filtro-fecha-fin-input", "date"),
        Output("filtro-hora-fin-input", "value"),
        Input("anadir-filtro-btn", "n_clicks"),
        Input("anadir-filtro-fecha-btn", "n_clicks"),
        Input({"type": "retirar-filtro-variable-btn", "value": ALL}, "n_clicks"),
        Input({"type": "retirar-filtro-fecha-btn", "value": ALL}, "n_clicks"),
        State("estado-grafico-store", "data"),
        State("filtro-variable-crear-dropdown", "value"),
        State("filtro-operador-crear-dropdown", "value"),
        State("filtro-valor-crear-input", "value"),
        State("filtro-fecha-inicio-input", "date"),
        State("filtro-hora-inicio-input", "value"),
        State("filtro-fecha-fin-input", "date"),
        State("filtro-hora-fin-input", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_filtros_agregados(
        _,
        __,
        ___,
        ____,
        estado_grafico,
        valor_variable,
        operador,
        valor,
        fecha_inicio,
        hora_inicio,
        fecha_fin,
        hora_fin,
        filtros_guardados,
    ):
        filtros_guardados = normalizar_filtros_guardados(filtros_guardados)
        disparador = callback_context.triggered_id
        _ = obtener_freq_desde_estado_grafico(estado_grafico)
        filtros_variable = list(obtener_filtros_variable(filtros_guardados))
        filtros_fecha = list(obtener_filtros_fecha(filtros_guardados))
        siguiente_id = max(
            (filtro.get("id", -1) for filtro in filtros_variable + filtros_fecha),
            default=-1,
        ) + 1

        if disparador == "anadir-filtro-btn":
            if valor_variable and operador and valor is not None:
                filtros_variable.append(
                    {
                        "id": siguiente_id,
                        "columna": valor_variable,
                        "operador": operador,
                        "valor": valor,
                    }
                )
                return {
                    "variables": filtros_variable,
                    "fechas": filtros_fecha,
                }, None, fecha_inicio, hora_inicio, fecha_fin, hora_fin
            return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if disparador == "anadir-filtro-fecha-btn":
            inicio = construir_fecha_hora(fecha_inicio, hora_inicio, "00:00")
            fin = construir_fecha_hora(fecha_fin, hora_fin, "23:59")
            if inicio and fin:
                if fin < inicio:
                    inicio, fin = fin, inicio
                filtros_fecha.append(
                    {
                        "id": siguiente_id,
                        "inicio": inicio,
                        "fin": fin,
                    }
                )
                return {
                    "variables": filtros_variable,
                    "fechas": filtros_fecha,
                }, valor, None, "00:00", None, "23:59"
            return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if isinstance(disparador, dict) and disparador.get("type") == "retirar-filtro-variable-btn":
            restantes = [
                filtro
                for filtro in filtros_variable
                if filtro.get("id") != disparador["value"]
            ]
            return {
                "variables": restantes,
                "fechas": filtros_fecha,
            }, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if isinstance(disparador, dict) and disparador.get("type") == "retirar-filtro-fecha-btn":
            restantes = [
                filtro
                for filtro in filtros_fecha
                if filtro.get("id") != disparador["value"]
            ]
            return {
                "variables": filtros_variable,
                "fechas": restantes,
            }, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

    @app.callback(
        Output("filtros-variable-container", "children"),
        Output("filtros-fecha-container", "children"),
        Output("filtros-resumen", "children"),
        Input("estado-grafico-store", "data"),
        Input("filtros-store", "data"),
        Input("variables-seleccionadas-store", "data"),
        Input("modo-datos-radio", "value"),
    )
    def mostrar_filtros(estado_grafico, filtros_guardados, variables_seleccionadas, modo_datos):
        filtros_guardados = normalizar_filtros_guardados(filtros_guardados)
        filtros_variable = obtener_filtros_variable(filtros_guardados)
        filtros_fecha = obtener_filtros_fecha(filtros_guardados)

        if filtros_variable:
            chips_variable = html.Div(
                [construir_chip_filtro_variable(filtro) for filtro in filtros_variable],
                style=BADGE_CONTAINER_STYLE,
            )
        else:
            chips_variable = html.Div("No hay filtros por variable anadidos.")

        if filtros_fecha:
            chips_fecha = html.Div(
                [construir_chip_filtro_fecha(filtro) for filtro in filtros_fecha],
                style=BADGE_CONTAINER_STYLE,
            )
        else:
            chips_fecha = html.Div("No hay filtros por fecha anadidos.")

        freq = obtener_freq_desde_estado_grafico(estado_grafico)
        columnas_requeridas = list(variables_seleccionadas or []) + [
            filtro["columna"] for filtro in filtros_variable if filtro.get("columna")
        ]
        if not columnas_requeridas and not filtros_fecha and modo_datos == "todo":
            return (
                chips_variable,
                chips_fecha,
                html.Div("Muestras eliminadas: 0 (0.00% del dataframe total)."),
            )

        df_combinado = cargar_dataset_para_columnas(
            freq,
            columnas_requeridas,
            cargar_todo_si_vacio=bool(filtros_fecha) or modo_datos != "todo",
        )
        total = len(df_combinado.index)
        mascara_total = combinar_mascaras(
            construir_mascara_desde_df(df_combinado, filtros_guardados),
            construir_mascara_modo_datos(df_combinado, modo_datos, freq),
        )
        rechazo = ~mascara_total if mascara_total is not None else None
        eliminadas = int(rechazo.sum()) if rechazo is not None else 0
        porcentaje = (eliminadas / total * 100) if total else 0

        resumen = html.Div(
            f"Muestras eliminadas: {eliminadas} ({porcentaje:.2f}% del dataframe total)."
        )
        return chips_variable, chips_fecha, resumen

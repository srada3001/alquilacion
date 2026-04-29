from dash import ALL, Input, Output, State, callback_context, html, no_update
import plotly.graph_objects as go
import re

from dashboard_app.callbacks.common import (
    BADGE_CONTAINER_STYLE,
    cargar_dataset_para_columnas,
    construir_etiqueta_columna,
    construir_mascara_contexto_operacion,
    construir_opciones_periodo_detalle,
    construir_opciones_variables_por_fase,
    expandir_valor_variable,
    normalizar_lista_unica,
    normalizar_serie,
    obtener_freq_desde_relayout,
    obtener_freq_efectiva,
    obtener_rango_desde_estado_grafico,
    obtener_rango_desde_relayout,
    resolver_contexto_operacion_desde_periodo,
)
from dashboard_app.data import obtener_unidad_columna
from dashboard_app.domain.filters import (
    combinar_mascaras,
    construir_mascara_desde_df,
    normalizar_filtros_guardados,
    obtener_filtro_periodo,
    obtener_filtros_variable,
)
from dashboard_app.pages.series_temporales.domain import (
    calcular_correlaciones_para_variable,
)
from dashboard_app.pages.series_temporales.views import (
    construir_bloque_resultado,
    construir_chip_contexto_operacion,
    construir_chip_filtro_periodo,
    construir_chip_filtro_variable,
    construir_chip_variable,
    construir_imagen_fase,
)

HORA_REGEX = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
UNIDAD_SIN_DEFINIR = "Sin unidad definida"
UNIDAD_NORMALIZADA = "Valor normalizado"
EJE_RESERVA_POR_LADO = 0.06
VISTAS_TEMPORALES = {
    "vista_1": [
        "horno | FI-1238-ALQUILATO",
        "horno | FI-1666A",
        "horno | TI-1497",
    ]
}


def normalizar_hora(hora, hora_por_defecto):
    hora_texto = str(hora or "").strip()
    return hora_texto if HORA_REGEX.match(hora_texto) else hora_por_defecto


def construir_fecha_hora(fecha, hora, hora_por_defecto):
    if not fecha:
        return None
    return f"{fecha}T{normalizar_hora(hora, hora_por_defecto)}"


def es_id_patron(disparador, tipo):
    return hasattr(disparador, "get") and disparador.get("type") == tipo


def hay_contexto_operacion(modo_operacion=None, arranque_id=None, parada_id=None, operacion_id=None):
    return modo_operacion == "completa" or bool(arranque_id) or bool(parada_id) or bool(operacion_id)


def construir_mascara_global(
    freq,
    filtros,
    columnas_base=None,
    modo_operacion=None,
    arranque_id=None,
    parada_id=None,
    operacion_id=None,
):
    filtros_normalizados = normalizar_filtros_guardados(filtros)
    filtro_periodo = obtener_filtro_periodo(filtros_normalizados)
    columnas_filtro = [
        filtro["columna"]
        for filtro in obtener_filtros_variable(filtros_normalizados)
        if filtro.get("columna")
    ]
    columnas_requeridas = list(columnas_base or []) + columnas_filtro
    if not columnas_requeridas and not filtro_periodo and not hay_contexto_operacion(
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
    ):
        return None

    df_filtros = cargar_dataset_para_columnas(
        freq,
        columnas_requeridas,
        cargar_todo_si_vacio=bool(filtro_periodo) or hay_contexto_operacion(
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        ),
    )
    return combinar_mascaras(
        construir_mascara_desde_df(df_filtros, filtros_normalizados),
        construir_mascara_contexto_operacion(df_filtros, modo_operacion, arranque_id, parada_id, operacion_id),
    )


def cargar_dataframe_filtrado(
    estado_grafico,
    columnas,
    filtros_guardados,
    modo_operacion=None,
    arranque_id=None,
    parada_id=None,
    operacion_id=None,
):
    rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
    columnas = list(columnas or [])
    if not columnas:
        return cargar_dataset_para_columnas("1h", [])

    filtros_guardados = normalizar_filtros_guardados(filtros_guardados)
    columnas_requeridas = columnas + [
        filtro["columna"]
        for filtro in obtener_filtros_variable(filtros_guardados)
        if filtro.get("columna")
    ]
    freq = obtener_freq_efectiva(
        estado_grafico,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
    )
    df_combinado = cargar_dataset_para_columnas(
        freq,
        columnas_requeridas,
        cargar_todo_si_vacio=hay_contexto_operacion(
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        ),
        rango_tiempo=rango_visible,
    )
    mascara = combinar_mascaras(
        construir_mascara_desde_df(df_combinado, filtros_guardados),
        construir_mascara_contexto_operacion(df_combinado, modo_operacion, arranque_id, parada_id, operacion_id),
    )
    if mascara is not None:
        mascara = mascara.reindex(df_combinado.index, fill_value=False)
        return df_combinado.loc[mascara].copy()
    return df_combinado


def construir_clave_eje(columna, normalizar=False):
    if normalizar:
        return UNIDAD_NORMALIZADA

    unidad = obtener_unidad_columna(columna)
    unidad_resuelta = unidad or UNIDAD_SIN_DEFINIR
    return f"{construir_etiqueta_columna(columna)} [{unidad_resuelta}]"


def resolver_configuracion_ejes(unidades):
    unidades = list(dict.fromkeys(unidades))
    if not unidades:
        return {}, {}

    layout_updates = {}
    referencias = {}
    lado_extra_por_indice = {}
    conteo_lados = {"left": 0, "right": 0}

    for indice, unidad in enumerate(unidades, start=1):
        referencia_traza = "y" if indice == 1 else f"y{indice}"
        referencia_layout = "yaxis" if indice == 1 else f"yaxis{indice}"
        lado = "left" if indice == 1 or indice % 2 == 1 else "right"
        referencias[unidad] = referencia_traza
        lado_extra_por_indice[indice] = lado

        config = {
            "title": unidad,
            "automargin": True,
            "showgrid": indice == 1,
            "zeroline": False,
        }
        if indice == 1:
            config["side"] = "left"
        else:
            config["overlaying"] = "y"
            config["anchor"] = "free"
            config["side"] = lado
            conteo_lados[lado] += 1
            orden_lateral = conteo_lados[lado]
            config["_orden_lateral"] = orden_lateral

        layout_updates[referencia_layout] = config

    dominio_x_inicio = EJE_RESERVA_POR_LADO * conteo_lados["left"]
    dominio_x_fin = 1 - (EJE_RESERVA_POR_LADO * conteo_lados["right"])

    for indice, _unidad in enumerate(unidades, start=1):
        if indice == 1:
            continue

        referencia_layout = "yaxis" if indice == 1 else f"yaxis{indice}"
        config = layout_updates[referencia_layout]
        orden_lateral = config.pop("_orden_lateral")
        lado = lado_extra_por_indice[indice]
        if lado == "left":
            config["position"] = EJE_RESERVA_POR_LADO * (orden_lateral - 0.5)
        else:
            config["position"] = dominio_x_fin + (
                EJE_RESERVA_POR_LADO * (orden_lateral - 0.5)
            )

    layout_updates["xaxis"] = {
        "type": "date",
        "domain": [dominio_x_inicio, dominio_x_fin],
    }
    layout_updates["margin"] = {
        "l": 70 + (45 * conteo_lados["left"]),
        "r": 70 + (45 * conteo_lados["right"]),
        "t": 40,
        "b": 40,
    }
    return referencias, layout_updates


def register_callbacks(app):
    @app.callback(
        Output("fase-imagen-container", "children"),
        Input("seleccion-fases-dropdown", "value"),
    )
    def actualizar_imagen_fase(fase):
        return construir_imagen_fase(fase)

    @app.callback(
        Output("filtro-periodo-detalle-label", "children"),
        Output("filtro-periodo-detalle-label", "style"),
        Output("filtro-periodo-detalle-dropdown", "options"),
        Output("filtro-periodo-detalle-dropdown", "value"),
        Output("filtro-periodo-detalle-dropdown", "placeholder"),
        Output("filtro-periodo-detalle-dropdown", "style"),
        Output("filtro-periodo-fecha-container", "style"),
        Input("filtro-periodo-tipo-dropdown", "value"),
        State("filtro-periodo-detalle-dropdown", "value"),
    )
    def actualizar_controles_periodo(tipo_periodo, detalle_actual):
        estilo_oculto = {"display": "none"}
        estilo_visible = {"display": "block"}

        if tipo_periodo == "fecha":
            return (
                "",
                estilo_oculto,
                [],
                None,
                "Seleccionar periodo",
                estilo_oculto,
                {"marginBottom": "16px", "display": "block"},
            )

        if tipo_periodo in {"arranque", "parada", "operacion"}:
            opciones = construir_opciones_periodo_detalle(tipo_periodo)
            valores_validos = {opcion["value"] for opcion in opciones}
            valor = detalle_actual if detalle_actual in valores_validos else None
            etiquetas = {
                "arranque": "Arranque",
                "parada": "Parada",
                "operacion": "Operaci\u00f3n espec\u00edfica",
            }
            return (
                etiquetas[tipo_periodo],
                {"fontWeight": "600", "marginBottom": "8px", "display": "block"},
                opciones,
                valor,
                f"Seleccionar {etiquetas[tipo_periodo].lower()}",
                estilo_visible,
                {"marginBottom": "16px", "display": "none"},
            )

        return (
            "",
            estilo_oculto,
            [],
            None,
            "Seleccionar periodo",
            estilo_oculto,
            {"marginBottom": "16px", "display": "none"},
        )

    @app.callback(
        Output("seleccion-variables-dropdown", "options"),
        Output("seleccion-variables-dropdown", "value"),
        Input("estado-grafico-store", "data"),
        Input("filtros-store", "data"),
        Input("filtro-periodo-tipo-dropdown", "value"),
        Input("filtro-periodo-detalle-dropdown", "value"),
        Input("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
    )
    def actualizar_variables_selector(
        estado_grafico,
        filtros_guardados,
        tipo_periodo,
        detalle_periodo,
        fase,
        valor_actual,
    ):
        modo_operacion, arranque_id, parada_id, operacion_id = resolver_contexto_operacion_desde_periodo(
            tipo_periodo,
            detalle_periodo,
        )
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
        State("filtro-periodo-tipo-dropdown", "value"),
        State("filtro-periodo-detalle-dropdown", "value"),
        State("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_variables_agregadas(
        anadir_clicks,
        clicks_retirar,
        estado_grafico,
        filtros_guardados,
        tipo_periodo,
        detalle_periodo,
        fase,
        valor_variable,
        variables_agregadas,
    ):
        variables_agregadas = list(variables_agregadas or [])
        disparador = callback_context.triggered_id
        modo_operacion, arranque_id, parada_id, operacion_id = resolver_contexto_operacion_desde_periodo(
            tipo_periodo,
            detalle_periodo,
        )
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

        if es_id_patron(disparador, "retirar-variable-btn"):
            if not any((clicks_retirar or [])):
                return variables_agregadas
            variable = disparador["value"]
            return [v for v in variables_agregadas if v != variable]

        return variables_agregadas

    @app.callback(
        Output("variables-seleccionadas-store", "data", allow_duplicate=True),
        Output("vistas-temporales-dropdown", "value"),
        Input("vistas-temporales-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        prevent_initial_call=True,
    )
    def aplicar_vista_temporal(vista_temporal, variables_agregadas):
        if not vista_temporal:
            return no_update, None

        variables_agregadas = list(variables_agregadas or [])
        variables_vista = VISTAS_TEMPORALES.get(vista_temporal, [])
        return normalizar_lista_unica(variables_agregadas + variables_vista), None

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
        Input("filtro-periodo-tipo-dropdown", "value"),
        Input("filtro-periodo-detalle-dropdown", "value"),
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
        tipo_periodo,
        detalle_periodo,
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
        filtros_variable = list(obtener_filtros_variable(filtros_guardados))
        filtro_periodo = obtener_filtro_periodo(filtros_guardados)
        siguiente_id = max((filtro.get("id", -1) for filtro in filtros_variable), default=-1) + 1

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
                    "periodo": filtro_periodo,
                }, None, fecha_inicio, hora_inicio, fecha_fin, hora_fin
            return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if isinstance(disparador, str) and disparador in {
            "filtro-periodo-tipo-dropdown",
            "filtro-periodo-detalle-dropdown",
        }:
            return {
                "variables": filtros_variable,
                "periodo": None,
            }, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if disparador == "anadir-filtro-fecha-btn":
            inicio = construir_fecha_hora(fecha_inicio, hora_inicio, "00:00")
            fin = construir_fecha_hora(fecha_fin, hora_fin, "23:59")
            if tipo_periodo == "fecha" and inicio and fin:
                if fin < inicio:
                    inicio, fin = fin, inicio
                return {
                    "variables": filtros_variable,
                    "periodo": {
                        "inicio": inicio,
                        "fin": fin,
                    },
                }, valor, None, "00:00", None, "23:59"
            return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        if es_id_patron(disparador, "retirar-filtro-variable-btn"):
            restantes = [
                filtro
                for filtro in filtros_variable
                if filtro.get("id") != disparador["value"]
            ]
            return {
                "variables": restantes,
                "periodo": filtro_periodo,
            }, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

        return filtros_guardados, valor, fecha_inicio, hora_inicio, fecha_fin, hora_fin

    @app.callback(
        Output("filtros-variable-container", "children"),
        Output("filtro-periodo-container", "children"),
        Output("filtros-resumen", "children"),
        Input("estado-grafico-store", "data"),
        Input("filtros-store", "data"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtro-periodo-tipo-dropdown", "value"),
        Input("filtro-periodo-detalle-dropdown", "value"),
    )
    def mostrar_filtros(
        estado_grafico,
        filtros_guardados,
        variables_seleccionadas,
        tipo_periodo,
        detalle_periodo,
    ):
        filtros_guardados = normalizar_filtros_guardados(filtros_guardados)
        filtros_variable = obtener_filtros_variable(filtros_guardados)
        filtro_periodo = obtener_filtro_periodo(filtros_guardados)
        modo_operacion, arranque_id, parada_id, operacion_id = resolver_contexto_operacion_desde_periodo(
            tipo_periodo,
            detalle_periodo,
        )
        chips_contexto = construir_chip_contexto_operacion(modo_operacion, arranque_id, parada_id, operacion_id)

        if filtros_variable:
            chips_variable = html.Div(
                [construir_chip_filtro_variable(filtro) for filtro in filtros_variable],
                style=BADGE_CONTAINER_STYLE,
            )
        else:
            chips_variable = html.Div("No hay filtros por variable anadidos.")

        if tipo_periodo == "fecha" and filtro_periodo:
            chips_periodo = html.Div(
                [construir_chip_filtro_periodo(filtro_periodo)],
                style=BADGE_CONTAINER_STYLE,
            )
        elif hay_contexto_operacion(modo_operacion, arranque_id, parada_id, operacion_id):
            chips_periodo = chips_contexto
        else:
            chips_periodo = html.Div("No hay filtro de periodo activo.")

        freq = obtener_freq_efectiva(
            estado_grafico,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )
        rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
        columnas_requeridas = list(variables_seleccionadas or []) + [
            filtro["columna"] for filtro in filtros_variable if filtro.get("columna")
        ]
        if not filtros_variable and not filtro_periodo and not hay_contexto_operacion(
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        ):
            return (
                chips_variable,
                chips_periodo,
                html.Div("Muestras eliminadas: 0 (0.00% del dataframe total)."),
            )

        df_combinado = cargar_dataset_para_columnas(
            freq,
            columnas_requeridas,
            cargar_todo_si_vacio=bool(filtro_periodo) or hay_contexto_operacion(
                modo_operacion,
                arranque_id,
                parada_id,
                operacion_id,
            ),
            rango_tiempo=rango_visible,
        )
        total = len(df_combinado.index)
        mascara_total = combinar_mascaras(
            construir_mascara_desde_df(df_combinado, filtros_guardados),
            construir_mascara_contexto_operacion(df_combinado, modo_operacion, arranque_id, parada_id, operacion_id),
        )
        rechazo = ~mascara_total if mascara_total is not None else None
        eliminadas = int(rechazo.sum()) if rechazo is not None else 0
        porcentaje = (eliminadas / total * 100) if total else 0
        alcance = "del rango visible" if rango_visible is not None else "del dataframe total"

        resumen = html.Div(
            [
                html.Div(
                    f"Muestras eliminadas: {eliminadas} ({porcentaje:.2f}% {alcance})."
                ),
            ]
        )
        return chips_variable, chips_periodo, resumen

    @app.callback(
        Output("estado-grafico-store", "data", allow_duplicate=True),
        Input("grafico", "relayoutData"),
        State("estado-grafico-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_estado_grafico(relayout_data, estado_grafico):
        estado_grafico = dict(estado_grafico or {"freq": "1h", "range": None})
        if not relayout_data:
            return no_update

        if relayout_data.get("xaxis.autorange"):
            nuevo_estado = {"freq": "1h", "range": None}
            return no_update if nuevo_estado == estado_grafico else nuevo_estado

        rango = obtener_rango_desde_relayout(relayout_data)
        if rango is None:
            return no_update

        nuevo_estado = {
            "freq": obtener_freq_desde_relayout(relayout_data),
            "range": rango,
        }
        return no_update if nuevo_estado == estado_grafico else nuevo_estado

    @app.callback(
        Output("grafico", "figure"),
        Input("estado-grafico-store", "data"),
        Input("normalizar-checklist", "value"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtros-store", "data"),
        Input("filtro-periodo-tipo-dropdown", "value"),
        Input("filtro-periodo-detalle-dropdown", "value"),
    )
    def actualizar_grafico(
        estado_grafico,
        normalizar_opciones,
        variables_seleccionadas,
        filtros_guardados,
        tipo_periodo,
        detalle_periodo,
    ):
        columnas = list(variables_seleccionadas or [])
        if not columnas:
            return go.Figure()

        modo_operacion, arranque_id, parada_id, operacion_id = resolver_contexto_operacion_desde_periodo(
            tipo_periodo,
            detalle_periodo,
        )
        df_grafico = cargar_dataframe_filtrado(
            estado_grafico,
            columnas,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )

        normalizar = "normalizar" in (normalizar_opciones or [])
        fig = go.Figure()
        unidades_visibles = []

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            clave_eje = construir_clave_eje(col, normalizar=normalizar)
            unidades_visibles.append(clave_eje)
        referencias_eje, layout_ejes = resolver_configuracion_ejes(unidades_visibles)

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            serie = normalizar_serie(df_grafico[col]) if normalizar else df_grafico[col]
            clave_eje = construir_clave_eje(col, normalizar=normalizar)
            fig.add_trace(
                go.Scatter(
                    x=df_grafico.index,
                    y=serie,
                    mode="lines",
                    name=construir_etiqueta_columna(col),
                    connectgaps=False,
                    yaxis=referencias_eje.get(clave_eje, "y"),
                )
            )

        fig.update_layout(
            hovermode="x unified",
            showlegend=True,
            uirevision=(
                f"grafico-principal::{modo_operacion}::"
                f"{arranque_id or 'sin-arranque'}::{parada_id or 'sin-parada'}::"
                f"{operacion_id or 'sin-operacion'}"
            ),
            **layout_ejes,
        )
        rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
        if rango_visible is not None and not hay_contexto_operacion(
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        ):
            fig.update_layout(xaxis_range=rango_visible)
        return fig

    @app.callback(
        Output("report-variable-dropdown", "options"),
        Output("report-variable-dropdown", "value"),
        Input("variables-seleccionadas-store", "data"),
        State("report-variable-dropdown", "value"),
    )
    def sincronizar_variables_reporte(variables_seleccionadas, valor_actual):
        variables = list(variables_seleccionadas or [])
        opciones = [
            {"label": construir_etiqueta_columna(columna), "value": columna}
            for columna in variables
        ]
        valores_validos = {opcion["value"] for opcion in opciones}
        valor = valor_actual if valor_actual in valores_validos else None
        return opciones, valor

    @app.callback(
        Output("report-container", "children", allow_duplicate=True),
        Input("report-variable-dropdown", "value"),
        Input("filtros-store", "data"),
        Input("filtro-periodo-tipo-dropdown", "value"),
        Input("filtro-periodo-detalle-dropdown", "value"),
        prevent_initial_call=True,
    )
    def actualizar_reporte(columna_reporte, filtros_guardados, tipo_periodo, detalle_periodo):
        if not columna_reporte:
            return []

        modo_operacion, arranque_id, parada_id, operacion_id = resolver_contexto_operacion_desde_periodo(
            tipo_periodo,
            detalle_periodo,
        )
        mascara_global = construir_mascara_global(
            "1h",
            filtros_guardados,
            columnas_base=[columna_reporte],
            modo_operacion=modo_operacion,
            arranque_id=arranque_id,
            parada_id=parada_id,
            operacion_id=operacion_id,
        )
        correlaciones, serie_objetivo, df_numerico = calcular_correlaciones_para_variable(
            "1h",
            columna_reporte,
            mascara_global,
        )
        return [
            construir_bloque_resultado(
                correlaciones,
                serie_objetivo,
            )
        ]

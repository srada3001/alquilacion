from dash import ALL, Input, Output, State, callback_context, html
import pandas as pd
import plotly.graph_objects as go

from dashboard_app.data import (
    cargar_dataframes_columnas,
    combinar_dataframes_por_fase,
    formatear_nombre_fase,
    obtener_columnas_fase,
)
from dashboard_app.domain.filters import (
    OPERADORES_FILTRO,
    construir_mascara_desde_df,
    construir_mascara_rechazo_desde_df,
)
from dashboard_app.domain.statistics import (
    calcular_correlaciones_para_variable,
    construir_histograma,
    construir_tabla_correlacion,
    construir_tabla_describe,
)


BADGE_CONTAINER_STYLE = {
    "display": "flex",
    "flexWrap": "wrap",
    "gap": "8px",
    "marginBottom": "12px",
}


BADGE_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "8px",
    "padding": "6px 10px",
    "border": "1px solid #d9d9d9",
    "borderRadius": "999px",
    "backgroundColor": "#f7f7f7",
}


RESULTADOS_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
    "gap": "16px",
    "alignItems": "start",
}


GRUPO_PREFIX = "__grupo__::"
GRUPOS_VARIABLES = {
    "AI": "Niveles de oxigeno",
    "FI": "Flujos",
    "NI": "Niveles",
    "PD": "Presiones",
    "PI": "Presiones",
    "TI": "Temperaturas",
}


def normalizar_serie(serie):
    rango = serie.max() - serie.min()
    if rango == 0:
        return serie * 0
    return (serie - serie.min()) / rango


def construir_valor_columna(fase, columna):
    return f"{fase} | {columna}"


def separar_valor_columna(valor):
    return valor.split(" | ", 1)


def construir_etiqueta_fase(fase):
    return formatear_nombre_fase(fase)


def construir_etiqueta_columna(valor):
    fase, columna = separar_valor_columna(valor)
    return f"{construir_etiqueta_fase(fase)} | {columna}"


def construir_opciones_variables_por_fase(freq, fase, incluir_grupos=True):
    if not fase:
        return []

    columnas = sorted(obtener_columnas_fase(fase, freq))
    opciones = []

    if incluir_grupos:
        conteos_grupo = {}
        for columna in columnas:
            prefijo = columna[:2]
            if prefijo in GRUPOS_VARIABLES:
                conteos_grupo[prefijo] = conteos_grupo.get(prefijo, 0) + 1

        grupos = sorted(
            prefijo
            for prefijo, cantidad in conteos_grupo.items()
            if cantidad >= 2
        )
        opciones.extend(
            {"label": GRUPOS_VARIABLES[grupo], "value": f"{GRUPO_PREFIX}{grupo}"}
            for grupo in grupos
        )

    opciones.extend(
        {"label": columna, "value": construir_valor_columna(fase, columna)}
        for columna in columnas
    )
    return opciones


def expandir_valor_variable(freq, fase, valor):
    if not fase or not valor:
        return []
    if valor.startswith(GRUPO_PREFIX):
        grupo = valor.replace(GRUPO_PREFIX, "", 1)
        columnas = sorted(obtener_columnas_fase(fase, freq))
        return [
            construir_valor_columna(fase, columna)
            for columna in columnas
            if columna.startswith(grupo)
        ]
    return [valor]


def agrupar_columnas_por_fase(columnas_combinadas):
    columnas_por_fase = {}

    for columna in columnas_combinadas or []:
        fase, nombre_columna = separar_valor_columna(columna)
        columnas_por_fase.setdefault(fase, [])
        columnas_por_fase[fase].append(nombre_columna)

    return columnas_por_fase


def construir_dataframes_para_columnas(freq, columnas_requeridas):
    columnas_por_fase = agrupar_columnas_por_fase(columnas_requeridas)
    return cargar_dataframes_columnas(
        list(columnas_por_fase.keys()),
        freq,
        columnas_por_fase=columnas_por_fase,
    )


def construir_mascara_global(freq, filtros):
    columnas_filtro = [filtro["columna"] for filtro in filtros if filtro.get("columna")]
    if not columnas_filtro:
        return None

    dataframes = construir_dataframes_para_columnas(freq, columnas_filtro)
    df_filtros = combinar_dataframes_por_fase(dataframes)
    return construir_mascara_desde_df(df_filtros, filtros)


def construir_bloque_resultado(columna_objetivo, correlaciones, serie_objetivo):
    return html.Div(
        [
            html.H4(construir_etiqueta_columna(columna_objetivo)),
            html.Div(
                [
                    construir_tabla_correlacion(correlaciones, construir_etiqueta_columna),
                    construir_tabla_describe(serie_objetivo.dropna()),
                    construir_histograma(serie_objetivo, columna_objetivo, construir_etiqueta_columna),
                ],
                style=RESULTADOS_GRID_STYLE,
            ),
        ],
        style={"marginBottom": "24px"},
    )


def construir_chip_variable(variable):
    return html.Div(
        [
            html.Span(construir_etiqueta_columna(variable)),
            html.Button("Retirar", id={"type": "retirar-variable-btn", "value": variable}, n_clicks=0),
        ],
        style=BADGE_STYLE,
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


def normalizar_lista_unica(valores):
    return sorted(set(valores), key=lambda x: x.lower())


def obtener_freq_desde_relayout(relayout_data):
    if not relayout_data:
        return "1h"

    inicio = relayout_data.get("xaxis.range[0]") or relayout_data.get("xaxis.range", [None, None])[0]
    fin = relayout_data.get("xaxis.range[1]") or relayout_data.get("xaxis.range", [None, None])[1]
    if not inicio or not fin:
        return "1h"

    try:
        inicio_dt = pd.to_datetime(inicio)
        fin_dt = pd.to_datetime(fin)
    except Exception:
        return "1h"

    if inicio_dt is None or fin_dt is None:
        return "1h"
    if pd.isna(inicio_dt) or pd.isna(fin_dt):
        return "1h"

    return "5min" if (fin_dt - inicio_dt).days < 365 else "1h"


def obtener_rango_desde_relayout(relayout_data):
    if not relayout_data:
        return None

    inicio = relayout_data.get("xaxis.range[0]") or relayout_data.get("xaxis.range", [None, None])[0]
    fin = relayout_data.get("xaxis.range[1]") or relayout_data.get("xaxis.range", [None, None])[1]
    if not inicio or not fin:
        return None
    return [inicio, fin]


def obtener_freq_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return "1h"
    return estado_grafico.get("freq", "1h")


def obtener_rango_desde_estado_grafico(estado_grafico):
    if not estado_grafico:
        return None
    return estado_grafico.get("range")


def register_dashboard_callbacks(app):
    @app.callback(
        Output("estado-grafico-store", "data", allow_duplicate=True),
        Input("grafico", "relayoutData"),
        State("estado-grafico-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_estado_grafico(relayout_data, estado_grafico):
        estado_grafico = dict(estado_grafico or {"freq": "1h", "range": None})
        if not relayout_data:
            return estado_grafico

        if relayout_data.get("xaxis.autorange"):
            return {"freq": "1h", "range": None}

        rango = obtener_rango_desde_relayout(relayout_data)
        if rango is None:
            return estado_grafico

        return {
            "freq": obtener_freq_desde_relayout(relayout_data),
            "range": rango,
        }

    @app.callback(
        Output("seleccion-variables-dropdown", "options"),
        Output("seleccion-variables-dropdown", "value"),
        Input("estado-grafico-store", "data"),
        Input("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
    )
    def actualizar_variables_selector(estado_grafico, fase, valor_actual):
        freq = obtener_freq_desde_estado_grafico(estado_grafico)
        opciones = construir_opciones_variables_por_fase(freq, fase, incluir_grupos=True)
        valores_validos = {opcion["value"] for opcion in opciones}
        return opciones, valor_actual if valor_actual in valores_validos else None

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
        Output("variables-seleccionadas-store", "data", allow_duplicate=True),
        Input("anadir-variable-btn", "n_clicks"),
        Input({"type": "retirar-variable-btn", "value": ALL}, "n_clicks"),
        State("estado-grafico-store", "data"),
        State("seleccion-fases-dropdown", "value"),
        State("seleccion-variables-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_variables_agregadas(_, __, estado_grafico, fase, valor_variable, variables_agregadas):
        variables_agregadas = list(variables_agregadas or [])
        disparador = callback_context.triggered_id
        freq = obtener_freq_desde_estado_grafico(estado_grafico)

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
        dataframes = construir_dataframes_para_columnas(freq, columnas_requeridas)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        total = len(df_combinado.index)
        rechazo = construir_mascara_rechazo_desde_df(df_combinado, filtros_guardados)
        eliminadas = int(rechazo.sum()) if rechazo is not None else 0
        porcentaje = (eliminadas / total * 100) if total else 0

        resumen = html.Div(
            f"Muestras eliminadas: {eliminadas} ({porcentaje:.2f}% del dataframe total)."
        )
        return chips, resumen

    @app.callback(
        Output("correlacion-seleccion-checklist", "options"),
        Input("variables-seleccionadas-store", "data"),
    )
    def sincronizar_variables_correlacion(variables_seleccionadas):
        variables = list(variables_seleccionadas or [])
        return [
            {"label": construir_etiqueta_columna(columna), "value": columna}
            for columna in variables
        ]

    @app.callback(
        Output("grafico", "figure"),
        Input("estado-grafico-store", "data"),
        Input("normalizar-checklist", "value"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtros-store", "data"),
    )
    def actualizar_grafico(estado_grafico, normalizar_opciones, variables_seleccionadas, filtros_guardados):
        rango_visible = obtener_rango_desde_estado_grafico(estado_grafico)
        columnas = list(variables_seleccionadas or [])
        if not columnas:
            return go.Figure()

        filtros_guardados = list(filtros_guardados or [])
        columnas_requeridas = columnas + [
            filtro["columna"] for filtro in filtros_guardados if filtro.get("columna")
        ]
        freq = obtener_freq_desde_estado_grafico(estado_grafico)
        dataframes = construir_dataframes_para_columnas(freq, columnas_requeridas)
        df_combinado = combinar_dataframes_por_fase(dataframes)
        mascara = construir_mascara_desde_df(df_combinado, filtros_guardados)
        df_grafico = df_combinado.where(mascara) if mascara is not None else df_combinado

        normalizar = "normalizar" in (normalizar_opciones or [])
        fig = go.Figure()

        for col in columnas:
            if col not in df_grafico.columns:
                continue
            serie = normalizar_serie(df_grafico[col]) if normalizar else df_grafico[col]
            fig.add_trace(
                go.Scatter(
                    x=df_grafico.index,
                    y=serie,
                    mode="lines",
                    name=construir_etiqueta_columna(col),
                    connectgaps=False,
                )
            )

        fig.update_layout(
            title="Evolucion temporal de variables seleccionadas",
            hovermode="x unified",
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            showlegend=True,
            uirevision="grafico-principal",
        )
        if rango_visible is not None:
            fig.update_layout(xaxis_range=rango_visible)
        return fig

    @app.callback(
        Output("correlaciones-container", "children", allow_duplicate=True),
        Input("calcular-correlaciones-btn", "n_clicks"),
        State("correlacion-seleccion-checklist", "value"),
        State("filtros-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_correlaciones(n_clicks, columnas_correlacion, filtros_guardados):
        if not n_clicks or not columnas_correlacion:
            return []

        freq = "1h"
        filtros_guardados = list(filtros_guardados or [])
        mascara_global = construir_mascara_global(freq, filtros_guardados)
        resultados = []

        for columna in columnas_correlacion:
            correlaciones, serie_objetivo = calcular_correlaciones_para_variable(
                freq,
                columna,
                mascara_global,
                separar_valor_columna=separar_valor_columna,
                construir_valor_columna=construir_valor_columna,
            )
            resultados.append(construir_bloque_resultado(columna, correlaciones, serie_objetivo))

        return resultados

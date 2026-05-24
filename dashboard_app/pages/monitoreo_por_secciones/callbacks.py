from dash import ALL, Input, Output, State, callback_context, dcc, html, no_update
import pandas as pd
import plotly.graph_objects as go

from analysis_core.dataset_catalog import obtener_columnas_dataset
from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.callbacks.common import (
    ACCION_RETIRAR_STYLE,
    construir_etiqueta_columna,
    construir_opciones_variables_por_fase,
    expandir_valor_variable,
)
from dashboard_app.domain.semaforo import construir_configuracion_semaforo
from dashboard_app.pages.indicator_utils import formatear_texto
from dashboard_app.pages.monitoreo_por_secciones.domain import (
    MONITOREO_FREQ,
    obtener_rango_monitoreo_serializado,
)
from dashboard_app.pages.monitoreo_por_secciones.layout import (
    EDITOR_VISTA_GUARDADA_OCULTO_STYLE,
    EDITOR_VISTA_GUARDADA_VISIBLE_STYLE,
)
from dashboard_app.pages.semaforos import (
    construir_estado_vacio,
    construir_tabla_semaforos,
)
from dashboard_app.pages.series_temporales.graphing import (
    agrupar_columnas_por_unidad,
    completar_indice_temporal,
    construir_figura_series_temporales,
)
from dashboard_app.pages.series_temporales.views import construir_imagen_fase
from dashboard_app.repositories.saved_views import (
    delete_saved_view,
    upsert_saved_view,
)


RANGO_FIELDS = ("minimo", "maximo", "normal", "normal_sor", "normal_eor")
RANGO_LABELS = {
    "minimo": "Mínimo",
    "maximo": "Máximo",
    "normal": "Normal",
    "normal_sor": "Normal SOR",
    "normal_eor": "Normal EOR",
}

EDITOR_VARIABLES_STYLE = {
    "display": "grid",
    "gap": "12px",
    "overflowX": "auto",
}

EDITOR_VARIABLE_CARD_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(220px, 1.4fr) repeat(5, minmax(96px, 1fr)) auto",
    "minWidth": "860px",
    "gap": "10px",
    "alignItems": "end",
    "padding": "12px",
    "border": "1px solid #d7e3f4",
    "borderRadius": "8px",
    "backgroundColor": "#ffffff",
}

EDITOR_VARIABLE_TITULO_STYLE = {
    "fontWeight": "600",
    "lineHeight": "1.25",
}

EDITOR_VARIABLE_FASE_STYLE = {
    "marginTop": "4px",
    "fontSize": "12px",
    "color": "#6b7280",
}

EDITOR_CAMPO_STYLE = {
    "display": "grid",
    "gap": "4px",
}

EDITOR_LABEL_STYLE = {
    "fontSize": "12px",
    "fontWeight": "600",
    "color": "#4b5563",
}

EDITOR_INPUT_STYLE = {
    "width": "100%",
    "boxSizing": "border-box",
}


def es_id_patron(disparador, tipo):
    return hasattr(disparador, "get") and disparador.get("type") == tipo


def construir_figura_vacia(texto):
    figura = go.Figure()
    annotations = []
    if texto:
        annotations.append(
            {
                "text": texto,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "#6b7280"},
            }
        )
    figura.update_layout(
        height=280,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=annotations,
    )
    return figura


def buscar_vista_por_nombre(nombre, vistas_guardadas):
    return next(
        (
            vista
            for vista in list(vistas_guardadas or [])
            if vista.get("name") == nombre
        ),
        None,
    )


def limpiar_texto(valor):
    texto = str(valor or "").strip()
    return texto or None


def construir_variable_desde_columna(columna):
    if " | " not in str(columna):
        return None
    scope, tag = str(columna).split(" | ", 1)
    return {
        "tag": limpiar_texto(tag),
        "scope": limpiar_texto(scope),
        "descripcion": limpiar_texto(tag),
        "column": str(columna),
        "minimo": None,
        "maximo": None,
        "normal": None,
        "normal_sor": None,
        "normal_eor": None,
    }


def normalizar_variable_editor(variable):
    if isinstance(variable, str):
        return construir_variable_desde_columna(variable)
    if not isinstance(variable, dict):
        return None

    columna = variable.get("column")
    if not columna:
        columna = f"{variable.get('scope')} | {variable.get('tag')}"
    base = construir_variable_desde_columna(columna)
    if base is None:
        return None

    base["descripcion"] = limpiar_texto(variable.get("descripcion")) or base["tag"]
    for campo in RANGO_FIELDS:
        base[campo] = limpiar_texto(variable.get(campo))
    return aplicar_exclusion_rangos(base)


def aplicar_exclusion_rangos(variable):
    normal = limpiar_texto(variable.get("normal"))
    normal_sor = limpiar_texto(variable.get("normal_sor"))
    normal_eor = limpiar_texto(variable.get("normal_eor"))
    if normal:
        variable["normal"] = normal
        variable["normal_sor"] = None
        variable["normal_eor"] = None
    elif normal_sor or normal_eor:
        variable["normal"] = None
        variable["normal_sor"] = normal_sor
        variable["normal_eor"] = normal_eor
    return variable


def normalizar_variables_editor(variables):
    normalizadas = []
    columnas_vistas = set()
    for variable in variables or []:
        normalizada = normalizar_variable_editor(variable)
        if normalizada is None:
            continue
        columna = normalizada["column"]
        if columna in columnas_vistas:
            continue
        columnas_vistas.add(columna)
        normalizadas.append(normalizada)
    return sorted(normalizadas, key=lambda variable: variable["column"].lower())


def actualizar_variables_con_inputs(variables, input_ids, input_values):
    variables_actualizadas = normalizar_variables_editor(variables)
    por_columna = {variable["column"]: variable for variable in variables_actualizadas}
    for input_id, valor in zip(input_ids or [], input_values or []):
        if not isinstance(input_id, dict):
            continue
        columna = input_id.get("column")
        campo = input_id.get("field")
        if columna in por_columna and campo in RANGO_FIELDS:
            por_columna[columna][campo] = limpiar_texto(valor)
    return normalizar_variables_editor(variables_actualizadas)


def construir_campo_rango(variable, campo):
    columna = variable["column"]
    return html.Label(
        [
            html.Span(RANGO_LABELS[campo], style=EDITOR_LABEL_STYLE),
            dcc.Input(
                id={"type": "monitoreo-rango-input", "column": columna, "field": campo},
                type="text",
                value=variable.get(campo),
                disabled=False,
                style=EDITOR_INPUT_STYLE,
            ),
        ],
        style=EDITOR_CAMPO_STYLE,
    )


def construir_editor_variable(variable):
    columna = variable["column"]
    return html.Div(
        [
            html.Div(
                [
                    html.Div(construir_etiqueta_columna(columna), style=EDITOR_VARIABLE_TITULO_STYLE),
                    html.Div(formatear_texto(variable.get("scope"), es_fase=True), style=EDITOR_VARIABLE_FASE_STYLE),
                ]
            ),
            *[construir_campo_rango(variable, campo) for campo in RANGO_FIELDS],
            html.Button(
                "-",
                id={"type": "monitoreo-retirar-variable-btn", "value": columna},
                n_clicks=0,
                style=ACCION_RETIRAR_STYLE,
            ),
        ],
        style=EDITOR_VARIABLE_CARD_STYLE,
    )


def validar_pares_sor_eor(variables):
    invalidas = []
    for variable in variables:
        tiene_sor = limpiar_texto(variable.get("normal_sor")) is not None
        tiene_eor = limpiar_texto(variable.get("normal_eor")) is not None
        if tiene_sor != tiene_eor:
            invalidas.append(variable.get("tag") or variable.get("column"))
    return invalidas


def register_callbacks(app):
    @app.callback(
        Output("monitoreo-fase-imagen-container", "children"),
        Input("monitoreo-fase-dropdown", "value"),
    )
    def actualizar_imagen_fase(fase):
        return construir_imagen_fase(fase)

    @app.callback(
        Output("monitoreo-variable-dropdown", "options"),
        Output("monitoreo-variable-dropdown", "value"),
        Input("monitoreo-fase-dropdown", "value"),
        State("monitoreo-variable-dropdown", "value"),
    )
    def actualizar_variables_selector(fase, valor_actual):
        opciones = construir_opciones_variables_por_fase(
            MONITOREO_FREQ,
            fase,
            incluir_grupos=True,
        )
        valores_validos = {opcion["value"] for opcion in opciones}
        return opciones, valor_actual if valor_actual in valores_validos else None

    @app.callback(
        Output("monitoreo-editor-variables-store", "data", allow_duplicate=True),
        Input("monitoreo-anadir-variable-btn", "n_clicks"),
        Input({"type": "monitoreo-retirar-variable-btn", "value": ALL}, "n_clicks"),
        State("monitoreo-fase-dropdown", "value"),
        State("monitoreo-variable-dropdown", "value"),
        State("monitoreo-editor-variables-store", "data"),
        prevent_initial_call=True,
    )
    def actualizar_variables_editor(
        _anadir_clicks,
        clicks_retirar,
        fase,
        valor_variable,
        variables_agregadas,
    ):
        variables_agregadas = normalizar_variables_editor(variables_agregadas)
        disparador = callback_context.triggered_id

        if disparador == "monitoreo-anadir-variable-btn":
            nuevas = expandir_valor_variable(MONITOREO_FREQ, fase, valor_variable)
            variables_por_columna = {
                variable["column"]: variable
                for variable in variables_agregadas
            }
            for columna in nuevas:
                if columna not in variables_por_columna:
                    variable = construir_variable_desde_columna(columna)
                    if variable is not None:
                        variables_por_columna[columna] = variable
            return normalizar_variables_editor(variables_por_columna.values())

        if es_id_patron(disparador, "monitoreo-retirar-variable-btn"):
            if not any((clicks_retirar or [])):
                return variables_agregadas
            columna = disparador["value"]
            return [
                variable
                for variable in variables_agregadas
                if variable.get("column") != columna
            ]

        return variables_agregadas

    @app.callback(
        Output("monitoreo-editor-variables-store", "data", allow_duplicate=True),
        Input({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "value"),
        State({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "id"),
        State("monitoreo-editor-variables-store", "data"),
        prevent_initial_call=True,
    )
    def sincronizar_rangos_editor(input_values, input_ids, variables_agregadas):
        return actualizar_variables_con_inputs(variables_agregadas, input_ids, input_values)

    @app.callback(
        Output({"type": "monitoreo-rango-input", "column": ALL, "field": "normal"}, "disabled"),
        Output({"type": "monitoreo-rango-input", "column": ALL, "field": "normal_sor"}, "disabled"),
        Output({"type": "monitoreo-rango-input", "column": ALL, "field": "normal_eor"}, "disabled"),
        Input({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "value"),
        State({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "id"),
        prevent_initial_call=False,
    )
    def actualizar_disponibilidad_rangos(input_values, input_ids):
        valores_por_columna = {}
        for input_id, valor in zip(input_ids or [], input_values or []):
            if not isinstance(input_id, dict):
                continue
            columna = input_id.get("column")
            campo = input_id.get("field")
            valores_por_columna.setdefault(columna, {})[campo] = limpiar_texto(valor)

        columnas_normal = [
            input_id.get("column")
            for input_id in input_ids or []
            if isinstance(input_id, dict) and input_id.get("field") == "normal"
        ]
        columnas_sor = [
            input_id.get("column")
            for input_id in input_ids or []
            if isinstance(input_id, dict) and input_id.get("field") == "normal_sor"
        ]
        columnas_eor = [
            input_id.get("column")
            for input_id in input_ids or []
            if isinstance(input_id, dict) and input_id.get("field") == "normal_eor"
        ]

        normal_disabled = [
            bool(
                valores_por_columna.get(columna, {}).get("normal_sor")
                or valores_por_columna.get(columna, {}).get("normal_eor")
            )
            for columna in columnas_normal
        ]
        sor_disabled = [
            bool(valores_por_columna.get(columna, {}).get("normal"))
            for columna in columnas_sor
        ]
        eor_disabled = [
            bool(valores_por_columna.get(columna, {}).get("normal"))
            for columna in columnas_eor
        ]
        return normal_disabled, sor_disabled, eor_disabled

    @app.callback(
        Output("monitoreo-editor-variables-container", "children"),
        Input("monitoreo-editor-variables-store", "data"),
    )
    def mostrar_variables_editor(variables_agregadas):
        variables_agregadas = normalizar_variables_editor(variables_agregadas)
        if not variables_agregadas:
            return html.Div("No hay variables añadidas.")
        return html.Div(
            [
                construir_editor_variable(variable)
                for variable in variables_agregadas
            ],
            style=EDITOR_VARIABLES_STYLE,
        )

    @app.callback(
        Output("monitoreo-editor-store", "data", allow_duplicate=True),
        Output("monitoreo-vista-nombre-input", "value", allow_duplicate=True),
        Output("monitoreo-editor-variables-store", "data", allow_duplicate=True),
        Output("monitoreo-vista-estado", "children", allow_duplicate=True),
        Input("monitoreo-crear-vista-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def mostrar_editor_vista_guardada(_mostrar_clicks):
        return {"visible": True}, "", [], ""

    @app.callback(
        Output("monitoreo-editor-container", "style"),
        Input("monitoreo-editor-store", "data"),
    )
    def actualizar_visibilidad_editor_vista_guardada(estado_editor):
        visible = bool((estado_editor or {}).get("visible"))
        if visible:
            return EDITOR_VISTA_GUARDADA_VISIBLE_STYLE
        return EDITOR_VISTA_GUARDADA_OCULTO_STYLE

    @app.callback(
        Output("monitoreo-vistas-store", "data", allow_duplicate=True),
        Output("monitoreo-vistas-dropdown", "value", allow_duplicate=True),
        Output("monitoreo-vista-nombre-input", "value"),
        Output("monitoreo-editor-store", "data", allow_duplicate=True),
        Output("monitoreo-editor-variables-store", "data"),
        Output("monitoreo-vista-estado", "children"),
        Input("monitoreo-guardar-vista-btn", "n_clicks"),
        Input("monitoreo-eliminar-vista-btn", "n_clicks"),
        State("monitoreo-vista-nombre-input", "value"),
        State("monitoreo-vistas-dropdown", "value"),
        State("monitoreo-editor-variables-store", "data"),
        State("monitoreo-vistas-store", "data"),
        State({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "value"),
        State({"type": "monitoreo-rango-input", "column": ALL, "field": ALL}, "id"),
        prevent_initial_call=True,
    )
    def gestionar_vistas_guardadas(
        _guardar_clicks,
        _eliminar_clicks,
        nombre_vista,
        vista_seleccionada,
        variables_agregadas,
        vistas_guardadas,
        input_values,
        input_ids,
    ):
        disparador = callback_context.triggered_id
        nombre_limpio = str(nombre_vista or "").strip()
        variables_agregadas = actualizar_variables_con_inputs(
            variables_agregadas,
            input_ids,
            input_values,
        )
        vistas_guardadas = list(vistas_guardadas or [])

        if disparador == "monitoreo-guardar-vista-btn":
            if not variables_agregadas:
                return (
                    no_update,
                    no_update,
                    nombre_vista,
                    no_update,
                    variables_agregadas,
                    "Selecciona al menos una variable antes de guardar la vista.",
                )
            if not nombre_limpio:
                return (
                    no_update,
                    no_update,
                    nombre_vista,
                    no_update,
                    variables_agregadas,
                    "Escribe un nombre para guardar la vista.",
                )

            sor_eor_incompletas = validar_pares_sor_eor(variables_agregadas)
            if sor_eor_incompletas:
                return (
                    no_update,
                    no_update,
                    nombre_vista,
                    no_update,
                    variables_agregadas,
                    "Completa Normal SOR y Normal EOR para: "
                    + ", ".join(sor_eor_incompletas)
                    + ".",
                )

            variables_definidas = normalizar_variables_editor(variables_agregadas)
            vistas_actualizadas = upsert_saved_view(nombre_limpio, variables_definidas)

            sin_rangos = [
                variable.get("tag")
                for variable in variables_definidas
                if not construir_configuracion_semaforo(variable).get("segmentos")
            ]
            mensaje = f"Vista '{nombre_limpio}' guardada correctamente."
            if sin_rangos:
                mensaje += " Algunas variables quedaron sin configuración válida para semáforo."

            return (
                vistas_actualizadas,
                nombre_limpio,
                "",
                {"visible": False},
                [],
                mensaje,
            )

        if disparador == "monitoreo-eliminar-vista-btn":
            if not vista_seleccionada:
                return (
                    no_update,
                    no_update,
                    nombre_vista,
                    no_update,
                    variables_agregadas,
                    "Selecciona una vista guardada para eliminarla.",
                )

            vistas_actualizadas = delete_saved_view(vista_seleccionada)
            return (
                vistas_actualizadas,
                None,
                "",
                {"visible": False},
                [],
                f"Vista '{vista_seleccionada}' eliminada.",
            )

        return no_update, no_update, nombre_vista, no_update, variables_agregadas, no_update

    @app.callback(
        Output("monitoreo-vistas-dropdown", "options"),
        Input("monitoreo-vistas-store", "data"),
    )
    def sincronizar_opciones_vistas_guardadas(vistas_guardadas):
        return [
            {"label": vista["name"], "value": vista["name"]}
            for vista in list(vistas_guardadas or [])
        ]

    @app.callback(
        Output("monitoreo-grafico", "figure"),
        Output("monitoreo-graficas-por-unidad", "children"),
        Output("monitoreo-semaforos-container", "children"),
        Input("monitoreo-vistas-dropdown", "value"),
        Input("monitoreo-vistas-store", "data"),
    )
    def actualizar_monitoreo(vista_guardada, vistas_guardadas):
        vista = buscar_vista_por_nombre(vista_guardada, vistas_guardadas)
        if vista is None:
            return (
                construir_figura_vacia(None),
                [],
                [],
            )

        rango_visible = obtener_rango_monitoreo_serializado()
        columnas_disponibles = set(obtener_columnas_dataset(MONITOREO_FREQ))
        columnas_vista = [
            variable.get("column")
            for variable in vista.get("variables") or []
            if variable.get("column")
        ]
        columnas_presentes = [columna for columna in columnas_vista if columna in columnas_disponibles]
        dataframe = (
            load_combined_dataset(
                MONITOREO_FREQ,
                columns=columnas_presentes,
                time_range=rango_visible,
            )
            if columnas_presentes
            else pd.DataFrame()
        )
        dataframe = completar_indice_temporal(
            dataframe,
            MONITOREO_FREQ,
            rango_tiempo=rango_visible,
        )

        if columnas_presentes:
            figura_principal = construir_figura_series_temporales(
                dataframe,
                columnas_presentes,
                normalizar=False,
                multi_eje=True,
                uirevision=f"monitoreo-principal::{vista['name']}",
                rango_visible=rango_visible,
            )
        else:
            figura_principal = construir_figura_vacia(
                "La vista seleccionada no contiene variables disponibles en el dataset."
            )

        grupos_unidad = agrupar_columnas_por_unidad(columnas_presentes, normalizar=False)
        if not columnas_presentes:
            graficas_por_unidad = construir_estado_vacio("La vista seleccionada no contiene variables disponibles en el dataset.")
        elif len(grupos_unidad) <= 1:
            graficas_por_unidad = []
        else:
            graficas_por_unidad = []
            for unidad, columnas_grupo in grupos_unidad.items():
                figura_grupo = construir_figura_series_temporales(
                    dataframe,
                    columnas_grupo,
                    normalizar=False,
                    multi_eje=False,
                    uirevision=f"monitoreo-unidad::{vista['name']}::{unidad}",
                    rango_visible=rango_visible,
                )
                graficas_por_unidad.append(
                    html.Div(
                        [
                            html.H3(f"Variables con unidad: {unidad}"),
                            dcc.Graph(figure=figura_grupo),
                        ],
                        style={"marginTop": "20px"},
                    )
                )

        semaforos = construir_tabla_semaforos(vista, dataframe, columnas_disponibles)
        return figura_principal, graficas_por_unidad, semaforos

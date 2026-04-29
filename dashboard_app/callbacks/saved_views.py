from dash import Input, Output, State, callback_context, no_update

from dashboard_app.repositories.saved_views import (
    delete_saved_view,
    upsert_saved_view,
)


EDITOR_VISTA_GUARDADA_VISIBLE_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(220px, 360px) auto",
    "gap": "12px",
    "alignItems": "center",
    "marginBottom": "16px",
}

EDITOR_VISTA_GUARDADA_OCULTO_STYLE = {
    **EDITOR_VISTA_GUARDADA_VISIBLE_STYLE,
    "display": "none",
}


def register_callbacks(app):
    @app.callback(
        Output("editor-vista-guardada-store", "data", allow_duplicate=True),
        Output("nombre-vista-guardada-input", "value", allow_duplicate=True),
        Output("vista-guardada-estado", "children", allow_duplicate=True),
        Input("mostrar-guardar-vista-btn", "n_clicks"),
        State("vistas-guardadas-dropdown", "value"),
        prevent_initial_call=True,
    )
    def mostrar_editor_vista_guardada(_mostrar_clicks, vista_seleccionada):
        return {"visible": True}, vista_seleccionada or "", ""

    @app.callback(
        Output("editor-vista-guardada-container", "style"),
        Input("editor-vista-guardada-store", "data"),
    )
    def actualizar_visibilidad_editor_vista_guardada(estado_editor):
        visible = bool((estado_editor or {}).get("visible"))
        if visible:
            return EDITOR_VISTA_GUARDADA_VISIBLE_STYLE
        return EDITOR_VISTA_GUARDADA_OCULTO_STYLE

    @app.callback(
        Output("vistas-guardadas-store", "data", allow_duplicate=True),
        Output("vistas-guardadas-dropdown", "value", allow_duplicate=True),
        Output("nombre-vista-guardada-input", "value"),
        Output("editor-vista-guardada-store", "data", allow_duplicate=True),
        Output("vista-guardada-estado", "children"),
        Input("guardar-vista-btn", "n_clicks"),
        Input("eliminar-vista-btn", "n_clicks"),
        State("nombre-vista-guardada-input", "value"),
        State("vistas-guardadas-dropdown", "value"),
        State("variables-seleccionadas-store", "data"),
        State("vistas-guardadas-scope-store", "data"),
        prevent_initial_call=True,
    )
    def gestionar_vistas_guardadas(
        _guardar_clicks,
        _eliminar_clicks,
        nombre_vista,
        vista_seleccionada,
        variables_agregadas,
        views_scope,
    ):
        disparador = callback_context.triggered_id
        nombre_limpio = str(nombre_vista or "").strip()
        variables_agregadas = list(variables_agregadas or [])

        if disparador == "guardar-vista-btn":
            if not variables_agregadas:
                return no_update, no_update, nombre_vista, no_update, "Selecciona al menos una variable antes de guardar la vista."
            if not nombre_limpio:
                return no_update, no_update, nombre_vista, no_update, "Escribe un nombre para guardar la vista."

            vistas_actualizadas = upsert_saved_view(nombre_limpio, variables_agregadas, views_scope)
            return (
                vistas_actualizadas,
                nombre_limpio,
                "",
                {"visible": False},
                f"Vista '{nombre_limpio}' guardada correctamente.",
            )

        if disparador == "eliminar-vista-btn":
            if not vista_seleccionada:
                return no_update, no_update, nombre_vista, no_update, "Selecciona una vista guardada para eliminarla."

            vistas_actualizadas = delete_saved_view(vista_seleccionada, views_scope)
            return (
                vistas_actualizadas,
                None,
                "",
                {"visible": False},
                f"Vista '{vista_seleccionada}' eliminada.",
            )

        return no_update, no_update, nombre_vista, no_update, no_update

    @app.callback(
        Output("vistas-guardadas-dropdown", "options"),
        Input("vistas-guardadas-store", "data"),
    )
    def sincronizar_opciones_vistas_guardadas(vistas_guardadas):
        vistas_guardadas = list(vistas_guardadas or [])
        return [
            {"label": vista["name"], "value": vista["name"]}
            for vista in vistas_guardadas
        ]

    @app.callback(
        Output("nombre-vista-guardada-input", "value", allow_duplicate=True),
        Input("vistas-guardadas-dropdown", "value"),
        prevent_initial_call=True,
    )
    def reflejar_nombre_vista_guardada(vista_seleccionada):
        return vista_seleccionada or ""

    @app.callback(
        Output("variables-seleccionadas-store", "data", allow_duplicate=True),
        Output("vista-guardada-estado", "children", allow_duplicate=True),
        Input("vistas-guardadas-dropdown", "value"),
        State("vistas-guardadas-store", "data"),
        prevent_initial_call=True,
    )
    def aplicar_vista_guardada(vista_guardada, vistas_guardadas):
        if not vista_guardada:
            return no_update, no_update

        vistas_guardadas = list(vistas_guardadas or [])
        vista = next((item for item in vistas_guardadas if item.get("name") == vista_guardada), None)
        if vista is None:
            return no_update, "La vista seleccionada ya no existe en el archivo de vistas guardadas."

        return list(vista.get("variables") or []), f"Vista '{vista_guardada}' aplicada."

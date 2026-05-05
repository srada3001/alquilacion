from dash import Input, Output

from dashboard_app.pages.bombas.layout import cargar_bombas, construir_tabla_bombas


def register_callbacks(app):
    @app.callback(
        Output("bombas-tabla-container", "children"),
        Input("bombas-fases-dropdown", "value"),
    )
    def actualizar_tabla_bombas(fases_seleccionadas):
        bombas = cargar_bombas()
        fases = list(fases_seleccionadas or [])
        if fases:
            bombas = bombas.loc[bombas["fase"].isin(fases)].copy()
        return construir_tabla_bombas(bombas)

from dash import Input, Output

from dashboard_app.pages.valvulas.layout import cargar_valvulas, construir_tabla_valvulas


def register_callbacks(app):
    @app.callback(
        Output("valvulas-tabla-container", "children"),
        Input("valvulas-fases-dropdown", "value"),
    )
    def actualizar_tabla_valvulas(fases_seleccionadas):
        valvulas = cargar_valvulas()
        fases = list(fases_seleccionadas or [])
        if fases:
            valvulas = valvulas.loc[valvulas["fase"].isin(fases)].copy()
        return construir_tabla_valvulas(valvulas)

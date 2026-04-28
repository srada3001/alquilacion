from dash import Input, Output, html
import pandas as pd

from dashboard_app.callbacks.common import construir_etiqueta_columna
from dashboard_app.pages.series_temporales.callbacks import cargar_dataframe_filtrado
from dashboard_app.pages.series_temporales.views import construir_bloque_comparacion_variables


def _iterar_pares(variables):
    for indice in range(0, len(variables), 2):
        yield variables[indice : indice + 2]


def register_callbacks(app):
    @app.callback(
        Output("pair-graphs-container", "children"),
        Input("estado-grafico-store", "data"),
        Input("variables-seleccionadas-store", "data"),
        Input("filtros-store", "data"),
        Input("modo-operacion-radio", "value"),
        Input("filtro-arranque-dropdown", "value"),
        Input("filtro-parada-dropdown", "value"),
        Input("filtro-operacion-dropdown", "value"),
    )
    def actualizar_comparaciones_por_pares(
        estado_grafico,
        variables_seleccionadas,
        filtros_guardados,
        modo_operacion,
        arranque_id,
        parada_id,
        operacion_id,
    ):
        variables = list(variables_seleccionadas or [])
        if len(variables) < 2:
            return html.Div(
                "Selecciona dos variables para generar la primera comparacion."
            )

        pares_completos = [par for par in _iterar_pares(variables) if len(par) == 2]
        if not pares_completos:
            return html.Div(
                "Selecciona dos variables para generar la primera comparacion."
            )

        columnas = [columna for par in pares_completos for columna in par]
        df_filtrado = cargar_dataframe_filtrado(
            estado_grafico,
            columnas,
            filtros_guardados,
            modo_operacion,
            arranque_id,
            parada_id,
            operacion_id,
        )

        bloques = []
        for indice, (variable_x, variable_y) in enumerate(pares_completos, start=1):
            if variable_x not in df_filtrado.columns or variable_y not in df_filtrado.columns:
                bloques.append(
                    html.Div(
                        (
                            f"Comparacion {indice}: no se pudieron cargar "
                            f"{construir_etiqueta_columna(variable_x)} y "
                            f"{construir_etiqueta_columna(variable_y)}."
                        ),
                        style={"marginBottom": "24px"},
                    )
                )
                continue

            pares_validos = df_filtrado[[variable_x, variable_y]].dropna()
            if pares_validos.empty:
                bloques.append(
                    html.Div(
                        (
                            f"Comparacion {indice}: no hay datos disponibles para "
                            f"{construir_etiqueta_columna(variable_x)} y "
                            f"{construir_etiqueta_columna(variable_y)} con los filtros actuales."
                        ),
                        style={"marginBottom": "24px"},
                    )
                )
                continue

            correlacion = pares_validos[variable_x].corr(pares_validos[variable_y])
            if pd.isna(correlacion):
                correlacion = None

            bloques.append(
                construir_bloque_comparacion_variables(
                    pares_validos,
                    variable_x,
                    variable_y,
                    correlacion=correlacion,
                    titulo=f"Comparacion {indice}",
                )
            )

        if len(variables) % 2 == 1:
            bloques.append(
                html.Div(
                    "Selecciona una variable adicional para completar la siguiente comparacion.",
                    style={"marginBottom": "24px", "fontStyle": "italic"},
                )
            )

        return bloques

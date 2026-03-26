from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go

from dashboard_app.data import cargar_df_columnas, obtener_columnas_numericas_fase, obtener_fases


def construir_tabla_simple(titulo, filas):
    return html.Div([html.H5(titulo), html.Table(filas)])


def construir_tabla_describe(serie):
    descripcion = serie.describe()
    filas = [html.Tr([html.Th("Estadistica"), html.Th("Valor")])]

    for indice, valor in descripcion.items():
        texto_valor = f"{valor:.4f}" if isinstance(valor, (int, float)) else str(valor)
        filas.append(html.Tr([html.Td(str(indice)), html.Td(texto_valor)]))

    return construir_tabla_simple("Descripcion estadistica", filas)


def construir_tabla_correlacion(correlaciones, etiquetar_columna):
    filas = [html.Tr([html.Th("Variable"), html.Th("Correlacion")])]

    for variable, valor in correlaciones.items():
        filas.append(
            html.Tr(
                [
                    html.Td(etiquetar_columna(variable)),
                    html.Td(f"{valor:.4f}"),
                ]
            )
        )

    return construir_tabla_simple("Correlaciones lineales", filas)


def construir_histograma(serie, columna_objetivo, etiquetar_columna):
    figura = go.Figure(
        data=[
            go.Histogram(
                x=serie.dropna(),
                nbinsx=30,
                name=etiquetar_columna(columna_objetivo),
            )
        ]
    )
    figura.update_layout(
        title="Histograma",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return dcc.Graph(figure=figura, config={"displayModeBar": False})


def calcular_correlaciones_para_variable(
    freq,
    columna_objetivo,
    mascara_global,
    separar_valor_columna,
    construir_valor_columna,
):
    correlaciones = []
    fase_objetivo, nombre_objetivo = separar_valor_columna(columna_objetivo)
    df_objetivo = cargar_df_columnas(fase_objetivo, freq, [nombre_objetivo])
    serie_objetivo = df_objetivo[nombre_objetivo]

    if mascara_global is not None:
        serie_objetivo = serie_objetivo.loc[
            mascara_global.reindex(serie_objetivo.index, fill_value=False)
        ]

    for fase in obtener_fases():
        columnas_numericas = sorted(obtener_columnas_numericas_fase(fase, freq))
        if not columnas_numericas:
            continue

        df_fase = cargar_df_columnas(fase, freq, columnas_numericas)
        if mascara_global is not None:
            mascara_fase = mascara_global.reindex(df_fase.index, fill_value=False)
            df_fase = df_fase.loc[mascara_fase]

        if df_fase.empty or serie_objetivo.empty:
            continue

        correlacion_fase = df_fase.corrwith(serie_objetivo)
        correlacion_fase.index = [
            construir_valor_columna(fase, columna)
            for columna in correlacion_fase.index
        ]
        correlaciones.append(correlacion_fase.dropna())

    if not correlaciones:
        return pd.Series(dtype=float), serie_objetivo

    correlaciones_totales = pd.concat(correlaciones).sort_values(ascending=False)
    correlaciones_totales = correlaciones_totales.drop(labels=[columna_objetivo], errors="ignore")
    return correlaciones_totales, serie_objetivo

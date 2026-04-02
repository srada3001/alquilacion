from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.data import obtener_columnas_numericas_dataset

def construir_tabla_describe(serie):
    descripcion = serie.describe()
    filas = [html.Tr([html.Th("Estadistica"), html.Th("Valor")])]

    for indice, valor in descripcion.items():
        texto_valor = f"{valor:.4f}" if isinstance(valor, (int, float)) else str(valor)
        filas.append(html.Tr([html.Td(str(indice)), html.Td(texto_valor)]))

    return html.Div([html.Table(filas)])


def construir_tabla_correlacion(correlaciones, etiquetar_columna):
    correlaciones_filtradas = correlaciones[correlaciones.abs() >= 0.05]
    correlaciones_filtradas = correlaciones_filtradas.reindex(
        correlaciones_filtradas.abs().sort_values(ascending=False).index
    )

    filas = [
        html.Tr(
            [
                html.Th("Variable"),
                html.Th("Correlacion"),
                html.Th("Variable"),
                html.Th("Correlacion"),
            ]
        )
    ]

    items = list(correlaciones_filtradas.items())
    for i in range(0, len(items), 2):
        celdas = []
        for variable, valor in items[i:i + 2]:
            celdas.extend(
                [
                    html.Td(etiquetar_columna(variable)),
                    html.Td(f"{valor:.4f}"),
                ]
            )
        while len(celdas) < 4:
            celdas.extend([html.Td(""), html.Td("")])
        filas.append(html.Tr(celdas))

    return html.Div(
        [
            html.P(
                "Se presentan las correlaciones lineales con magnitud superior a 0.05. "
                "El orden esta dado por la magnitud y es independiente del signo."
            ),
            html.Table(filas),
        ]
    )


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
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return dcc.Graph(figure=figura, config={"displayModeBar": False})


def calcular_correlaciones_para_variable(
    freq,
    columna_objetivo,
    mascara_global,
):
    columnas_numericas = obtener_columnas_numericas_dataset(freq)
    if columna_objetivo not in columnas_numericas:
        columnas_numericas.append(columna_objetivo)

    df_numerico = load_combined_dataset(freq, columns=columnas_numericas)
    if df_numerico.empty or columna_objetivo not in df_numerico.columns:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    serie_objetivo = df_numerico[columna_objetivo]

    if mascara_global is not None:
        mascara = mascara_global.reindex(df_numerico.index, fill_value=False)
        df_numerico = df_numerico.loc[mascara]
        serie_objetivo = serie_objetivo.loc[mascara]

    if df_numerico.empty or serie_objetivo.empty:
        return pd.Series(dtype=float), serie_objetivo

    correlaciones_totales = df_numerico.corrwith(serie_objetivo).dropna().sort_values(ascending=False)
    correlaciones_totales = correlaciones_totales.drop(labels=[columna_objetivo], errors="ignore")
    return correlaciones_totales, serie_objetivo

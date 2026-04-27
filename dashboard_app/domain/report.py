from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import numpy as np

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
    correlaciones_filtradas = correlaciones[correlaciones.abs() >= 0.2]
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
                "Se presentan las correlaciones lineales con magnitud superior a 0.2. "
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


def construir_grafico_dispersion(
    df_numerico,
    columna_objetivo,
    columna_relacion,
    etiquetar_columna,
):
    columnas = [columna_objetivo, columna_relacion]
    pares = df_numerico[columnas].dropna()
    if pares.empty:
        return html.Div("No hay suficientes datos para construir la dispersion.")

    figura = go.Figure()
    figura.add_trace(
        go.Scattergl(
            x=pares[columna_relacion],
            y=pares[columna_objetivo],
            mode="markers",
            marker=dict(size=6, opacity=0.45),
            name="Muestras",
        )
    )

    if len(pares) >= 2:
        coeficientes = np.polyfit(
            pares[columna_relacion].to_numpy(),
            pares[columna_objetivo].to_numpy(),
            1,
        )
        x_linea = np.linspace(
            pares[columna_relacion].min(),
            pares[columna_relacion].max(),
            100,
        )
        y_linea = coeficientes[0] * x_linea + coeficientes[1]
        figura.add_trace(
            go.Scatter(
                x=x_linea,
                y=y_linea,
                mode="lines",
                name="Tendencia",
            )
        )

    figura.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        xaxis_title=etiquetar_columna(columna_relacion),
        yaxis_title=etiquetar_columna(columna_objetivo),
    )
    return dcc.Graph(figure=figura, config={"displayModeBar": False})


def obtener_top_variables_correlacion(correlaciones, top_n=4):
    if correlaciones is None or correlaciones.empty:
        return []
    return (
        correlaciones.abs()
        .sort_values(ascending=False)
        .head(top_n)
        .index.tolist()
    )


def construir_boxplot_relacion(
    df_numerico,
    columna_objetivo,
    columna_relacion,
    etiquetar_columna,
):
    columnas = [columna_objetivo, columna_relacion]
    pares = df_numerico[columnas].dropna()
    if pares.empty:
        return html.Div("No hay suficientes datos para construir el boxplot.")

    cuartiles = pares[columna_relacion].quantile([0.25, 0.75]).to_list()
    grupos = [
        ("Bajo", pares[pares[columna_relacion] <= cuartiles[0]][columna_objetivo]),
        (
            "Medio",
            pares[
                (pares[columna_relacion] > cuartiles[0])
                & (pares[columna_relacion] <= cuartiles[1])
            ][columna_objetivo],
        ),
        ("Alto", pares[pares[columna_relacion] > cuartiles[1]][columna_objetivo]),
    ]

    figura = go.Figure()
    for etiqueta, grupo in grupos:
        grupo = grupo.dropna()
        if grupo.empty:
            continue
        figura.add_trace(
            go.Box(
                y=grupo,
                name=etiqueta,
                boxpoints=False,
            )
        )

    if not figura.data:
        return html.Div("No hay suficientes datos para construir el boxplot.")

    figura.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        yaxis_title=etiquetar_columna(columna_objetivo),
        xaxis_title=etiquetar_columna(columna_relacion),
        showlegend=False,
    )
    return dcc.Graph(figure=figura, config={"displayModeBar": False})


def construir_bloque_dispersiones(df_numerico, columna_objetivo, correlaciones, etiquetar_columna, top_n=4):
    top_variables = obtener_top_variables_correlacion(correlaciones, top_n=top_n)
    if not top_variables:
        return html.Div("No hay suficientes correlaciones para mostrar dispersiones.")

    return html.Div(
        [
            html.Div(
                [
                    html.H3(
                        f"{etiquetar_columna(variable)} (r={correlaciones[variable]:.4f})"
                    ),
                    construir_grafico_dispersion(
                        df_numerico,
                        columna_objetivo,
                        variable,
                        etiquetar_columna,
                    ),
                ]
            )
            for variable in top_variables
        ]
    )


def construir_boxplot_relaciones(df_numerico, columna_objetivo, correlaciones, etiquetar_columna, top_n=4):
    top_variables = obtener_top_variables_correlacion(correlaciones, top_n=top_n)
    if not top_variables:
        return html.Div("No hay suficientes correlaciones para mostrar boxplots.")

    figura = go.Figure()
    for variable in top_variables:
        pares = df_numerico[[columna_objetivo, variable]].dropna()
        if pares.empty:
            continue

        cuartiles = pares[variable].quantile([0.25, 0.5, 0.75]).to_list()
        etiquetas = [
            f"{etiquetar_columna(variable)} | Bajo",
            f"{etiquetar_columna(variable)} | Medio",
            f"{etiquetar_columna(variable)} | Alto",
        ]

        grupos = [
            pares[pares[variable] <= cuartiles[0]][columna_objetivo],
            pares[(pares[variable] > cuartiles[0]) & (pares[variable] <= cuartiles[2])][columna_objetivo],
            pares[pares[variable] > cuartiles[2]][columna_objetivo],
        ]

        for etiqueta, grupo in zip(etiquetas, grupos):
            grupo = grupo.dropna()
            if grupo.empty:
                continue
            figura.add_trace(
                go.Box(
                    y=grupo,
                    name=etiqueta,
                    boxpoints=False,
                )
            )

    if not figura.data:
        return html.Div("No hay suficientes datos para construir boxplots.")

    figura.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=420,
        yaxis_title=etiquetar_columna(columna_objetivo),
        xaxis=dict(showticklabels=False),
        showlegend=True,
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
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.DataFrame()

    serie_objetivo = df_numerico[columna_objetivo]

    if mascara_global is not None:
        mascara = mascara_global.reindex(df_numerico.index, fill_value=False)
        df_numerico = df_numerico.loc[mascara]
        serie_objetivo = serie_objetivo.loc[mascara]

    if df_numerico.empty or serie_objetivo.empty:
        return pd.Series(dtype=float), serie_objetivo, df_numerico

    correlaciones_totales = df_numerico.corrwith(serie_objetivo).dropna().sort_values(ascending=False)
    correlaciones_totales = correlaciones_totales.drop(labels=[columna_objetivo], errors="ignore")
    return correlaciones_totales, serie_objetivo, df_numerico

from dash import Input, Output, dcc, html
import plotly.graph_objects as go
import pandas as pd
import re
import unicodedata

from dashboard_app.callbacks.common import (
    construir_etiqueta_columna,
)
from dashboard_app.repositories.analysis_cache import (
    get_precomputed_analysis_columns,
    load_precomputed_analysis_result,
)


ANALISIS_PROFUNDO_STACK_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr)",
    "gap": "16px",
    "alignItems": "start",
}

ANALISIS_PROFUNDO_DISPONIBILIDAD_MENSAJE = (
    "Solo disponible para Operación completa, arranques y operaciones sin filtros extra."
)

VARIABLES_INTERES = [
    ("TI 2105", ["debutanizadora_y_tratamiento_de_alquilato | TI-2105"]),
    ("PI 2108", ["debutanizadora_y_tratamiento_de_alquilato | PI-2108"]),
    ("PI 2124", ["debutanizadora_y_tratamiento_de_alquilato | PI-2124", "debutanizadora_y_tratamiento_de_alquilato | PIC-2124"]),
    ("TI 2101", ["debutanizadora_y_tratamiento_de_alquilato | TI-2101"]),
    ("TIC 2103", ["debutanizadora_y_tratamiento_de_alquilato | TIC-2103"]),
    ("TI 2102", ["debutanizadora_y_tratamiento_de_alquilato | TI-2102"]),
    ("FIC 2112", ["debutanizadora_y_tratamiento_de_alquilato | FIC-2112"]),
    ("TIC 2104", ["debutanizadora_y_tratamiento_de_alquilato | TIC-2104", "debutanizadora_y_tratamiento_de_alquilato | TI-2104"]),
    ("FIC 1047", ["reactor_de_alquilacion | FIC-1047", "horno | FIC-1047-F-1-ISOBUTANO"]),
    ("FIC 1059 C", ["reactor_de_alquilacion | FIC-1059C", "lab_isobutano_reciclo | FIC-1059C Olefinas 1"]),
    ("FIC 1903 C", ["reactor_de_alquilacion | FIC-1903C", "lab_isobutano_reciclo | FIC-1903C-Olefinas 2", "horno | FIC-1903C-F-2-OLEFINAS"]),
    ("Relacion isobutano / olefina", ["lab_isobutano_reciclo | Relacion 1 Ol/iso", "lab_isobutano_reciclo | Relacion 2 Ol/iso"]),
    ("TIC 1091", ["isostripper | TIC-1091"]),
    ("TI 1521", ["horno | TI-1521"]),
    ("TI 1098", ["isostripper | TI-1098"]),
    ("PI 1092 B", ["isostripper | PI-1092B"]),
    ("TI 1109", ["isostripper | TI-1109"]),
    ("TI 1497", ["horno | TI-1497", "isostripper | TI-1497"]),
    ("FIC 2100", ["debutanizadora_y_tratamiento_de_alquilato | FIC-2100", "isostripper | FIC-2100"]),
    ("TI 1096", ["isostripper | TI-1096"]),
    ("FIC 2319", ["isostripper | FIC-2319"]),
    ("FIC 2319 A", ["isostripper | FIC-2319A"]),
    ("PI 1924", ["reactor_de_alquilacion | PI-1924", "reactor_de_alquilacion | LIC-1924"]),
    ("FIC 1047", ["reactor_de_alquilacion | FIC-1047", "horno | FIC-1047-F-1-ISOBUTANO"]),
    ("FIC 1903", ["reactor_de_alquilacion | FIC-1903C", "horno | FIC-1903C-F-2-OLEFINAS"]),
    ("Relacion 2C-4=/1C-4= Prefiltrada", ["lab_R-202 | Relacion 2C-4=/1C-4=-Prefiltrada"]),
    ("Relacion 1 Ol/iso Prefiltrada", ["lab_isobutano_reciclo | Relacion 1 Ol/iso-Prefiltrada"]),
    ("Relacion 2 Ol/iso Prefiltrada", ["lab_isobutano_reciclo | Relacion 2 Ol/iso-Prefiltrada"]),
]


def normalizar_texto(texto):
    normalizado = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(char for char in normalizado if not unicodedata.combining(char))
    limpio = re.sub(r"[^a-z0-9]+", "", sin_acentos.lower())
    return limpio


def formatear_valor_metrica(valor):
    if valor is None or pd.isna(valor):
        return "-"
    return f"{float(valor):.4f}"


def resolver_fila_resumen(summary, candidatos):
    if summary is None or summary.empty:
        return None

    candidatos_normalizados = [normalizar_texto(candidato) for candidato in candidatos]
    for row in summary.itertuples(index=False):
        feature = getattr(row, "feature", "")
        feature_normalizado = normalizar_texto(feature)
        if feature in candidatos or feature_normalizado in candidatos_normalizados:
            return row
    return None


def construir_tabla_variables_referencia(summary, variables, titulo):
    filas = [
        html.Tr(
            [
                html.Th("Variable solicitada"),
                html.Th("Variable encontrada"),
                html.Th("Lag"),
                html.Th("Corr"),
                html.Th("MI"),
                html.Th("TE"),
                html.Th("RF"),
                html.Th("Consenso"),
            ]
        )
    ]

    for etiqueta, candidatos in variables:
        row = resolver_fila_resumen(summary, candidatos)
        if row is None:
            filas.append(
                html.Tr(
                    [
                        html.Td(etiqueta),
                        html.Td("No disponible"),
                        html.Td("-"),
                        html.Td("-"),
                        html.Td("-"),
                        html.Td("-"),
                        html.Td("-"),
                        html.Td("-"),
                    ]
                )
            )
            continue

        filas.append(
            html.Tr(
                [
                    html.Td(etiqueta),
                    html.Td(construir_etiqueta_columna(row.feature)),
                    html.Td(row.best_lag_label),
                    html.Td(formatear_valor_metrica(row.pearson)),
                    html.Td(formatear_valor_metrica(getattr(row, "mutual_information", None))),
                    html.Td(formatear_valor_metrica(getattr(row, "transfer_entropy", None))),
                    html.Td(formatear_valor_metrica(getattr(row, "importance_mean", None))),
                    html.Td(formatear_valor_metrica(row.consensus_score)),
                ]
            )
        )

    return html.Div(
        [
            html.H2(titulo),
            html.Table(filas),
        ]
    )


def construir_tabla_influencias(summary, etiquetar_columna, top_n=12):
    filas = [
        html.Tr(
            [
                html.Th("Variable"),
                html.Th("Lag"),
                html.Th("Corr"),
                html.Th("MI"),
                html.Th("TE"),
                html.Th("RF"),
                html.Th("Consenso"),
            ]
        )
    ]

    for row in summary.head(top_n).itertuples(index=False):
        filas.append(
            html.Tr(
                [
                    html.Td(etiquetar_columna(row.feature)),
                    html.Td(row.best_lag_label),
                    html.Td(formatear_valor_metrica(row.pearson)),
                    html.Td(formatear_valor_metrica(getattr(row, "mutual_information", None))),
                    html.Td(formatear_valor_metrica(getattr(row, "transfer_entropy", None))),
                    html.Td(formatear_valor_metrica(getattr(row, "importance_mean", None))),
                    html.Td(formatear_valor_metrica(row.consensus_score)),
                ]
            )
        )

    return html.Div([html.Table(filas)])


def construir_grafico_influencias(summary, etiquetar_columna, top_n=10):
    if summary is None or summary.empty:
        return html.Div("No hubo suficientes datos para calcular influencias.")

    top = summary.head(top_n).iloc[::-1]
    fig = go.Figure(
        data=[
            go.Bar(
                x=top["consensus_score"],
                y=[etiquetar_columna(valor) for valor in top["feature"]],
                orientation="h",
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=360,
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def construir_resumen_metricas(metrics):
    if not metrics:
        return html.Div("Random Forest no pudo entrenarse con suficientes datos.")
    if metrics.get("error"):
        return html.Div(metrics["error"])

    filas = [
        html.Tr([html.Th("Metrica"), html.Th("Valor")]),
        html.Tr([html.Td("Filas contexto"), html.Td(str(metrics.get("context_rows", "-")))]),
        html.Tr([html.Td("Min overlap"), html.Td(str(metrics.get("min_overlap", "-")))]),
        html.Tr([html.Td("Tamano batch RF"), html.Td(str(metrics.get("rf_batch_features", "-")))]),
        html.Tr([html.Td("Batches RF"), html.Td(str(metrics.get("batches_total", "-")))]),
        html.Tr([html.Td("Batches RF exitosos"), html.Td(str(metrics.get("batches_trained", "-")))]),
        html.Tr([html.Td("Variables con RF"), html.Td(str(metrics.get("features_scored", "-")))]),
        html.Tr([html.Td("Filas train"), html.Td(f"{metrics.get('train_rows_min', '-')} a {metrics.get('train_rows_max', '-')}")]),
        html.Tr([html.Td("Filas test"), html.Td(f"{metrics.get('test_rows_min', '-')} a {metrics.get('test_rows_max', '-')}")]),
        html.Tr([html.Td("R2 test promedio"), html.Td(formatear_valor_metrica(metrics.get("test_r2_mean")))]),
        html.Tr([html.Td("MAE test promedio"), html.Td(formatear_valor_metrica(metrics.get("test_mae_mean")))]),
        html.Tr([html.Td("Features usadas promedio"), html.Td(formatear_valor_metrica(metrics.get("features_used_mean")))]),
        html.Tr([html.Td("Features descartadas promedio"), html.Td(formatear_valor_metrica(metrics.get("features_dropped_mean")))]),
    ]
    return html.Div([html.Table(filas)])


def construir_bloque_analisis_profundo(influence_result):
    summary = influence_result["summary"]
    metrics = influence_result["metrics"]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Influencias principales"),
                            construir_tabla_influencias(summary, construir_etiqueta_columna),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Metricas del modelo"),
                            construir_resumen_metricas(metrics),
                        ]
                    ),
                    html.Div(
                        [
                            html.H2("Top influencias por consenso"),
                            construir_grafico_influencias(summary, construir_etiqueta_columna),
                        ]
                    ),
                    construir_tabla_variables_referencia(
                        summary,
                        VARIABLES_INTERES,
                        "Variables de interes",
                    ),
                ],
                style=ANALISIS_PROFUNDO_STACK_STYLE,
            ),
        ]
    )


def construir_bloque_resultado_profundo(influence_result):
    return html.Div(
        [
            construir_bloque_analisis_profundo(influence_result),
        ],
        style={"marginBottom": "24px"},
    )


def register_deep_analysis_callbacks(app):
    @app.callback(
        Output("deep-analysis-container", "children", allow_duplicate=True),
        Input("deep-analysis-dropdown", "value"),
        Input("deep-analysis-context-dropdown", "value"),
        prevent_initial_call=True,
    )
    def actualizar_analisis_profundo(
        columna_objetivo,
        context_key,
    ):
        if not columna_objetivo:
            return []
        if not context_key:
            return [html.Div("Selecciona un contexto disponible para consultar el analisis profundo.")]

        if columna_objetivo not in get_precomputed_analysis_columns():
            return [
                html.Div(
                    "Selecciona una variable con analisis profundo precomputado."
                )
            ]

        cached = load_precomputed_analysis_result(columna_objetivo, context_key)
        if cached is None:
            return [
                html.Div(
                    "No se encontraron resultados precomputados para la variable seleccionada."
                )
            ]

        return [
            construir_bloque_resultado_profundo(
                cached,
            )
        ]

import sys

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.callbacks.common import construir_mascara_contexto_operacion
from dashboard_app.data import obtener_columnas_numericas_dataset
from dashboard_app.domain.deep_analysis import calcular_influencias_para_variable
from dashboard_app.repositories.analysis_cache import (
    PRECOMPUTED_ANALYSIS_COLUMNS,
    get_precomputed_analysis_contexts,
    has_precomputed_analysis_result,
    save_precomputed_analysis_result,
)


def load_dataset_influence(columnas_objetivo):
    columnas = obtener_columnas_numericas_dataset("5min")
    for columna_objetivo in columnas_objetivo:
        if columna_objetivo not in columnas:
            columnas.append(columna_objetivo)
    return load_combined_dataset("5min", columns=columnas)


def filtrar_dataset_para_contexto(df_influence_base, contexto):
    mascara = construir_mascara_contexto_operacion(
        df_influence_base,
        modo_operacion=contexto["modo_operacion"],
        arranque_id=contexto["arranque_id"],
        parada_id=contexto["parada_id"],
        operacion_id=contexto["operacion_id"],
    )
    if mascara is None:
        return df_influence_base
    return df_influence_base.loc[mascara.reindex(df_influence_base.index, fill_value=False)]


def main():
    columnas_cli = [arg.strip() for arg in sys.argv[1:] if arg.strip()]
    columnas = sorted(columnas_cli or PRECOMPUTED_ANALYSIS_COLUMNS)
    if not columnas:
        print("No hay columnas configuradas para precomputar.")
        return

    contextos = get_precomputed_analysis_contexts()
    print(
        f"Precomputando analisis para {len(columnas)} columnas "
        f"en {len(contextos)} contextos..."
    )
    df_influence_base = load_dataset_influence(columnas)

    for contexto in contextos:
        columnas_pendientes = [
            columna
            for columna in columnas
            if not has_precomputed_analysis_result(columna, contexto["key"])
        ]
        if not columnas_pendientes:
            print(f"Cache existente, se omite contexto: {contexto['label']}")
            continue

        df_contexto = filtrar_dataset_para_contexto(df_influence_base, contexto)
        print(
            f"Contexto {contexto['label']}: "
            f"{len(df_contexto)} filas, {len(columnas_pendientes)} columnas pendientes"
        )

        for columna in columnas_pendientes:
            print(f"Procesando {contexto['label']} -> {columna}")
            influence_result = calcular_influencias_para_variable(df_contexto, columna)
            save_precomputed_analysis_result(
                columna,
                contexto["key"],
                influence_result,
            )
            print(f"Guardado cache: {contexto['label']} -> {columna}")


if __name__ == "__main__":
    main()

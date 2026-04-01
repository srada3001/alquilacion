import sys

from data_processing.analysis_dataset import load_combined_dataset
from dashboard_app.data import obtener_columnas_numericas_dataset
from dashboard_app.domain.deep_analysis import calcular_influencias_para_variable
from dashboard_app.repositories.analysis_cache import (
    PRECOMPUTED_ANALYSIS_COLUMNS,
    has_precomputed_analysis_result,
    save_precomputed_analysis_result,
)


def load_dataset_influence(columnas_objetivo):
    columnas = obtener_columnas_numericas_dataset("5min")
    for columna_objetivo in columnas_objetivo:
        if columna_objetivo not in columnas:
            columnas.append(columna_objetivo)
    return load_combined_dataset("5min", columns=columnas)


def main():
    columnas_cli = [arg.strip() for arg in sys.argv[1:] if arg.strip()]
    columnas = sorted(columnas_cli or PRECOMPUTED_ANALYSIS_COLUMNS)
    if not columnas:
        print("No hay columnas configuradas para precomputar.")
        return

    print(f"Precomputando analisis para {len(columnas)} columnas...")
    df_influence_base = load_dataset_influence(columnas)

    for columna in columnas:
        if has_precomputed_analysis_result(columna):
            print(f"Cache existente, se omite: {columna}")
            continue
        print(f"Procesando: {columna}")
        influence_result = calcular_influencias_para_variable(df_influence_base, columna)
        save_precomputed_analysis_result(
            columna,
            influence_result,
        )
        print(f"Guardado cache: {columna}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

from config import get_processed_output_path
from data_processing.analysis_dataset import (
    build_combined_dataset_1h,
    build_combined_dataset_5m,
    get_combined_dataset_path_1h,
    get_combined_dataset_path_5m,
)
from data_processing.kalman import aplicar_filtro_kalman


DERIVED_PHASE_NAME = "variables_derivadas"
KALMAN_PROCESS_VARIANCE = 0.0005
KALMAN_MEASUREMENT_VARIANCE = 100.0

VARIABLES_KALMAN = {
    "tratadores_e_intercambiadores_de_butano": {
        "AI-1224A": "tratadores_e_intercambiadores_de_butano | AI-1224A-Kalman",
        "AI-1224B": "tratadores_e_intercambiadores_de_butano | AI-1224B-Kalman",
    },
}

VARIABLES_PREFILTRADAS = {
    "lab_R-202": {
        "Relacion 2C-4=/1C-4=": {
            "columna_nueva": "lab_R-202 | Relacion 2C-4=/1C-4=-Prefiltrada",
            "min": None,
            "max": 13,
        },
    },
    "lab_isobutano_reciclo": {
        "Relacion 1 Ol/iso": {
            "columna_nueva": "lab_isobutano_reciclo | Relacion 1 Ol/iso-Prefiltrada",
            "min": 0,
            "max": 25,
        },
        "Relacion 2 Ol/iso": {
            "columna_nueva": "lab_isobutano_reciclo | Relacion 2 Ol/iso-Prefiltrada",
            "min": 0,
            "max": 25,
        },
    },
}


def cargar_fase(fase, cache):
    if fase in cache:
        return cache[fase]

    parquet_path = Path(get_processed_output_path(fase))
    if not parquet_path.exists():
        cache[fase] = pd.DataFrame()
        return cache[fase]

    df = pd.read_parquet(parquet_path)
    df.index = pd.to_datetime(df.index)
    cache[fase] = df
    return df


def construir_variables_derivadas():
    cache_fases = {}
    series_derivadas = []
    columnas_generadas = []

    for fase, variables in VARIABLES_KALMAN.items():
        df = cargar_fase(fase, cache_fases)
        if df.empty:
            continue

        for columna_origen, columna_nueva in variables.items():
            if columna_origen not in df.columns:
                continue

            serie = aplicar_filtro_kalman(
                df[columna_origen],
                process_variance=KALMAN_PROCESS_VARIANCE,
                measurement_variance=KALMAN_MEASUREMENT_VARIANCE,
            )
            series_derivadas.append(pd.Series(serie, index=df.index, name=columna_nueva))
            columnas_generadas.append(columna_nueva)

    for fase, variables in VARIABLES_PREFILTRADAS.items():
        df = cargar_fase(fase, cache_fases)
        if df.empty:
            continue

        for columna_origen, regla in variables.items():
            if columna_origen not in df.columns:
                continue

            serie = df[columna_origen]
            valor_minimo = regla.get("min")
            valor_maximo = regla.get("max")

            if valor_minimo is None:
                serie = serie.where(serie <= valor_maximo)
            elif valor_maximo is None:
                serie = serie.where(serie >= valor_minimo)
            else:
                serie = serie.where(
                    serie.between(valor_minimo, valor_maximo, inclusive="both")
                )

            series_derivadas.append(serie.rename(regla["columna_nueva"]))
            columnas_generadas.append(regla["columna_nueva"])

    if not series_derivadas:
        return pd.DataFrame(), []

    derivadas_df = pd.concat(series_derivadas, axis=1, sort=True).sort_index()
    return derivadas_df, columnas_generadas


def guardar_variables_derivadas(df):
    output_path = Path(get_processed_output_path(DERIVED_PHASE_NAME))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, engine="pyarrow")
    return output_path


def main():
    derivadas_df, columnas_generadas = construir_variables_derivadas()
    output_path = guardar_variables_derivadas(derivadas_df)

    if columnas_generadas:
        print(f"Actualizado: {output_path.name} -> {', '.join(columnas_generadas)}")
    else:
        print(f"Sin cambios: {output_path.name}")

    combinado_5m = build_combined_dataset_5m()
    combinado_1h = build_combined_dataset_1h()
    print(
        f"Dataset combinado generado: {get_combined_dataset_path_5m()} "
        f"-> {combinado_5m.shape[0]} filas, {combinado_5m.shape[1]} columnas"
    )
    print(
        f"Dataset combinado generado: {get_combined_dataset_path_1h()} "
        f"-> {combinado_1h.shape[0]} filas, {combinado_1h.shape[1]} columnas"
    )


if __name__ == "__main__":
    main()

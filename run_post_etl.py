import os

import pandas as pd

from data_processing.analysis_dataset import (
    build_combined_dataset_1h,
    build_combined_dataset_5m,
    get_combined_dataset_path_1h,
    get_combined_dataset_path_5m,
)
from data_processing.kalman import aplicar_filtro_kalman
from config import (
    DATA_PATH,
    PARQUET_EXTENSION,
    PROCESSED_DATA_FOLDER,
)


VARIABLES_DESVIACION = {
    "AI-1224A": ("AI-1224A-desviacion", 10),
    "AI-1224B": ("AI-1224B-desviacion", 90),
}
VARIABLES_KALMAN = {
    "AI-1224A": "AI-1224A-kalman",
    "AI-1224B": "AI-1224B-kalman",
}
KALMAN_PROCESS_VARIANCE = 0.0005
KALMAN_MEASUREMENT_VARIANCE = 100.0


def obtener_rutas_parquet(carpeta):
    carpeta_path = os.path.join(DATA_PATH, carpeta)
    if not os.path.isdir(carpeta_path):
        return []

    return sorted(
        os.path.join(carpeta_path, nombre)
        for nombre in os.listdir(carpeta_path)
        if nombre.endswith(PARQUET_EXTENSION)
    )


def agregar_variables_desviacion(df):
    columnas_agregadas = []

    for columna_origen, (columna_nueva, valor_ideal) in VARIABLES_DESVIACION.items():
        if columna_origen not in df.columns:
            continue
        if columna_nueva in df.columns:
            df = df.drop(columns=[columna_nueva])
        df[columna_nueva] = df[columna_origen] - valor_ideal
        columnas_agregadas.append(columna_nueva)

    return df, columnas_agregadas


def agregar_variables_kalman(df):
    columnas_agregadas = []

    for columna_origen, columna_nueva in VARIABLES_KALMAN.items():
        if columna_origen not in df.columns:
            continue
        if columna_nueva in df.columns:
            df = df.drop(columns=[columna_nueva])
        df[columna_nueva] = aplicar_filtro_kalman(
            df[columna_origen],
            process_variance=KALMAN_PROCESS_VARIANCE,
            measurement_variance=KALMAN_MEASUREMENT_VARIANCE,
        )
        columnas_agregadas.append(columna_nueva)

    return df, columnas_agregadas


def procesar_parquet(parquet_path):
    df = pd.read_parquet(parquet_path)
    columnas_agregadas = []
    df, columnas_desviacion = agregar_variables_desviacion(df)
    columnas_agregadas.extend(columnas_desviacion)
    df, columnas_kalman = agregar_variables_kalman(df)
    columnas_agregadas.extend(columnas_kalman)

    if not columnas_agregadas:
        print(f"Sin cambios: {os.path.basename(parquet_path)}")
        return

    df.to_parquet(parquet_path, engine="pyarrow")
    print(
        f"Actualizado: {os.path.basename(parquet_path)} "
        f"-> {', '.join(columnas_agregadas)}"
    )


def main():
    print(f"Procesando carpeta: {PROCESSED_DATA_FOLDER}")
    for parquet_path in obtener_rutas_parquet(PROCESSED_DATA_FOLDER):
        procesar_parquet(parquet_path)

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

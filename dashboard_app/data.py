import os

import pandas as pd

from config import (
    DATA_PATH,
    PROCESSED_DATA_FOLDER,
    get_processed_output_1h_path,
    get_processed_output_path,
)


GRUPOS = {
    "Temperatura": lambda df: [c for c in df.columns if c.startswith("TI")],
    "Flujo": lambda df: [c for c in df.columns if c.startswith("FI")],
    "Presion": lambda df: [c for c in df.columns if c.startswith("P")],
    "Oxigeno": lambda df: [c for c in df.columns if c.startswith("AI")],
}


def obtener_fases():
    outputs_path = os.path.join(DATA_PATH, PROCESSED_DATA_FOLDER)
    if not os.path.isdir(outputs_path):
        return []

    fases = []
    for archivo in os.listdir(outputs_path):
        archivo_path = os.path.join(outputs_path, archivo)
        if not os.path.isfile(archivo_path) or not archivo.endswith(".parquet"):
            continue
        fases.append(os.path.splitext(archivo)[0])

    return sorted(fases)


def cargar_df(fase, freq):
    if freq == "1h":
        carga_path = get_processed_output_1h_path(fase)
    else:
        carga_path = get_processed_output_path(fase)

    df = pd.read_parquet(carga_path)
    df.index = pd.to_datetime(df.index)
    return df
def cargar_dataframes(fases, freq):
    dataframes = {}
    for fase in fases or []:
        dataframes[fase] = cargar_df(fase, freq)
    return dataframes


def combinar_dataframes_por_fase(dataframes):
    dataframes_renombrados = []

    for fase, df in dataframes.items():
        dataframes_renombrados.append(df.add_prefix(f"{fase} | "))

    if not dataframes_renombrados:
        return pd.DataFrame()

    return pd.concat(dataframes_renombrados, axis=1)

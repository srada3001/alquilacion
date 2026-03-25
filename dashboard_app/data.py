import os

import pandas as pd
from pyarrow import parquet as pq
from pyarrow import types as patypes

from config import (
    DATA_PATH,
    PROCESSED_DATA_FOLDER,
    get_processed_output_1h_path,
    get_processed_output_path,
)


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


def formatear_nombre_fase(fase):
    texto = fase.replace("_", " ").strip()
    if not texto:
        return fase
    return texto[0].upper() + texto[1:]


def cargar_df(fase, freq):
    return cargar_df_columnas(fase, freq)


def obtener_ruta_carga(fase, freq):
    if freq == "1h":
        return get_processed_output_1h_path(fase)
    return get_processed_output_path(fase)


def obtener_columnas_fase(fase, freq):
    carga_path = obtener_ruta_carga(fase, freq)
    schema = pq.ParquetFile(carga_path).schema_arrow
    return [
        field.name
        for field in schema
        if field.name != "__index_level_0__"
    ]


def obtener_columnas_numericas_fase(fase, freq):
    carga_path = obtener_ruta_carga(fase, freq)
    schema = pq.ParquetFile(carga_path).schema_arrow
    columnas = []

    for field in schema:
        if field.name == "__index_level_0__":
            continue
        if (
            patypes.is_integer(field.type)
            or patypes.is_floating(field.type)
            or patypes.is_decimal(field.type)
        ):
            columnas.append(field.name)

    return columnas


def cargar_df_columnas(fase, freq, columnas=None):
    carga_path = obtener_ruta_carga(fase, freq)
    if columnas is not None:
        columnas = list(dict.fromkeys(columnas))
        if not columnas:
            return pd.DataFrame()
        df = pd.read_parquet(carga_path, columns=columnas)
    else:
        df = pd.read_parquet(carga_path)

    df.index = pd.to_datetime(df.index)
    return df


def cargar_dataframes(fases, freq):
    return cargar_dataframes_columnas(fases, freq)


def cargar_dataframes_columnas(fases, freq, columnas_por_fase=None):
    dataframes = {}
    for fase in fases or []:
        columnas = None
        if columnas_por_fase is not None:
            columnas = columnas_por_fase.get(fase, [])
        dataframes[fase] = cargar_df_columnas(fase, freq, columnas=columnas)
    return dataframes


def combinar_dataframes_por_fase(dataframes):
    dataframes_renombrados = []

    for fase, df in dataframes.items():
        dataframes_renombrados.append(df.add_prefix(f"{fase} | "))

    if not dataframes_renombrados:
        return pd.DataFrame()

    return pd.concat(dataframes_renombrados, axis=1)

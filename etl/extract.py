import os

import pandas as pd

from config import get_raw_phase_path


def buscar_partes(fase, logger):
    data_folder_path = get_raw_phase_path(fase)
    partes = [f for f in os.listdir(data_folder_path) if os.path.isdir(os.path.join(data_folder_path, f))]
    logger.info("Partes encontradas: %s", partes)
    partes_paths = [os.path.join(data_folder_path, parte) for parte in partes]
    return partes_paths


def buscar_csv(parte_path, logger):
    csv_files = [f for f in os.listdir(parte_path) if f.endswith(".csv")]
    logger.info("Documentos csv encontrados: %s", csv_files)
    csv_paths = [os.path.join(parte_path, csv_file) for csv_file in csv_files]
    return csv_paths


def extraer_dataframes(csv_paths, logger):
    """
    Lee multiples archivos CSV y devuelve un diccionario de DataFrames.
    Si algun archivo falla, se loguea el error y se continua con los demas.
    """

    dataframes = {}
    total_archivos = len(csv_paths)

    logger.info("Iniciando lectura de archivos CSV")

    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            key = os.path.splitext(os.path.basename(path))[0]
            dataframes[key] = df

            logger.debug("Archivo leido correctamente: %s (%s columnas)", key, len(df.columns))

        except Exception as e:
            logger.error("Error leyendo archivo %s: %s", path, e)

    logger.info(
        "Lectura completada: %s/%s archivos procesados correctamente",
        len(dataframes),
        total_archivos,
    )

    if not dataframes:
        logger.warning("No se pudo leer ningun archivo CSV correctamente")

    return dataframes

import logging
import os
import warnings

import pandas as pd

from config import DATA_PATH, RAW_DATA_FOLDER, get_raw_phase_path
from etl.extract import buscar_csv, buscar_partes, extraer_dataframes
from etl.load import cargar_df, guardar_resumen
from etl.transform import (
    ajustar_formatos,
    configurar_fecha_como_index,
    eliminar_columnas_duplicadas,
    eliminar_filas_duplicadas,
    eliminar_columnas_sin_informacion,
    eliminar_filas_sin_informacion,
    renombrar_columnas,
    resamplear_por_frecuencia,
    resumen,
    unir_dataframes_por_tiempo,
    unir_partes,
)
from etl.utils import set_logger
from etl.load import cargar_df_1h

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

if __name__ == "__main__":
    logging.info("ETL comenzado")

    logging.info("Buscando las fases")
    raw_data_root = os.path.join(DATA_PATH, RAW_DATA_FOLDER)
    fases = [
        f for f in os.listdir(raw_data_root)
        if os.path.isdir(get_raw_phase_path(f))
    ]
    logging.info("Fases encontradas: %s", fases)

    for fase in fases:
        logger = set_logger(fase)
        logger.info("COMENZANDO ETL PARA %s", fase.upper())
        partes_paths = buscar_partes(fase, logger)
        df_partes = []
        for parte_path in partes_paths:
            parte = os.path.basename(parte_path)
            logger.info("PROCESANDO PARTE %s, de la fase %s", parte.upper(), fase.upper())
            csv_paths = buscar_csv(parte_path, logger)
            dataframes = extraer_dataframes(csv_paths, logger)
            if not dataframes:
                logger.warning("No hay dataframes validos en %s", parte)
                continue
            df_parte = unir_dataframes_por_tiempo(dataframes, logger)
            df_parte = renombrar_columnas(df_parte, logger)
            df_parte = ajustar_formatos(df_parte, logger)
            df_parte = configurar_fecha_como_index(df_parte, logger)
            df_partes.append(df_parte)

        if not df_partes:
            logger.warning("No hay partes validas para la fase %s", fase)
            continue
        df = unir_partes(df_partes, logger)
        df = eliminar_columnas_duplicadas(df, logger)
        df = eliminar_filas_duplicadas(df, logger)
        df = eliminar_columnas_sin_informacion(df, logger)
        df = eliminar_filas_sin_informacion(df, logger)
        df_5m = resamplear_por_frecuencia(df, "5min", logger)
        df_5m = eliminar_filas_sin_informacion(df_5m, logger)
        df_1h = resamplear_por_frecuencia(df, "1h", logger)
        df_1h = eliminar_filas_sin_informacion(df_1h, logger)
        resumen_df = resumen(df_5m, logger)
        guardar_resumen(resumen_df, fase, logger)
        cargar_df(df=df_5m, fase=fase, logger=logger)
        cargar_df_1h(df=df_1h, fase=fase, logger=logger)

    logging.info("ETL terminado")

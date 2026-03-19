import os

from config import get_processed_output_path, get_summary_path


def guardar_resumen(resumen, fase, logger):
    logger.info("Guardando resumen")
    resumen_path = get_summary_path(fase)
    os.makedirs(os.path.dirname(resumen_path), exist_ok=True)
    resumen.to_csv(resumen_path, index=True)
    logger.info("Resumen guardado")


def cargar_df(df, fase, logger):
    logger.info("Guardando data procesada")
    carga_path = get_processed_output_path(fase)
    os.makedirs(os.path.dirname(carga_path), exist_ok=True)
    df.to_parquet(carga_path, engine="pyarrow")
    logger.info("Data procesada guardada")

LOG_FILE = "etl.log"
DATA_PATH = "data"
DATA_ORIGINAL_FOLDER = "data_original"
SUMMARY_FILE = "resumen_etl.csv"
PARQUET_FILE = "df.parquet"

import logging
import os
import pandas as pd
import re

import warnings
#Ignorar warnings relacionados con el tipo de dato
#Se solucionan en la transformación
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

def set_logger(fase):
    logger = logging.getLogger(fase)
    logger.setLevel(logging.DEBUG)

    #Evita duplicado
    if logger.hasHandlers():
        logger.handlers.clear()

    log_path = os.path.join(DATA_PATH, fase, LOG_FILE)

    # Handler para archivo
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Añadir handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def buscar_partes(fase):
    data_folder_path = os.path.join(DATA_PATH, fase, DATA_ORIGINAL_FOLDER)
    partes = [f for f in os.listdir(data_folder_path) if os.path.isdir(os.path.join(data_folder_path, f))]
    logger.info("Partes encontradas: %s", partes)
    partes_paths = [os.path.join(data_folder_path, parte) for parte in partes]
    return partes_paths

def buscar_csv(parte_path):
    csv_files = [f for f in os.listdir(parte_path) if f.endswith(".csv")]
    logger.info("Documentos csv encontrados: %s", csv_files)
    csv_paths = [os.path.join(parte_path, csv_file) for csv_file in csv_files]
    return csv_paths

def extraer_dataframes(csv_paths):
    """
    Lee múltiples archivos CSV y devuelve un diccionario de DataFrames.
    Si algún archivo falla, se loguea el error y se continúa con los demás.
    """

    dataframes = {}
    total_archivos = len(csv_paths)

    logger.info("Iniciando lectura de archivos CSV")

    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            key = os.path.splitext(os.path.basename(path))[0]
            dataframes[key] = df

            logger.debug("Archivo leído correctamente: %s (%s columnas)", key, len(df.columns))

        except Exception as e:
            logger.error("Error leyendo archivo %s: %s", path, e)

    logger.info(
        "Lectura completada: %s/%s archivos procesados correctamente",
        len(dataframes),
        total_archivos
    )

    if not dataframes:
        logger.warning("No se pudo leer ningún archivo CSV correctamente")

    return dataframes

def unir_dataframes_por_tiempo(dataframes):
    """
    Concatena múltiples DataFrames por filas (stack temporal).
    """
    
    logger.info("Uniendo diferentes periodos de tiempo en un mismo dataframe")
    df = pd.concat(dataframes.values(), ignore_index=False).sort_index()
    logger.info("DataFrame unificado: %s filas y %s columnas", df.shape[0], df.shape[1])
    logger.debug("Las columnas son: %s", df.columns)
    return df

def renombrar_columnas(df, prefix = r"\\pigrc\044-"):
    """
    Renombra las columnas de un DataFrame eliminando un prefijo común y la terminación .MEAS,
    estandarizando el nombre de la columna de fecha y unificando tags tipo PI2353 → PI-2353.
    """
    df = df.rename(
        columns=lambda c: "fecha" if c.strip().lower() == "fecha"
        else re.sub(
            r"([A-Za-z]+)(\d+)",
            r"\1-\2",
            c.replace(prefix, "").replace(".MEAS.1", "").replace(".MEAS", "")
        )
    )

    logger.info("Las columnas renombradas son: %s", df.columns)

    return df

def ajustar_formatos(df):

    logger.info("Ajustando formato de fechas")
    df["fecha"] = pd.to_datetime(
        df["fecha"],
        errors="coerce"
    )
    logger.info("Formato de fechas ajustado")

    logger.info("Ajustando formato de valores numéricos")
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].apply(pd.to_numeric, errors="coerce")
    logger.info("Formato de valores numéricos ajustado")

    return df

def configurar_fecha_como_index(df):
    df.set_index('fecha', inplace=True)
    return df

def unir_partes(df_partes):
    df = pd.concat(df_partes, ignore_index=False)
    return df

def eliminar_columnas_sin_informacion(df):
    """
    Elimina columnas que tengan 2 o menos valores únicos.
    """

    logger.info("Eliminando columnas sin información relevante")
    total_columnas = df.shape[1]
    
    df_filtrado = df.loc[:, df.nunique() > 2]
    
    columnas_restantes = df_filtrado.shape[1]
    columnas_eliminadas = total_columnas - columnas_restantes

    logger.info("Columnas eliminadas: %s", columnas_eliminadas)

    return df_filtrado

def eliminar_filas_sin_informacion(df):
    """Eliminación de filas completamente vacías
    Una fila se elimina solo si TODOS sus valores son NaN o NaT"""

    logger.info("Eliminando filas sin información")
    mask_filas_vacias = df.isna().all(axis=1)
    df = df.loc[~mask_filas_vacias].copy()
    logger.info(f"Filas eliminadas: {mask_filas_vacias.sum()}")

    return df

def resumen(df):
    """
    Devuelve un resumen estructural del DataFrame con tipos de datos,
    conteo de valores nulos, no nulos y valores únicos por columna.
    """

    logger.info("Generando resumen")
    resumen = pd.DataFrame({
        "tipo": df.dtypes,
        "no_nulos": df.notna().sum(),
        "nulos": df.isna().sum(),
        "unicos": df.nunique()
    })
    logger.info("Resumen: \n%s", resumen.head())
    return resumen

def guardar_resumen(resumen, fase):
    resumen_path = os.path.join(DATA_PATH, fase, SUMMARY_FILE)
    resumen.to_csv(resumen_path, index=True)
    
def cargar_df(df, fase):
    carga_path = os.path.join(DATA_PATH, fase, PARQUET_FILE)
    df.to_parquet(carga_path, engine="pyarrow")
    
"""
Estructura esperada de los datos:

├── data/
│   ├── <fase>/
│   │   ├── data_original/
│   │   │   ├── <parte_1>/
│   │   │   │   ├── archivo1.csv
│   │   │   │   ├── archivo2.csv
│   │   │   ├── <parte_2>/
│   │   │   │   ├── archivo3.csv
│   │   ├── df.parquet
│   │   ├── resumen_etl.csv
│   │   ├── etl.log

Donde:
- "data" es la carpeta raíz de los datos
- Cada "fase" es una subcarpeta dentro de "data"
- "data_original" contiene las distintas partes de la data
- Cada "parte" agrupa archivos CSV
- Los CSV de una misma parte tienen las mismas columnas
- Cada archivo representa un periodo de tiempo distinto
- El ETL genera:
    - df.parquet: dataset final procesado
    - resumen_etl.csv: resumen estructural
    - etl.log: log del proceso
"""
if __name__ == "__main__":
    logging.info("ETL comenzado")

    logging.info("Buscando las fases")
    #Buscar las fases
    #Las fases son las carpetas del folder
    fases = [
        f for f in os.listdir(DATA_PATH)
        if os.path.isdir(os.path.join(DATA_PATH, f))
    ]
    logging.info("Fases encontradas: %s", fases)

    for fase in fases:
        logger = set_logger(fase)
        logger.info("COMENZANDO ETL PARA %s", fase.upper())
        partes_paths = buscar_partes(fase)
        df_partes = []
        for parte_path in partes_paths:
            parte = os.path.basename(parte_path)
            logger.info("PROCESANDO PARTE %s, de la fase %s", parte.upper(), fase.upper())
            csv_paths = buscar_csv(parte_path)
            dataframes = extraer_dataframes(csv_paths)
            if not dataframes:
                logger.warning("No hay dataframes válidos en %s", parte)
                continue
            df_parte = unir_dataframes_por_tiempo(dataframes)
            df_parte = renombrar_columnas(df_parte)
            df_parte = ajustar_formatos(df_parte)
            df_parte = configurar_fecha_como_index(df_parte)
            df_partes.append(df_parte)

        if not df_partes:
            logger.warning("No hay partes válidas para la fase %s", fase)
            continue
        df = unir_partes(df_partes)    
        df = eliminar_columnas_sin_informacion(df)
        df = eliminar_filas_sin_informacion(df)
        resumen_df = resumen(df)
        guardar_resumen(resumen_df, fase)
        logger.info("COMENZANDO CARGA PARA %s", fase.upper())
        cargar_df(df=df, fase=fase)

    logging.info("ETL terminado")
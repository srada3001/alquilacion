import re

import pandas as pd


def unir_dataframes_por_tiempo(dataframes, logger):
    """
    Concatena multiples DataFrames por filas (stack temporal).
    """

    logger.info("Uniendo diferentes periodos de tiempo en un mismo dataframe")
    df = pd.concat(dataframes.values(), ignore_index=False).sort_index()
    logger.info("DataFrame unificado: %s filas y %s columnas", df.shape[0], df.shape[1])
    logger.debug("Las columnas son: %s", df.columns)
    return df


def renombrar_columnas(df, logger, prefix=r"\\pigrc\044-"):
    """
    Renombra las columnas de un DataFrame eliminando un prefijo comun y la terminacion .MEAS,
    estandarizando el nombre de la columna de fecha y unificando tags tipo PI2353 a PI-2353.
    """
    df = df.rename(
        columns=lambda c: "fecha" if c.strip().lower() == "fecha"
        else re.sub(
            r"([A-Za-z]+)(\d+)",
            r"\1-\2",
            c.replace(prefix, "").replace(".MEAS.1", "").replace(".MEAS", ""),
        )
    )

    logger.info("Las columnas renombradas son: %s", df.columns)

    return df


def ajustar_formatos(df, logger):
    """
    Convierte la columna ``fecha`` soportando dos formatos de origen:
    fechas en texto y seriales de fecha de Excel.

    Algunos archivos traen valores como ``4/15/2017 0:00`` y otros como
    ``45669.00139``. Los valores numericos se interpretan como dias desde el
    origen de Excel (1899-12-30) y los no numericos se parsean como fechas en
    texto.
    """
    logger.info("Ajustando formato de fechas")
    fecha_numerica = pd.to_numeric(df["fecha"], errors="coerce")
    es_fecha_excel = fecha_numerica.notna()

    fecha_texto = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    fecha_texto.loc[~es_fecha_excel] = pd.to_datetime(
        df.loc[~es_fecha_excel, "fecha"],
        errors="coerce",
    )
    fecha_excel = pd.to_datetime(
        fecha_numerica,
        unit="D",
        origin="1899-12-30",
        errors="coerce",
    )
    df["fecha"] = fecha_texto.fillna(fecha_excel)
    logger.info("Formato de fechas ajustado")

    logger.info("Ajustando formato de valores numericos")
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].apply(pd.to_numeric, errors="coerce")
    logger.info("Formato de valores numericos ajustado")

    return df


def configurar_fecha_como_index(df, logger):
    logger.info("Ajustando fechas como index")
    df.set_index("fecha", inplace=True)
    logger.info("Fechas ajustadas como index")
    return df


def unir_partes(df_partes, logger):
    logger.info("Uniendo las partes")
    df = pd.concat(df_partes, ignore_index=False)
    logger.info("Partes unidas en un solo dataframe")
    return df


def eliminar_columnas_duplicadas(df, logger):
    logger.info("Eliminando columnas duplicadas")
    total_columnas = df.shape[1]
    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    columnas_eliminadas = total_columnas - df.shape[1]
    logger.info("Columnas duplicadas eliminadas: %s", columnas_eliminadas)
    return df


def eliminar_filas_duplicadas(df, logger):
    logger.info("Eliminando filas duplicadas")
    total_filas = df.shape[0]
    df = df.loc[~df.reset_index().duplicated(keep="first").values].copy()
    filas_eliminadas = total_filas - df.shape[0]
    logger.info("Filas duplicadas eliminadas: %s", filas_eliminadas)
    return df


def resamplear_por_frecuencia(df, freq, logger):
    logger.info("Resampleando dataframe a %s", freq)
    df_resampleado = df.resample(freq).mean()
    logger.info(
        "DataFrame resampleado a %s: %s filas y %s columnas",
        freq,
        df_resampleado.shape[0],
        df_resampleado.shape[1],
    )
    return df_resampleado


def eliminar_columnas_sin_informacion(df, logger):
    """
    Elimina columnas que tengan 2 o menos valores unicos.
    """

    logger.info("Eliminando columnas sin informacion relevante")
    total_columnas = df.shape[1]

    df_filtrado = df.loc[:, df.nunique() > 2]

    columnas_restantes = df_filtrado.shape[1]
    columnas_eliminadas = total_columnas - columnas_restantes

    logger.info("Columnas eliminadas: %s", columnas_eliminadas)

    return df_filtrado


def eliminar_filas_sin_informacion(df, logger):
    """Eliminacion de filas completamente vacias.
    Una fila se elimina solo si TODOS sus valores son NaN o NaT.
    """

    logger.info("Eliminando filas sin informacion")
    mask_filas_vacias = df.isna().all(axis=1)
    df = df.loc[~mask_filas_vacias].copy()
    logger.info("Filas eliminadas: %s", mask_filas_vacias.sum())

    return df


def resumen(df, logger):
    """
    Devuelve un resumen estructural del DataFrame con tipos de datos,
    conteo de valores nulos, no nulos y valores unicos por columna.
    """

    logger.info("Generando resumen")
    resumen_df = pd.DataFrame(
        {
            "tipo": df.dtypes,
            "no_nulos": df.notna().sum(),
            "nulos": df.isna().sum(),
            "unicos": df.nunique(),
        }
    )
    logger.info("Resumen: \n%s", resumen_df.head())
    return resumen_df

from pyarrow import parquet as pq
from pyarrow import types as patypes

from data_processing.analysis_dataset import get_combined_dataset_path, load_combined_dataset


def formatear_nombre_fase(fase):
    texto = fase.replace("_", " ").strip()
    if not texto:
        return fase
    return texto[0].upper() + texto[1:]


def obtener_columnas_dataset(freq):
    carga_path = get_combined_dataset_path(freq)
    if not carga_path.exists():
        load_combined_dataset(freq)
    if not carga_path.exists():
        return []

    schema = pq.ParquetFile(carga_path).schema_arrow
    return [field.name for field in schema if field.name != "__index_level_0__"]


def obtener_columnas_numericas_dataset(freq):
    carga_path = get_combined_dataset_path(freq)
    if not carga_path.exists():
        load_combined_dataset(freq)
    if not carga_path.exists():
        return []

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


def obtener_fases():
    fases = {
        columna.split(" | ", 1)[0]
        for columna in obtener_columnas_dataset("5min")
        if " | " in columna
    }
    return sorted(fases)


def obtener_columnas_fase(fase, freq):
    prefijo = f"{fase} | "
    return [
        columna.split(" | ", 1)[1]
        for columna in obtener_columnas_dataset(freq)
        if columna.startswith(prefijo)
    ]

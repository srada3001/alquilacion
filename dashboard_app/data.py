import base64
from functools import lru_cache
from pathlib import Path

import pandas as pd
from pyarrow import parquet as pq
from pyarrow import types as patypes

from config import DATA_PATH, get_metadata_path
from data_processing.analysis_dataset import get_combined_dataset_path, load_combined_dataset


IMAGES_DIR = Path(DATA_PATH) / "images"
UNITS_METADATA_PATH = Path(get_metadata_path("unidades_variables.csv"))
IMAGE_SUFFIX_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


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


def obtener_ruta_imagen_planta():
    return IMAGES_DIR / "planta.jpg"


def obtener_ruta_imagen_fase(fase):
    if not fase:
        return None
    return IMAGES_DIR / f"{fase}.jpg"


def codificar_imagen_data_uri(path_str):
    path = Path(path_str)
    mime = IMAGE_SUFFIX_TO_MIME.get(path.suffix.lower())
    if mime is None or not path.exists():
        return None
    contenido = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{contenido}"


def obtener_data_uri_imagen_planta():
    path = obtener_ruta_imagen_planta()
    if path is None:
        return None
    return codificar_imagen_data_uri(str(path))


def obtener_data_uri_imagen_fase(fase):
    path = obtener_ruta_imagen_fase(fase)
    if path is None:
        return None
    return codificar_imagen_data_uri(str(path))


def _construir_clave_columna_metadata(fase, variable):
    return f"{str(fase).strip()} | {str(variable).strip()}"


@lru_cache(maxsize=4)
def _cargar_mapa_unidades_por_version(mtime_ns):
    if mtime_ns is None:
        return {}

    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            metadata = pd.read_csv(UNITS_METADATA_PATH, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return {}

    columnas_requeridas = {"fase", "variable", "unidad"}
    if not columnas_requeridas.issubset(metadata.columns):
        return {}

    metadata = metadata.copy()
    metadata["fase"] = metadata["fase"].astype(str).str.strip()
    metadata["variable"] = metadata["variable"].astype(str).str.strip()
    metadata["unidad"] = metadata["unidad"].fillna("").astype(str).str.strip()
    metadata = metadata.loc[metadata["unidad"] != ""].copy()
    if metadata.empty:
        return {}

    metadata["clave"] = metadata.apply(
        lambda row: _construir_clave_columna_metadata(row["fase"], row["variable"]),
        axis=1,
    )
    metadata = metadata.drop_duplicates(subset=["clave"], keep="last")
    return dict(zip(metadata["clave"], metadata["unidad"]))


def obtener_mapa_unidades():
    if not UNITS_METADATA_PATH.exists():
        return {}
    return _cargar_mapa_unidades_por_version(UNITS_METADATA_PATH.stat().st_mtime_ns)


def obtener_unidad_columna(columna):
    return obtener_mapa_unidades().get(str(columna).strip(), "")

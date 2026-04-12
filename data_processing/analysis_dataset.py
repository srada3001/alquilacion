import os
from pathlib import Path

import numpy as np
import pandas as pd

from config import DATA_PATH, PROCESSED_DATA_FOLDER, get_analysis_output_path


COMBINED_DATASET_NAME_5M = "all_phases_5min"
COMBINED_DATASET_NAME_1H = "all_phases_1h"


def get_combined_dataset_path_5m():
    return Path(get_analysis_output_path(COMBINED_DATASET_NAME_5M))


def get_combined_dataset_path_1h():
    return Path(get_analysis_output_path(COMBINED_DATASET_NAME_1H))


def get_combined_dataset_path(freq):
    if freq == "1h":
        return get_combined_dataset_path_1h()
    return get_combined_dataset_path_5m()


def build_combined_dataset_5m():
    base = Path(DATA_PATH) / PROCESSED_DATA_FOLDER
    frames = []

    for parquet_path in sorted(base.glob("*.parquet")):
        phase = parquet_path.stem
        df = pd.read_parquet(parquet_path)
        df.index = pd.to_datetime(df.index)
        numeric = df.select_dtypes(include=[np.number]).astype("float32")
        frames.append(numeric.add_prefix(f"{phase} | "))

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, axis=1, sort=True).sort_index()
    output_path = get_combined_dataset_path_5m()
    os.makedirs(output_path.parent, exist_ok=True)
    combined.to_parquet(output_path, engine="pyarrow")
    return combined


def build_combined_dataset_1h():
    combined_5m = load_combined_dataset("5min")
    if combined_5m.empty:
        combined_1h = pd.DataFrame()
    else:
        combined_1h = combined_5m.resample("1h").mean()
        combined_1h = combined_1h.loc[~combined_1h.isna().all(axis=1)].copy()

    output_path = get_combined_dataset_path_1h()
    os.makedirs(output_path.parent, exist_ok=True)
    combined_1h.to_parquet(output_path, engine="pyarrow")
    return combined_1h


def normalizar_rango_tiempo(time_range):
    if not time_range or len(time_range) < 2:
        return None, None

    inicio = pd.to_datetime(time_range[0], errors="coerce")
    fin = pd.to_datetime(time_range[1], errors="coerce")
    if pd.isna(inicio) or pd.isna(fin):
        return None, None
    if fin < inicio:
        inicio, fin = fin, inicio
    return inicio, fin


def load_combined_dataset(freq="5min", columns=None, time_range=None):
    dataset_path = get_combined_dataset_path(freq)
    if not dataset_path.exists():
        if freq == "1h":
            return build_combined_dataset_1h()
        return build_combined_dataset_5m()

    if columns is not None:
        columns = list(dict.fromkeys(columns))
        if not columns:
            return pd.DataFrame()
        read_kwargs = {"columns": columns}
    else:
        read_kwargs = {}

    inicio, fin = normalizar_rango_tiempo(time_range)
    if inicio is not None and fin is not None:
        read_kwargs["filters"] = [
            ("__index_level_0__", ">=", inicio),
            ("__index_level_0__", "<=", fin),
        ]

    try:
        df = pd.read_parquet(dataset_path, engine="pyarrow", **read_kwargs)
    except Exception:
        read_kwargs.pop("filters", None)
        df = pd.read_parquet(dataset_path, engine="pyarrow", **read_kwargs)

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    if inicio is not None and fin is not None:
        df = df.loc[(df.index >= inicio) & (df.index <= fin)]
    return df


def load_combined_dataset_5m(columns=None, time_range=None):
    return load_combined_dataset("5min", columns=columns, time_range=time_range)

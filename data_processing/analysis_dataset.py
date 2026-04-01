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


def load_combined_dataset(freq="5min", columns=None):
    dataset_path = get_combined_dataset_path(freq)
    if not dataset_path.exists():
        if freq == "1h":
            return build_combined_dataset_1h()
        return build_combined_dataset_5m()

    if columns is not None:
        columns = list(dict.fromkeys(columns))
        if not columns:
            return pd.DataFrame()
        df = pd.read_parquet(dataset_path, columns=columns)
    else:
        df = pd.read_parquet(dataset_path)

    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def load_combined_dataset_5m(columns=None):
    return load_combined_dataset("5min", columns=columns)

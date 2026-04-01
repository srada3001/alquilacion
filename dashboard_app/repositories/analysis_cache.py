import json
import re
from pathlib import Path

import pandas as pd

from config import ANALYSIS_DATA_FOLDER, DATA_PATH


PRECOMPUTED_ANALYSIS_COLUMNS = {
    "tratadores_e_intercambiadores_de_butano | AI-1224A",
    "tratadores_e_intercambiadores_de_butano | AI-1224A-kalman",
    "tratadores_e_intercambiadores_de_butano | AI-1224B",
    "tratadores_e_intercambiadores_de_butano | AI-1224B-kalman",
}


def _sanitize_column_name(column_name):
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", column_name.strip().lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "analysis"


def get_analysis_cache_base_path():
    return Path(DATA_PATH) / ANALYSIS_DATA_FOLDER / "precomputed_analysis"


def get_analysis_cache_path(column_name):
    return get_analysis_cache_base_path() / _sanitize_column_name(column_name)


def get_precomputed_analysis_columns():
    return sorted(PRECOMPUTED_ANALYSIS_COLUMNS)


def has_precomputed_analysis_result(column_name):
    if column_name not in PRECOMPUTED_ANALYSIS_COLUMNS:
        return False
    base_path = get_analysis_cache_path(column_name)
    return (
        (base_path / "metadata.json").exists()
        and (base_path / "summary.parquet").exists()
    )


def save_precomputed_analysis_result(
    column_name,
    influence_result,
):
    base_path = get_analysis_cache_path(column_name)
    base_path.mkdir(parents=True, exist_ok=True)

    frames = {
        "summary": influence_result.get("summary", pd.DataFrame()),
        "screening": influence_result.get("screening", pd.DataFrame()),
        "mi": influence_result.get("mi", pd.DataFrame()),
        "te": influence_result.get("te", pd.DataFrame()),
        "rf": influence_result.get("rf", pd.DataFrame()),
    }
    for name, frame in frames.items():
        frame.to_parquet(base_path / f"{name}.parquet", index=False)

    metadata = {
        "column_name": column_name,
        "metrics": influence_result.get("metrics", {}),
    }
    (base_path / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def load_precomputed_analysis_result(column_name):
    if column_name not in PRECOMPUTED_ANALYSIS_COLUMNS:
        return None

    base_path = get_analysis_cache_path(column_name)
    metadata_path = base_path / "metadata.json"
    if not metadata_path.exists():
        return None
    summary_path = base_path / "summary.parquet"
    if not summary_path.exists():
        return None

    frames = {}
    for name in ["summary", "screening", "mi", "te", "rf"]:
        frame_path = base_path / f"{name}.parquet"
        frames[name] = pd.read_parquet(frame_path) if frame_path.exists() else pd.DataFrame()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    return {
        "influence_result": {
            "summary": frames["summary"],
            "screening": frames["screening"],
            "mi": frames["mi"],
            "te": frames["te"],
            "rf": frames["rf"],
            "metrics": metadata.get("metrics", {}),
        },
    }

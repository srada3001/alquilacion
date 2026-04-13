import json
import re
from pathlib import Path

import pandas as pd

from config import ANALYSIS_DATA_FOLDER, DATA_PATH
from dashboard_app.domain.operation_events import obtener_eventos_operacion, obtener_operaciones


PRECOMPUTED_ANALYSIS_VERSION = 4

PRECOMPUTED_ANALYSIS_COLUMNS = {
    "tratadores_e_intercambiadores_de_butano | AI-1224A-Kalman",
    "tratadores_e_intercambiadores_de_butano | AI-1224B-Kalman",
}

PRECOMPUTED_ANALYSIS_CONTEXT_COMPLETA = "operacion_completa"


def _sanitize_cache_key(value):
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "analysis"


def get_analysis_cache_base_path():
    return Path(DATA_PATH) / ANALYSIS_DATA_FOLDER / "precomputed_analysis"


def build_precomputed_analysis_context_key(
    modo_operacion="toda",
    arranque_id=None,
    parada_id=None,
    operacion_id=None,
):
    contextos_especificos = [bool(arranque_id), bool(parada_id), bool(operacion_id)]
    if sum(contextos_especificos) > 1:
        return None
    if parada_id:
        return None
    if operacion_id:
        return str(operacion_id)
    if arranque_id:
        return str(arranque_id)
    if modo_operacion == "completa":
        return PRECOMPUTED_ANALYSIS_CONTEXT_COMPLETA
    return None


def get_precomputed_analysis_contexts():
    contextos = [
        {
            "key": PRECOMPUTED_ANALYSIS_CONTEXT_COMPLETA,
            "label": "Operación completa",
            "modo_operacion": "completa",
            "arranque_id": None,
            "parada_id": None,
            "operacion_id": None,
        }
    ]

    for evento in obtener_eventos_operacion():
        if evento["arranque_inicio"] is None or evento["arranque_fin"] is None:
            pass
        else:
            contextos.append(
                {
                    "key": build_precomputed_analysis_context_key(
                        arranque_id=evento["arranque_id"],
                    ),
                    "label": f"Arranque {evento['indice']:02d}",
                    "modo_operacion": "toda",
                    "arranque_id": evento["arranque_id"],
                    "parada_id": None,
                    "operacion_id": None,
                }
            )

    for operacion in obtener_operaciones():
        contextos.append(
            {
                "key": build_precomputed_analysis_context_key(
                    operacion_id=operacion["operacion_id"],
                ),
                "label": f"Operación {operacion['indice']:02d}",
                "modo_operacion": "toda",
                "arranque_id": None,
                "parada_id": None,
                "operacion_id": operacion["operacion_id"],
            }
        )

    return contextos


def get_analysis_cache_path(column_name, context_key):
    if not context_key:
        raise ValueError("context_key es obligatorio para el analisis precomputado.")
    return (
        get_analysis_cache_base_path()
        / _sanitize_cache_key(context_key)
        / _sanitize_cache_key(column_name)
    )


def get_precomputed_analysis_columns():
    return sorted(PRECOMPUTED_ANALYSIS_COLUMNS)


def has_precomputed_analysis_result(column_name, context_key):
    if column_name not in PRECOMPUTED_ANALYSIS_COLUMNS:
        return False
    if not context_key:
        return False
    base_path = get_analysis_cache_path(column_name, context_key)
    metadata_path = base_path / "metadata.json"
    summary_path = base_path / "summary.parquet"
    if not metadata_path.exists() or not summary_path.exists():
        return False

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    return metadata.get("version") == PRECOMPUTED_ANALYSIS_VERSION


def save_precomputed_analysis_result(
    column_name,
    context_key,
    influence_result,
):
    base_path = get_analysis_cache_path(column_name, context_key)
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
        "version": PRECOMPUTED_ANALYSIS_VERSION,
        "column_name": column_name,
        "context_key": context_key,
        "metrics": influence_result.get("metrics", {}),
    }
    (base_path / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def load_precomputed_analysis_result(column_name, context_key):
    if column_name not in PRECOMPUTED_ANALYSIS_COLUMNS:
        return None
    if not context_key:
        return None

    base_path = get_analysis_cache_path(column_name, context_key)
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
    if metadata.get("version") != PRECOMPUTED_ANALYSIS_VERSION:
        return None

    return {
        "summary": frames["summary"],
        "screening": frames["screening"],
        "mi": frames["mi"],
        "te": frames["te"],
        "rf": frames["rf"],
        "metrics": metadata.get("metrics", {}),
    }

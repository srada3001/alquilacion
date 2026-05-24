import json
from pathlib import Path

from config import get_metadata_path


LAB_VIEWS_PATH = Path(get_metadata_path("lab_views.json"))
VARIABLE_FIELDS = (
    "descripcion",
    "minimo",
    "maximo",
    "normal",
    "normal_sor",
    "normal_eor",
)


def _normalizar_texto(valor):
    texto = str(valor or "").strip()
    return texto or None


def _normalizar_nombre(nombre):
    return str(nombre or "").strip()


def _construir_columna_variable(scope, tag):
    scope_limpio = _normalizar_texto(scope)
    tag_limpio = _normalizar_texto(tag)
    if not scope_limpio or not tag_limpio:
        return None
    return f"{scope_limpio} | {tag_limpio}"


def _normalizar_variable(variable):
    if not isinstance(variable, dict):
        return None

    tag = _normalizar_texto(variable.get("tag"))
    scope = _normalizar_texto(variable.get("scope", variable.get("fase")))
    if not tag or not scope:
        return None

    normalizada = {
        "tag": tag,
        "scope": scope,
        "column": _normalizar_texto(variable.get("column")) or _construir_columna_variable(scope, tag),
    }

    for campo in VARIABLE_FIELDS:
        fuente = campo
        if campo == "normal_sor":
            fuente = "normal_SOR" if "normal_SOR" in variable else "normal_sor"
        elif campo == "normal_eor":
            fuente = "normal_EOR" if "normal_EOR" in variable else "normal_eor"
        normalizada[campo] = _normalizar_texto(variable.get(fuente))

    return normalizada


def _extraer_vistas(contenido):
    if isinstance(contenido, dict):
        return contenido.get("vistas") or contenido.get("views") or []
    if isinstance(contenido, list):
        return contenido
    return []


def _normalizar_vistas(vistas):
    normalizadas = []
    nombres_vistos = set()
    for vista in vistas or []:
        if not isinstance(vista, dict):
            continue

        nombre = _normalizar_nombre(vista.get("name", vista.get("nombre")))
        if not nombre or nombre in nombres_vistos:
            continue

        variables = []
        columnas_vistas = set()
        for variable in vista.get("variables") or []:
            normalizada = _normalizar_variable(variable)
            if normalizada is None:
                continue
            columna = normalizada.get("column")
            if columna in columnas_vistas:
                continue
            columnas_vistas.add(columna)
            variables.append(normalizada)

        normalizadas.append({"name": nombre, "variables": variables})
        nombres_vistos.add(nombre)

    return sorted(normalizadas, key=lambda item: item["name"].lower())


def load_lab_views():
    if not LAB_VIEWS_PATH.exists():
        return []

    try:
        contenido = json.loads(LAB_VIEWS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    return _normalizar_vistas(_extraer_vistas(contenido))

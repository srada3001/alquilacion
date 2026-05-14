import json
import unicodedata
from functools import lru_cache
from pathlib import Path

from analysis_core.dataset_catalog import obtener_fases
from config import get_saved_views_path


SAVED_VIEWS_PATH = Path(get_saved_views_path())
VARIABLE_FIELDS = (
    "descripcion",
    "minimo",
    "maximo",
    "normal",
    "normal_sor",
    "normal_eor",
)
SERIALIZED_FIELD_NAMES = {
    "descripcion": "descripcion",
    "minimo": "minimo",
    "maximo": "maximo",
    "normal": "normal",
    "normal_sor": "normal_SOR",
    "normal_eor": "normal_EOR",
}


def _normalizar_texto(valor):
    texto = str(valor or "").strip()
    return texto or None


def _normalizar_nombre(nombre):
    return str(nombre or "").strip()


def _clave_fase(texto):
    valor = _normalizar_texto(texto) or ""
    valor = valor.replace("_", " ")
    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(caracter for caracter in valor if not unicodedata.combining(caracter))
    return " ".join(valor.lower().split())


@lru_cache(maxsize=1)
def _mapa_fases():
    return {_clave_fase(fase): fase for fase in obtener_fases()}


def resolver_scope_variable(scope):
    texto = _normalizar_texto(scope)
    if not texto:
        return None
    return _mapa_fases().get(_clave_fase(texto), texto)


def construir_columna_variable(scope, tag):
    scope_resuelto = resolver_scope_variable(scope)
    tag_limpio = _normalizar_texto(tag)
    if not scope_resuelto or not tag_limpio:
        return None
    return f"{scope_resuelto} | {tag_limpio}"


def _normalizar_variable(variable):
    if isinstance(variable, str):
        if " | " not in variable:
            return None
        scope, tag = variable.split(" | ", 1)
        variable = {
            "scope": scope,
            "tag": tag,
            "descripcion": tag,
        }

    if not isinstance(variable, dict):
        return None

    tag = _normalizar_texto(variable.get("tag"))
    scope = _normalizar_texto(variable.get("scope", variable.get("fase")))
    if not tag or not scope:
        return None

    normalizada = {
        "tag": tag,
        "scope": scope,
        "resolved_scope": resolver_scope_variable(scope),
        "column": construir_columna_variable(scope, tag),
        "extras": dict(variable.get("extras") or {}),
    }

    for clave in VARIABLE_FIELDS:
        fuente = clave
        if clave == "normal_sor":
            fuente = "normal_SOR" if "normal_SOR" in variable else "normal_sor"
        elif clave == "normal_eor":
            fuente = "normal_EOR" if "normal_EOR" in variable else "normal_eor"
        normalizada[clave] = _normalizar_texto(variable.get(fuente))

    conocidos = {
        "tag",
        "scope",
        "fase",
        "descripcion",
        "minimo",
        "maximo",
        "normal",
        "normal_sor",
        "normal_eor",
        "normal_SOR",
        "normal_EOR",
        "extras",
    }
    normalizada["extras"].update(
        {
            clave: valor
            for clave, valor in variable.items()
            if clave not in conocidos
        }
    )
    return normalizada


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

            clave_variable = normalizada.get("column") or f"{normalizada['scope']}::{normalizada['tag']}"
            if clave_variable in columnas_vistas:
                continue
            columnas_vistas.add(clave_variable)
            variables.append(normalizada)

        normalizadas.append({"name": nombre, "variables": variables})
        nombres_vistos.add(nombre)
    return sorted(normalizadas, key=lambda item: item["name"].lower())


def _extraer_vistas(contenido):
    if isinstance(contenido, dict):
        return contenido.get("vistas") or contenido.get("views") or []
    if isinstance(contenido, list):
        return contenido
    return []


def _cargar_contenido_crudo():
    if not SAVED_VIEWS_PATH.exists():
        return {"vistas": []}

    try:
        return json.loads(SAVED_VIEWS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"vistas": []}


def _serializar_variable(variable):
    scope = _normalizar_texto(variable.get("scope")) or _normalizar_texto(variable.get("resolved_scope"))
    serializada = {
        "tag": _normalizar_texto(variable.get("tag")),
        "scope": scope,
    }
    for clave_interna, clave_archivo in SERIALIZED_FIELD_NAMES.items():
        serializada[clave_archivo] = _normalizar_texto(variable.get(clave_interna))

    extras = variable.get("extras") or {}
    for clave, valor in extras.items():
        if clave not in serializada:
            serializada[clave] = valor
    return serializada


def _serializar_vistas(vistas):
    return [
        {
            "nombre": vista["name"],
            "variables": [_serializar_variable(variable) for variable in vista.get("variables") or []],
        }
        for vista in _normalizar_vistas(vistas)
    ]


def load_saved_views():
    contenido = _cargar_contenido_crudo()
    return _normalizar_vistas(_extraer_vistas(contenido))


def save_saved_views(vistas):
    vistas_normalizadas = _normalizar_vistas(vistas)
    SAVED_VIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAVED_VIEWS_PATH.write_text(
        json.dumps({"vistas": _serializar_vistas(vistas_normalizadas)}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return vistas_normalizadas


def upsert_saved_view(nombre, variables):
    nombre_normalizado = _normalizar_nombre(nombre)
    variables_normalizadas = [
        variable
        for variable in (
            _normalizar_variable(variable) for variable in (variables or [])
        )
        if variable is not None
    ]
    vistas = [vista for vista in load_saved_views() if vista["name"] != nombre_normalizado]
    vistas.append({"name": nombre_normalizado, "variables": variables_normalizadas})
    return save_saved_views(vistas)


def delete_saved_view(nombre):
    nombre_normalizado = _normalizar_nombre(nombre)
    vistas = [vista for vista in load_saved_views() if vista["name"] != nombre_normalizado]
    return save_saved_views(vistas)

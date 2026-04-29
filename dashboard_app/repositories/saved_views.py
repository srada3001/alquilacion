import json
from pathlib import Path

from config import get_saved_views_path


SAVED_VIEWS_PATH = Path(get_saved_views_path())
DEFAULT_SCOPE = "series_temporales"


def _normalizar_variables(variables):
    vistas = []
    for variable in variables or []:
        texto = str(variable).strip()
        if texto and texto not in vistas:
            vistas.append(texto)
    return vistas


def _normalizar_nombre(nombre):
    return str(nombre or "").strip()


def _normalizar_vistas(vistas):
    normalizadas = []
    nombres_vistos = set()
    for vista in vistas or []:
        if not isinstance(vista, dict):
            continue
        nombre = _normalizar_nombre(vista.get("name"))
        variables = _normalizar_variables(vista.get("variables"))
        if not nombre or nombre in nombres_vistos:
            continue
        normalizadas.append({"name": nombre, "variables": variables})
        nombres_vistos.add(nombre)
    return sorted(normalizadas, key=lambda item: item["name"].lower())


def _normalizar_scope(scope):
    return str(scope or DEFAULT_SCOPE).strip() or DEFAULT_SCOPE


def _extraer_vistas_por_scope(contenido, scope):
    scope_normalizado = _normalizar_scope(scope)
    if isinstance(contenido, dict):
        if "scopes" in contenido and isinstance(contenido["scopes"], dict):
            return contenido["scopes"].get(scope_normalizado, [])
        if "views" in contenido:
            return contenido.get("views", []) if scope_normalizado == DEFAULT_SCOPE else []
        return contenido.get(scope_normalizado, [])
    return contenido


def _cargar_contenido_crudo():
    if not SAVED_VIEWS_PATH.exists():
        return {}

    try:
        return json.loads(SAVED_VIEWS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_saved_views(scope=DEFAULT_SCOPE):
    contenido = _cargar_contenido_crudo()
    return _normalizar_vistas(_extraer_vistas_por_scope(contenido, scope))


def save_saved_views(vistas, scope=DEFAULT_SCOPE):
    vistas_normalizadas = _normalizar_vistas(vistas)
    scope_normalizado = _normalizar_scope(scope)
    contenido = _cargar_contenido_crudo()
    scopes = {}

    if isinstance(contenido, dict) and "scopes" in contenido and isinstance(contenido["scopes"], dict):
        for clave, valor in contenido["scopes"].items():
            scopes[_normalizar_scope(clave)] = _normalizar_vistas(valor)
    elif isinstance(contenido, dict) and "views" in contenido:
        scopes[DEFAULT_SCOPE] = _normalizar_vistas(contenido.get("views", []))

    scopes[scope_normalizado] = vistas_normalizadas
    SAVED_VIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAVED_VIEWS_PATH.write_text(
        json.dumps({"scopes": scopes}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return vistas_normalizadas


def upsert_saved_view(nombre, variables, scope=DEFAULT_SCOPE):
    nombre_normalizado = _normalizar_nombre(nombre)
    variables_normalizadas = _normalizar_variables(variables)
    vistas = [vista for vista in load_saved_views(scope) if vista["name"] != nombre_normalizado]
    vistas.append({"name": nombre_normalizado, "variables": variables_normalizadas})
    return save_saved_views(vistas, scope)


def delete_saved_view(nombre, scope=DEFAULT_SCOPE):
    nombre_normalizado = _normalizar_nombre(nombre)
    vistas = [vista for vista in load_saved_views(scope) if vista["name"] != nombre_normalizado]
    return save_saved_views(vistas, scope)

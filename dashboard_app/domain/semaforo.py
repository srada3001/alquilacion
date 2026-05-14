import re

import pandas as pd


ETIQUETAS_UMBRALES = {
    "minimo": "Min",
    "normal": "Normal",
    "normal_sor": "Normal SOR",
    "normal_eor": "Normal EOR",
    "maximo": "Max",
}


def parsear_valor_numerico(valor):
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except TypeError:
        pass

    if isinstance(valor, (int, float)):
        numero = float(valor)
        return None if pd.isna(numero) else numero

    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return None

    texto = texto.replace("%", "").replace(" ", "")
    if re.search(r"[A-Za-z]", texto):
        return None
    if "-" in texto[1:] or "/" in texto or ":" in texto:
        return None

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif texto.count(",") == 1 and "." not in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_umbrales(registro):
    return {
        "minimo": parsear_valor_numerico(registro.get("minimo")),
        "normal": parsear_valor_numerico(registro.get("normal")),
        "normal_sor": parsear_valor_numerico(
            registro.get("normal_sor", registro.get("normal_SOR"))
        ),
        "normal_eor": parsear_valor_numerico(
            registro.get("normal_eor", registro.get("normal_EOR"))
        ),
        "maximo": parsear_valor_numerico(registro.get("maximo")),
    }


def construir_configuracion_semaforo(registro):
    umbrales = normalizar_umbrales(registro)
    minimo = umbrales["minimo"]
    normal = umbrales["normal"]
    normal_sor = umbrales["normal_sor"]
    normal_eor = umbrales["normal_eor"]
    maximo = umbrales["maximo"]

    if all(valor is not None for valor in (minimo, normal_sor, normal_eor, maximo)):
        if minimo < normal_sor < normal_eor < maximo:
            return {
                "caso": "minimo_normal_sor_normal_eor_maximo",
                "segmentos": [
                    ("advertencia", minimo, normal_sor),
                    ("normal", normal_sor, normal_eor),
                    ("advertencia", normal_eor, maximo),
                ],
                "limite_inferior": minimo,
                "limite_superior": maximo,
                "umbrales": umbrales,
            }

    if all(valor is not None for valor in (normal_sor, normal_eor, maximo)):
        if normal_sor < normal_eor < maximo:
            return {
                "caso": "normal_sor_normal_eor_maximo",
                "segmentos": [
                    ("normal", normal_sor, normal_eor),
                    ("advertencia", normal_eor, maximo),
                ],
                "limite_inferior": normal_sor,
                "limite_superior": maximo,
                "umbrales": umbrales,
            }

    if all(valor is not None for valor in (minimo, normal, maximo)):
        if minimo < normal < maximo:
            umbral_inferior = minimo + (normal - minimo) * 0.2
            umbral_superior = maximo - (maximo - normal) * 0.2
            return {
                "caso": "minimo_normal_maximo",
                "segmentos": [
                    ("advertencia", minimo, umbral_inferior),
                    ("normal", umbral_inferior, umbral_superior),
                    ("advertencia", umbral_superior, maximo),
                ],
                "limite_inferior": minimo,
                "limite_superior": maximo,
                "umbrales": umbrales,
            }

    if normal is not None and maximo is not None and normal < maximo:
        umbral_superior = maximo - (maximo - normal) * 0.2
        return {
            "caso": "normal_maximo",
            "segmentos": [
                ("normal", normal, umbral_superior),
                ("advertencia", umbral_superior, maximo),
            ],
            "limite_inferior": normal,
            "limite_superior": maximo,
            "umbrales": umbrales,
        }

    if minimo is not None and normal is not None and minimo < normal:
        umbral_inferior = minimo + (normal - minimo) * 0.2
        return {
            "caso": "minimo_normal",
            "segmentos": [
                ("advertencia", minimo, umbral_inferior),
                ("normal", umbral_inferior, normal),
            ],
            "limite_inferior": minimo,
            "limite_superior": normal,
            "umbrales": umbrales,
        }

    return {
        "caso": "sin_configuracion",
        "segmentos": None,
        "limite_inferior": None,
        "limite_superior": None,
        "umbrales": umbrales,
    }


def calcular_estado_semaforo(actual, configuracion):
    actual_num = parsear_valor_numerico(actual)
    segmentos = configuracion.get("segmentos")
    limite_inferior = configuracion.get("limite_inferior")
    limite_superior = configuracion.get("limite_superior")

    if actual_num is None or not segmentos:
        return "sin_datos"
    if actual_num < limite_inferior or actual_num > limite_superior:
        return "critico"
    return next(
        (
            estado
            for estado, inicio, fin in segmentos
            if inicio <= actual_num <= fin
        ),
        "sin_datos",
    )


def construir_anotaciones_umbral(umbrales):
    anotaciones = []
    for clave, etiqueta in ETIQUETAS_UMBRALES.items():
        valor = umbrales.get(clave)
        if valor is None:
            continue
        anotaciones.append(
            {
                "x": valor,
                "text": etiqueta,
                "y": 0.48,
                "size": 10,
            }
        )
    return anotaciones

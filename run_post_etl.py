from pathlib import Path

import pandas as pd

from config import get_processed_output_path
from data_processing.analysis_dataset import (
    build_combined_dataset_1h,
    build_combined_dataset_5m,
    get_combined_dataset_path_1h,
    get_combined_dataset_path_5m,
)
from data_processing.kalman import aplicar_filtro_kalman


KALMAN_PROCESS_VARIANCE = 0.0005
KALMAN_MEASUREMENT_VARIANCE = 100.0
LEGACY_DERIVED_PHASE_NAME = "variables_derivadas"
FT3_TO_BBL = 1 / 5.614583333333333

VARIABLES_KALMAN = {
    "tratadores_e_intercambiadores_de_butano": {
        "AI-1224A": "AI-1224A-Kalman",
        "AI-1224B": "AI-1224B-Kalman",
    },
}

VARIABLES_PREFILTRADAS = {
    "lab_R-202": {
        "Relacion 2C-4=/1C-4=": {
            "columna_nueva": "Relacion 2C-4=/1C-4=-Prefiltrada",
            "min": None,
            "max": 13,
        },
    },
    "lab_isobutano_reciclo": {
        "Relacion 1 Ol/iso": {
            "columna_nueva": "Relacion 1 Ol/iso-Prefiltrada",
            "min": 0,
            "max": 25,
        },
        "Relacion 2 Ol/iso": {
            "columna_nueva": "Relacion 2 Ol/iso-Prefiltrada",
            "min": 0,
            "max": 25,
        },
    },
}

VARIABLES_DERIVADAS = {
    "despropanizadora_y_despojo": {
        "columna_nueva": "Relación de vapor de cima y carga",
        "numerador": "FI-1148",
        "numerador_bpd": "FI-1148BPD",
        "denominador": "FIC-1145",
    },
}


def cargar_fase(fase):
    parquet_path = Path(get_processed_output_path(fase))
    if not parquet_path.exists():
        return pd.DataFrame(), parquet_path

    df = pd.read_parquet(parquet_path)
    df.index = pd.to_datetime(df.index)
    return df, parquet_path


def aplicar_variables_kalman(df, reglas):
    df_actualizado = df.copy()
    columnas_generadas = []

    for columna_origen, columna_nueva in reglas.items():
        if columna_origen not in df_actualizado.columns:
            continue

        serie = aplicar_filtro_kalman(
            df_actualizado[columna_origen],
            process_variance=KALMAN_PROCESS_VARIANCE,
            measurement_variance=KALMAN_MEASUREMENT_VARIANCE,
        )
        df_actualizado[columna_nueva] = pd.Series(serie, index=df_actualizado.index)
        df_actualizado = df_actualizado.drop(columns=[columna_origen])
        columnas_generadas.append(columna_nueva)

    return df_actualizado, columnas_generadas


def aplicar_variables_prefiltradas(df, reglas):
    df_actualizado = df.copy()
    columnas_generadas = []

    for columna_origen, regla in reglas.items():
        if columna_origen not in df_actualizado.columns:
            continue

        serie = df_actualizado[columna_origen]
        valor_minimo = regla.get("min")
        valor_maximo = regla.get("max")

        if valor_minimo is None:
            serie = serie.where(serie <= valor_maximo)
        elif valor_maximo is None:
            serie = serie.where(serie >= valor_minimo)
        else:
            serie = serie.where(
                serie.between(valor_minimo, valor_maximo, inclusive="both")
            )

        df_actualizado[regla["columna_nueva"]] = serie
        df_actualizado = df_actualizado.drop(columns=[columna_origen])
        columnas_generadas.append(regla["columna_nueva"])

    return df_actualizado, columnas_generadas


def aplicar_variables_derivadas(df, reglas):
    df_actualizado = df.copy()
    columnas_generadas = []

    for regla in reglas:
        numerador_bpd = regla["numerador_bpd"]

        if numerador_bpd in df_actualizado.columns:
            numerador = df_actualizado[numerador_bpd]
        elif regla["numerador"] in df_actualizado.columns:
            numerador = df_actualizado[regla["numerador"]] * FT3_TO_BBL
        else:
            continue

        denominador_col = regla["denominador"]
        if denominador_col not in df_actualizado.columns:
            continue

        denominador = df_actualizado[denominador_col].replace(0, pd.NA)
        df_actualizado[regla["columna_nueva"]] = numerador / denominador
        columnas_generadas.append(regla["columna_nueva"])

    return df_actualizado, columnas_generadas


def actualizar_fase(
    fase,
    reglas_kalman=None,
    reglas_prefiltradas=None,
    reglas_derivadas=None,
):
    df, output_path = cargar_fase(fase)
    if df.empty:
        return output_path, []

    columnas_generadas = []
    df_actualizado = df

    if reglas_kalman:
        df_actualizado, nuevas_kalman = aplicar_variables_kalman(df_actualizado, reglas_kalman)
        columnas_generadas.extend(nuevas_kalman)

    if reglas_prefiltradas:
        df_actualizado, nuevas_prefiltradas = aplicar_variables_prefiltradas(
            df_actualizado,
            reglas_prefiltradas,
        )
        columnas_generadas.extend(nuevas_prefiltradas)

    if reglas_derivadas:
        df_actualizado, nuevas_derivadas = aplicar_variables_derivadas(
            df_actualizado,
            reglas_derivadas,
        )
        columnas_generadas.extend(nuevas_derivadas)

    if columnas_generadas:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_actualizado.to_parquet(output_path, engine="pyarrow")

    return output_path, columnas_generadas


def construir_fases_post_etl():
    fases = (
        set(VARIABLES_KALMAN)
        | set(VARIABLES_PREFILTRADAS)
        | set(VARIABLES_DERIVADAS)
    )
    return sorted(fases)


def eliminar_fase_derivada_legacy():
    legacy_path = Path(get_processed_output_path(LEGACY_DERIVED_PHASE_NAME))
    if legacy_path.exists():
        legacy_path.unlink()
        return legacy_path
    return None


def main():
    legacy_path = eliminar_fase_derivada_legacy()
    if legacy_path is not None:
        print(f"Eliminado legado: {legacy_path.name}")

    for fase in construir_fases_post_etl():
        output_path, columnas_generadas = actualizar_fase(
            fase,
            reglas_kalman=VARIABLES_KALMAN.get(fase),
            reglas_prefiltradas=VARIABLES_PREFILTRADAS.get(fase),
            reglas_derivadas=VARIABLES_DERIVADAS.get(fase),
        )

        if columnas_generadas:
            print(f"Actualizado: {output_path.name} -> {', '.join(columnas_generadas)}")
        else:
            print(f"Sin cambios: {output_path.name}")

    combinado_5m = build_combined_dataset_5m()
    combinado_1h = build_combined_dataset_1h()
    print(
        f"Dataset combinado generado: {get_combined_dataset_path_5m()} "
        f"-> {combinado_5m.shape[0]} filas, {combinado_5m.shape[1]} columnas"
    )
    print(
        f"Dataset combinado generado: {get_combined_dataset_path_1h()} "
        f"-> {combinado_1h.shape[0]} filas, {combinado_1h.shape[1]} columnas"
    )


if __name__ == "__main__":
    main()

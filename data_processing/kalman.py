import pandas as pd


def aplicar_filtro_kalman(
    serie,
    process_variance=0.0005,
    measurement_variance=100.0,
    initial_variance=1.0,
):
    observada = pd.to_numeric(serie, errors="coerce")
    estimada = []
    estimacion_actual = None
    varianza_actual = initial_variance

    for valor in observada:
        if pd.isna(valor):
            estimada.append(pd.NA)
            continue

        if estimacion_actual is None:
            estimacion_actual = float(valor)
            estimada.append(estimacion_actual)
            continue

        varianza_predicha = varianza_actual + process_variance
        ganancia = varianza_predicha / (
            varianza_predicha + measurement_variance
        )
        estimacion_actual = estimacion_actual + ganancia * (
            float(valor) - estimacion_actual
        )
        varianza_actual = (1 - ganancia) * varianza_predicha
        estimada.append(estimacion_actual)

    return pd.Series(estimada, index=serie.index, dtype="Float64")

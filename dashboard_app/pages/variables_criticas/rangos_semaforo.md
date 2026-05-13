# Rangos del semaforo

La visualizacion de variables criticas usa estas columnas del archivo `variables_criticas.csv`:

- `TAG`
- `Descripción`
- `Valor medido`
- `Mínimo`
- `Normal`
- `Normal SOR`
- `Normal EOR`
- `Máximo`

La columna `comentario` puede seguir existiendo en el CSV, pero no se muestra en el dashboard.

## Caso 1

Si existen `Normal SOR`, `Normal EOR` y `Máximo`, y no existen `Mínimo` ni `Normal`:

- Verde entre `Normal SOR` y `Normal EOR`
- Amarillo entre `Normal EOR` y `Máximo`
- Rojo por debajo de `Normal SOR` o por encima de `Máximo`

## Caso 2

Si existen `Mínimo`, `Normal` y `Máximo`, y no existen `Normal SOR` ni `Normal EOR`:

- El rango se divide en dos tramos independientes: `Mínimo -> Normal` y `Normal -> Máximo`
- El 20 % se calcula por separado dentro de cada tramo, tomando como referencia a `Normal`
- Amarillo en el 20 % mas cercano al `Mínimo`
- Verde entre ese umbral y el umbral superior
- Amarillo en el 20 % mas cercano al `Máximo`
- Rojo por fuera de `Mínimo` y `Máximo`

## Caso 3

Si existen solo `Normal` y `Máximo`:

- Verde en el 80 % inicial del rango entre `Normal` y `Máximo`
- Amarillo en el 20 % final antes de `Máximo`
- Rojo por fuera de `Normal` y `Máximo`

## Encabezados esperados

El codigo ahora espera esos encabezados exactamente como estan escritos arriba.

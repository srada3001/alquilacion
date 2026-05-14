# Rangos del semáforo en Monitoreo por secciones

La vista de `Monitoreo por secciones` toma los rangos desde `data/metadata/saved_views.json`.

Para cada variable se usa:

- El último valor no nulo disponible dentro del 31 de diciembre del año anterior.
- Los campos `minimo`, `normal`, `normal_SOR`, `normal_EOR` y `maximo` cuando puedan convertirse a número.

El parser acepta:

- Números enteros.
- Decimales con punto o con coma, por ejemplo `2.5`, `2,5`, `7423,52`.
- Porcentajes simples, por ejemplo `55%`.

No se construye semáforo cuando el rango tiene texto no numérico o ambiguo, por ejemplo `40-50%` o `5-Mar`.

## Caso 1

Si existen `minimo`, `normal_SOR`, `normal_EOR` y `maximo`, y están ordenados:

- Amarillo entre `minimo` y `normal_SOR`
- Verde entre `normal_SOR` y `normal_EOR`
- Amarillo entre `normal_EOR` y `maximo`
- Rojo por fuera de `minimo` y `maximo`

Ejemplos actuales:

- `carga_de_reactores_de_SHP | TIC-4022`
- `Reactor de SHP y despojadora | TI-4135` cuando el `scope` se resuelve al nombre real de fase

## Caso 2

Si existen `normal_SOR`, `normal_EOR` y `maximo`, y no hay un mínimo usable:

- Verde entre `normal_SOR` y `normal_EOR`
- Amarillo entre `normal_EOR` y `maximo`
- Rojo por debajo de `normal_SOR` o por encima de `maximo`

Este caso conserva la lógica base documentada para `variables_criticas`.

## Caso 3

Si existen `minimo`, `normal` y `maximo`:

- Se parte el rango en dos tramos: `minimo -> normal` y `normal -> maximo`
- El 20 % más cercano a `minimo` es amarillo
- La zona central es verde
- El 20 % más cercano a `maximo` es amarillo
- Rojo por fuera de `minimo` y `maximo`

Ejemplos actuales:

- `reactor_de_alquilacion | FIC-1047`
- `tratamiento_de_efluentes | LI-1285`

## Caso 4

Si existen solo `normal` y `maximo`:

- Verde en el 80 % inicial del tramo `normal -> maximo`
- Amarillo en el 20 % final antes de `maximo`
- Rojo por debajo de `normal` o por encima de `maximo`

Ejemplos actuales:

- `tratadores_e_intercambiadores_de_butano | TI-1305`
- `tratamiento_de_efluentes | FI-1288`

## Caso 5

Si existen solo `minimo` y `normal`:

- Amarillo en el 20 % más cercano a `minimo`
- Verde desde ese umbral hasta `normal`
- Rojo por debajo de `minimo` o por encima de `normal`

Ejemplos actuales:

- `tratadores_e_intercambiadores_de_propano | FI-2423A`
- `isostripper | TI-1563`

## Caso 6

Si no hay suficientes valores numéricos o el orden del rango es inválido:

- No se dibuja semáforo útil
- La fila queda como `sin_datos`

Ejemplos actuales:

- `reactor_de_alquilacion | LI-1072`, porque mezcla porcentaje invertido y `normal` como rango textual
- `horno_isostripper | AI-1512A`, porque `normal` llega como `5-Mar`
- Cualquier variable nueva guardada sin rangos todavía configurados

## Nota para nuevas vistas

Cuando se crea una vista nueva desde el dashboard:

- Se guarda siempre la relación `scope + tag`
- Si la variable ya existía en otra vista, reutiliza su descripción y sus rangos conocidos
- Si nunca había existido, se guarda con descripción básica y sin rangos, por lo que el semáforo quedará en `sin_datos` hasta completar el JSON

# Alquilacion

Proyecto para procesar datos de fases mediante un ETL, enriquecerlos en un post-ETL
y visualizarlos en una app Dash.

## Componentes principales

- `dashboard_app.py`: entrypoint de la app de visualizacion de datos procesados.
- `run_etl.py`: entrypoint para ejecutar el ETL completo.
- `config.py`: configuracion compartida de rutas y nombres de archivos.
- `etl/`: paquete con la logica de extraccion, transformacion, carga y utilidades.
- `dashboard_app/`: paquete con la logica, layout y callbacks del dashboard.
- `data/`: carpeta con datos originales, outputs base por fase, datasets unificados, logs y resumenes.

## Estructura esperada de datos

```text
data/
  data_original/
    <fase>/
      <parte_1>/
        archivo1.csv
        archivo2.csv
      <parte_2>/
        archivo3.csv
  outputs/
    <fase>.parquet
  analysis/
    all_phases_5min.parquet
    all_phases_1h.parquet
  logs/
    <fase>.log
  resumenes/
    <fase>.csv
```

## Flujo de trabajo

1. Colocar los CSV de entrada en `data/data_original/<fase>/<parte>/`.
2. Ejecutar el ETL para generar parquets base por fase a 5 minutos, logs y resumenes.
3. Ejecutar el post-proceso para agregar variables derivadas y generar los datasets unificados a 5 minutos y 1 hora.
4. Abrir la app para visualizar y analizar usando los datasets unificados.

## Ejecucion

Ejecutar ETL:

```bash
python run_etl.py
```

Ejecutar el post-proceso de variables derivadas:

```bash
python run_post_etl.py
```

Ejecutar la app:

```bash
python dashboard_app.py
```

## Convenciones

- Cada fase tiene una carpeta dentro de `data/data_original`.
- Cada output procesado base se guarda como `data/outputs/<fase>.parquet` con frecuencia de 5 minutos.
- Los datasets listos para analisis se guardan como `data/analysis/all_phases_5min.parquet` y `data/analysis/all_phases_1h.parquet`.
- Cada log se guarda como `data/logs/<fase>.log`.
- Cada resumen se guarda como `data/resumenes/<fase>.csv`.
- La app lista fases a partir de las columnas presentes en los datasets unificados.

## Dependencias principales

- `pandas`
- `pyarrow`
- `dash`
- `plotly`

## Notas

- La app permite comparary relacionar multiples fases al mismo tiempo.
- Se usa intencionalmente una frecuencia base de 5 minutos para facilitar la coherencia entre fases (algunas fueron tomadas fon frecuencia 1m y otras con frecuencia 5m).
- Se espera que en el futuro la data faltante se incorpore con frecuencia de 1 minuto y se hagan los ajustes necesarios.
- Dos filtros en vez de uno
y que las histograma y todo eso se ajsute a lo sfiltros
- AADIR HISTOGRAMA, TABLA MAX, MIN, MEAN, PORCENTAJES, K-means, barra busqueda variables, correlacion calcular atumamtico con modo manual.
- Despues de filtrar mostrar cantidad de datos y tiempo
- Queremos las correlaciones con todas las variables de todos los datasets

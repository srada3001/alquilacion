# Alquilacion

Proyecto para procesar datos de fases mediante un ETL y visualizarlos en una app Dash.

## Componentes principales

- `app.py`: app de visualizacion de datos procesados.
- `run_etl.py`: entrypoint para ejecutar el ETL completo.
- `config.py`: configuracion compartida de rutas y nombres de archivos.
- `etl/`: paquete con la logica de extraccion, transformacion, carga y utilidades.
- `data/`: carpeta con datos originales, outputs, logs y resumenes.

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
  logs/
    <fase>.log
  resumenes/
    <fase>.csv
```

## Flujo de trabajo

1. Colocar los CSV de entrada en `data/data_original/<fase>/<parte>/`.
2. Ejecutar el ETL para generar parquet, logs y resumenes.
3. Abrir la app para visualizar las fases con output disponible.

## Ejecucion

Ejecutar ETL:

```bash
python run_etl.py
```

Ejecutar la app:

```bash
python app.py
```

## Convenciones

- Cada fase tiene una carpeta dentro de `data/data_original`.
- Cada output procesado se guarda como `data/outputs/<fase>.parquet`.
- Cada log se guarda como `data/logs/<fase>.log`.
- Cada resumen se guarda como `data/resumenes/<fase>.csv`.
- La app lista fases a partir de los `.parquet` disponibles en `data/outputs`.

## Dependencias principales

- `pandas`
- `pyarrow`
- `dash`
- `plotly`

## Notas

- La app carga una fase a la vez.
- Si los datasets son muy grandes, conviene considerar salidas agregadas para visualizacion, por ejemplo por hora o por bloques de tiempo.

# Influence Analysis

Analisis transversal para identificar variables que podrian influir sobre:

- `tratadores_e_intercambiadores_de_butano | AI-1224A`
- `tratadores_e_intercambiadores_de_butano | AI-1224B`
- `tratadores_e_intercambiadores_de_butano | AI-1224A-kalman`
- `tratadores_e_intercambiadores_de_butano | AI-1224B-kalman`

Este modulo es independiente del dashboard. Trabaja sobre el dataset
unificado de 5 minutos generado por el post-ETL en
`data/analysis/all_phases_5min.parquet` para estudiar relaciones
contemporaneas, retardadas y no lineales entre variables de todas las fases.

## Metodologia

El script principal:

1. Carga y unifica todas las fases a frecuencia de 5 minutos.
2. Usa como targets tanto las variables originales como sus versiones filtradas
   con Kalman.
3. Excluye de las features las columnas derivadas de post-proceso para evitar
   rankings artificiales.
4. Busca la mejor correlacion de Pearson por variable considerando retardos.
5. Calcula correlacion de Spearman para captar dependencias monotonicas menos
   sensibles a outliers.
6. Calcula informacion mutua para captar relaciones no lineales.
7. Calcula transfer entropy para un subconjunto de candidatas fuertes.
8. Entrena un modelo `RandomForestRegressor` exogeno para estimar importancia
   conjunta de variables con rezago.
9. Genera tablas CSV, figuras PNG y un reporte Markdown.

## Ejecucion

```bash
python influence_analysis/run_analysis.py
```

## Salidas

Las salidas se guardan en `influence_analysis/outputs/`:

- `*_lag_screening.csv`
- `*_top_candidates.csv`
- `*_random_forest_importance.csv`
- `*_summary.csv`
- `*.png`
- `report.md`

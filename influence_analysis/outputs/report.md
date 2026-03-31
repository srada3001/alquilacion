# Reporte de influencias sobre AI-1224A y AI-1224B

Este reporte se genero de forma automatica a partir de los parquets de 5 minutos
de todas las fases. El objetivo es priorizar variables que podrian influir
sobre los medidores de oxigeno originales y sus versiones filtradas con Kalman,
considerando retardos y relaciones no lineales.

## Alcance del analisis

- Frecuencia usada: `5min`.
- Rango temporal observado: `2017-04-15 00:00:00` a `2026-02-28 23:55:00`.
- Variables numericas evaluadas: `345`.
- Targets evaluados: `4`.
- Retardos evaluados: `63` posiciones sobre la grilla de 5 minutos, hasta `2880min (48.00h)`.
- Metodos usados: correlacion de Pearson con rezago, correlacion de Spearman con rezago, informacion mutua, transfer entropy y Random Forest exogeno.


## tratadores_e_intercambiadores_de_butano | AI-1224A

- Muestras no nulas del target: `929548`.
- Features cribadas con rezago: `338`.
- Random Forest exogeno, R2 en test: `0.836`.
- Random Forest exogeno, MAE en test: `2.321`.

### Top variables candidatas

- `tratadores_e_intercambiadores_de_butano | AI-1224B`: lag=0min (0.00h), corr=-0.805, spearman=-0.859, consenso=0.905
- `debutanizadora_y_tratamiento_de_alquilato | TIC-2103`: lag=90min (1.50h), corr=-0.581, spearman=-0.756, consenso=0.505
- `debutanizadora_y_tratamiento_de_alquilato | TI-2105`: lag=75min (1.25h), corr=-0.475, spearman=-0.762, consenso=0.336
- `debutanizadora_y_tratamiento_de_alquilato | TI-1567`: lag=90min (1.50h), corr=-0.495, spearman=-0.437, consenso=0.302
- `isostripper | TI-1567`: lag=240min (4.00h), corr=-0.492, spearman=-0.406, consenso=0.290
- `tratadores_e_intercambiadores_de_propano | TIC-2400`: lag=420min (7.00h), corr=-0.606, spearman=-0.347, consenso=0.286
- `horno | FIC-1903C-F-2-OLEFINAS`: lag=270min (4.50h), corr=-0.526, spearman=-0.354, consenso=0.274
- `horno | FI-1903B-F-2-OLEFINAS`: lag=270min (4.50h), corr=-0.515, spearman=-0.363, consenso=0.274
- `reactor_de_alquilacion | FIC-1903C`: lag=270min (4.50h), corr=-0.511, spearman=-0.341, consenso=0.269
- `reactor_de_alquilacion | FI-1903B`: lag=270min (4.50h), corr=-0.501, spearman=-0.349, consenso=0.268
- `horno | FI-1059A-F-1-OLEFINAS`: lag=255min (4.25h), corr=-0.505, spearman=-0.332, consenso=0.264
- `psh | LI-4040`: lag=420min (7.00h), corr=-0.552, spearman=-0.328, consenso=0.263

### Lectura metodologica

- `corr` refleja la mejor correlacion lineal encontrada dentro de la grilla de retardos.
- `spearman` agrega una lectura monotona mas robusta frente a no linealidades suaves y outliers.
- El puntaje de consenso combina Pearson, Spearman, informacion mutua, transfer entropy e importancia en Random Forest.
- Un puntaje alto no prueba causalidad fisica por si mismo, pero si prioriza variables para revision de proceso.

## tratadores_e_intercambiadores_de_butano | AI-1224B

- Muestras no nulas del target: `930971`.
- Features cribadas con rezago: `338`.
- Random Forest exogeno, R2 en test: `0.785`.
- Random Forest exogeno, MAE en test: `3.020`.

### Top variables candidatas

- `tratadores_e_intercambiadores_de_butano | AI-1224A`: lag=0min (0.00h), corr=-0.805, spearman=-0.859, consenso=0.880
- `debutanizadora_y_tratamiento_de_alquilato | TI-2105`: lag=75min (1.25h), corr=0.669, spearman=0.850, consenso=0.556
- `debutanizadora_y_tratamiento_de_alquilato | TI-2102`: lag=90min (1.50h), corr=0.630, spearman=0.761, consenso=0.470
- `isostripper | TI-1565`: lag=75min (1.25h), corr=0.656, spearman=0.528, consenso=0.363
- `debutanizadora_y_tratamiento_de_alquilato | TI-1567`: lag=90min (1.50h), corr=0.628, spearman=0.515, consenso=0.337
- `isostripper | TI-1567`: lag=90min (1.50h), corr=0.627, spearman=0.514, consenso=0.336
- `tratadores_e_intercambiadores_de_propano | TI-2403`: lag=210min (3.50h), corr=0.703, spearman=0.353, consenso=0.315
- `debutanizadora_y_tratamiento_de_alquilato | TIC-2103`: lag=90min (1.50h), corr=0.587, spearman=0.748, consenso=0.313
- `tratadores_e_intercambiadores_de_propano | TI-2401`: lag=285min (4.75h), corr=0.676, spearman=0.405, consenso=0.312
- `debutanizadora_y_tratamiento_de_alquilato | FIC-2100`: lag=255min (4.25h), corr=0.652, spearman=0.396, consenso=0.310
- `isostripper | TI-1571`: lag=90min (1.50h), corr=0.604, spearman=0.552, consenso=0.307
- `isostripper | FIC-2100`: lag=255min (4.25h), corr=0.649, spearman=0.392, consenso=0.306

### Lectura metodologica

- `corr` refleja la mejor correlacion lineal encontrada dentro de la grilla de retardos.
- `spearman` agrega una lectura monotona mas robusta frente a no linealidades suaves y outliers.
- El puntaje de consenso combina Pearson, Spearman, informacion mutua, transfer entropy e importancia en Random Forest.
- Un puntaje alto no prueba causalidad fisica por si mismo, pero si prioriza variables para revision de proceso.

## tratadores_e_intercambiadores_de_butano | AI-1224A-kalman

- Muestras no nulas del target: `929548`.
- Features cribadas con rezago: `338`.
- Random Forest exogeno, R2 en test: `0.823`.
- Random Forest exogeno, MAE en test: `3.909`.

### Top variables candidatas

- `tratadores_e_intercambiadores_de_butano | AI-1224B`: lag=40min (0.67h), corr=-0.816, spearman=-0.877, consenso=1.000
- `debutanizadora_y_tratamiento_de_alquilato | TIC-2103`: lag=120min (2.00h), corr=-0.595, spearman=-0.779, consenso=0.506
- `debutanizadora_y_tratamiento_de_alquilato | TI-2105`: lag=120min (2.00h), corr=-0.486, spearman=-0.778, consenso=0.380
- `debutanizadora_y_tratamiento_de_alquilato | TI-1567`: lag=150min (2.50h), corr=-0.507, spearman=-0.445, consenso=0.315
- `isostripper | TI-1567`: lag=255min (4.25h), corr=-0.504, spearman=-0.428, consenso=0.315
- `tratadores_e_intercambiadores_de_propano | TIC-2400`: lag=480min (8.00h), corr=-0.622, spearman=-0.362, consenso=0.296
- `horno | FIC-1903C-F-2-OLEFINAS`: lag=315min (5.25h), corr=-0.538, spearman=-0.373, consenso=0.285
- `horno | FI-1903B-F-2-OLEFINAS`: lag=315min (5.25h), corr=-0.527, spearman=-0.382, consenso=0.285
- `reactor_de_alquilacion | FI-1903B`: lag=330min (5.50h), corr=-0.512, spearman=-0.369, consenso=0.279
- `reactor_de_alquilacion | FIC-1903C`: lag=315min (5.25h), corr=-0.524, spearman=-0.361, consenso=0.278
- `psh | FIC-4061`: lag=345min (5.75h), corr=-0.503, spearman=-0.365, consenso=0.274
- `horno | FI-1059A-F-1-OLEFINAS`: lag=315min (5.25h), corr=-0.517, spearman=-0.355, consenso=0.273

### Lectura metodologica

- `corr` refleja la mejor correlacion lineal encontrada dentro de la grilla de retardos.
- `spearman` agrega una lectura monotona mas robusta frente a no linealidades suaves y outliers.
- El puntaje de consenso combina Pearson, Spearman, informacion mutua, transfer entropy e importancia en Random Forest.
- Un puntaje alto no prueba causalidad fisica por si mismo, pero si prioriza variables para revision de proceso.

## tratadores_e_intercambiadores_de_butano | AI-1224B-kalman

- Muestras no nulas del target: `930971`.
- Features cribadas con rezago: `338`.
- Random Forest exogeno, R2 en test: `0.672`.
- Random Forest exogeno, MAE en test: `4.621`.

### Top variables candidatas

- `tratadores_e_intercambiadores_de_butano | AI-1224A`: lag=35min (0.58h), corr=-0.807, spearman=-0.853, consenso=0.986
- `debutanizadora_y_tratamiento_de_alquilato | TI-2105`: lag=120min (2.00h), corr=0.678, spearman=0.851, consenso=0.602
- `debutanizadora_y_tratamiento_de_alquilato | TI-2102`: lag=120min (2.00h), corr=0.639, spearman=0.766, consenso=0.519
- `isostripper | TI-1565`: lag=120min (2.00h), corr=0.664, spearman=0.529, consenso=0.392
- `isostripper | TI-1567`: lag=135min (2.25h), corr=0.637, spearman=0.517, consenso=0.372
- `debutanizadora_y_tratamiento_de_alquilato | TI-1567`: lag=135min (2.25h), corr=0.637, spearman=0.518, consenso=0.370
- `tratadores_e_intercambiadores_de_propano | TI-2405`: lag=240min (4.00h), corr=0.683, spearman=0.285, consenso=0.341
- `debutanizadora_y_tratamiento_de_alquilato | FIC-2100`: lag=315min (5.25h), corr=0.661, spearman=0.408, consenso=0.340
- `tratadores_e_intercambiadores_de_propano | TI-2401`: lag=330min (5.50h), corr=0.686, spearman=0.410, consenso=0.338
- `isostripper | TI-1571`: lag=120min (2.00h), corr=0.612, spearman=0.555, consenso=0.337
- `tratadores_e_intercambiadores_de_propano | TI-2403`: lag=255min (4.25h), corr=0.714, spearman=0.358, consenso=0.335
- `isostripper | FIC-2100`: lag=315min (5.25h), corr=0.658, spearman=0.404, consenso=0.335

### Lectura metodologica

- `corr` refleja la mejor correlacion lineal encontrada dentro de la grilla de retardos.
- `spearman` agrega una lectura monotona mas robusta frente a no linealidades suaves y outliers.
- El puntaje de consenso combina Pearson, Spearman, informacion mutua, transfer entropy e importancia en Random Forest.
- Un puntaje alto no prueba causalidad fisica por si mismo, pero si prioriza variables para revision de proceso.

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyinform import transfer_entropy
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis_dataset import load_combined_dataset_5m


OUTPUT_DIR = Path("influence_analysis") / "outputs"
TARGETS = [
    "tratadores_e_intercambiadores_de_butano | AI-1224A",
    "tratadores_e_intercambiadores_de_butano | AI-1224B",
    "tratadores_e_intercambiadores_de_butano | AI-1224A-kalman",
    "tratadores_e_intercambiadores_de_butano | AI-1224B-kalman",
]
MIN_OVERLAP = 4000
TOP_SCREENING = 50
TOP_MI = 30
TOP_TE = 20
TOP_MODEL_FEATURES = 24
SCREENING_SAMPLE_SIZE = 120000
MI_SAMPLE_SIZE = 25000
TE_SAMPLE_SIZE = 12000
MODEL_SAMPLE_SIZE = 220000
RANDOM_STATE = 42


def build_lag_steps():
    lags = set(range(0, 13))
    lags.update(range(15, 73, 3))
    lags.update(range(84, 289, 12))
    lags.update(range(312, 577, 24))
    return sorted(lags)


LAG_STEPS = build_lag_steps()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def is_derived_column(column):
    lowered = column.lower()
    return (
        lowered.endswith("-kalman")
        or lowered.endswith("-desviacion")
        or lowered.endswith("-desviación")
    )


def base_sensor_name(column):
    sensor = column.split("|")[-1].strip()
    sensor = re.sub(r"-(kalman|desviacion|desviación)$", "", sensor, flags=re.IGNORECASE)
    return sensor


def lag_label(lag_steps):
    minutes = lag_steps * 5
    hours = minutes / 60
    return f"{minutes}min ({hours:.2f}h)"


def load_combined_dataframe():
    return load_combined_dataset_5m()


def sample_rows(frame, max_rows):
    if len(frame) <= max_rows:
        return frame
    idx = np.linspace(0, len(frame) - 1, num=max_rows, dtype=int)
    return frame.iloc[idx]


def candidate_columns(df, target_name):
    target_base = base_sensor_name(target_name)
    cols = []
    for column in df.columns:
        if column == target_name:
            continue
        if is_derived_column(column):
            continue
        if base_sensor_name(column) == target_base:
            continue
        cols.append(column)
    return cols


def compute_lag_screening(df, target_name):
    cols = candidate_columns(df, target_name)
    sampled = sample_rows(df[[target_name] + cols], SCREENING_SAMPLE_SIZE)
    target = sampled[target_name]
    target_rank = target.rank(method="average")
    results = []

    for column in cols:
        serie = sampled[column]
        best = None

        for lag in LAG_STEPS:
            shifted = serie.shift(lag)
            pair = pd.concat(
                [shifted.rename("feature"), target.rename("target")], axis=1
            ).dropna()

            if len(pair) < MIN_OVERLAP:
                continue
            if pair["feature"].nunique() <= 1 or pair["target"].nunique() <= 1:
                continue

            pearson = pair["feature"].corr(pair["target"])
            spearman = pair["feature"].rank(method="average").corr(
                pair["target"].rank(method="average")
            )
            if pd.isna(pearson):
                continue

            if best is None or abs(pearson) > abs(best["pearson"]):
                best = {
                    "feature": column,
                    "best_lag_steps": lag,
                    "best_lag_label": lag_label(lag),
                    "pearson": float(pearson),
                    "abs_pearson": float(abs(pearson)),
                    "spearman": float(spearman) if not pd.isna(spearman) else np.nan,
                    "abs_spearman": float(abs(spearman)) if not pd.isna(spearman) else np.nan,
                    "samples": int(len(pair)),
                }

        if best is not None:
            results.append(best)

    screening = pd.DataFrame(results).sort_values(
        ["abs_pearson", "abs_spearman", "samples"],
        ascending=[False, False, False],
    )
    return screening


def compute_mutual_information(df, target_name, screening):
    target = df[target_name]
    rows = []

    for row in screening.head(TOP_MI).itertuples(index=False):
        shifted = df[row.feature].shift(int(row.best_lag_steps))
        pair = pd.concat(
            [shifted.rename("feature"), target.rename("target")], axis=1
        ).dropna()

        if len(pair) < MIN_OVERLAP:
            continue

        pair = sample_rows(pair, MI_SAMPLE_SIZE)
        mi = mutual_info_regression(
            pair[["feature"]],
            pair["target"],
            random_state=RANDOM_STATE,
        )[0]
        rows.append(
            {
                "feature": row.feature,
                "best_lag_steps": int(row.best_lag_steps),
                "best_lag_label": row.best_lag_label,
                "mutual_information": float(mi),
                "samples": int(len(pair)),
            }
        )

    return pd.DataFrame(rows).sort_values(
        "mutual_information", ascending=False
    )


def discretize_series(series, bins=6):
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=bins, labels=False, duplicates="drop").astype(int)


def compute_transfer_entropy(df, target_name, screening):
    target = df[target_name]
    rows = []

    for row in screening.head(TOP_TE).itertuples(index=False):
        shifted = df[row.feature].shift(int(row.best_lag_steps))
        pair = pd.concat(
            [shifted.rename("feature"), target.rename("target")], axis=1
        ).dropna()

        if len(pair) < MIN_OVERLAP:
            continue

        pair = sample_rows(pair, TE_SAMPLE_SIZE)

        try:
            feature_disc = discretize_series(pair["feature"])
            target_disc = discretize_series(pair["target"])
            te_value = transfer_entropy(
                feature_disc.to_list(),
                target_disc.to_list(),
                k=1,
            )
        except Exception:
            continue

        rows.append(
            {
                "feature": row.feature,
                "best_lag_steps": int(row.best_lag_steps),
                "best_lag_label": row.best_lag_label,
                "transfer_entropy": float(te_value),
                "samples": int(len(pair)),
            }
        )

    return pd.DataFrame(rows).sort_values(
        "transfer_entropy", ascending=False
    )


def build_model_matrix(df, target_name, screening, mi_df, te_df):
    selected = []

    frames = [
        screening.head(TOP_MODEL_FEATURES),
        mi_df.head(12) if mi_df is not None and not mi_df.empty else None,
        te_df.head(10) if te_df is not None and not te_df.empty else None,
    ]

    for frame in frames:
        if frame is None or frame.empty:
            continue
        for row in frame.itertuples(index=False):
            if row.feature not in selected:
                selected.append(row.feature)

    lag_map = {
        row.feature: int(row.best_lag_steps)
        for row in screening.itertuples(index=False)
    }

    model_df = pd.DataFrame(index=df.index)
    for feature in selected[:TOP_MODEL_FEATURES]:
        lag = lag_map.get(feature, 0)
        model_df[f"{feature} [lag={lag}x5min]"] = df[feature].shift(lag)

    model_df["target"] = df[target_name]
    model_df = model_df.dropna(subset=["target"])
    model_df = sample_rows(model_df, MODEL_SAMPLE_SIZE)
    return model_df


def train_random_forest(model_df):
    if model_df.empty or model_df.shape[1] <= 1:
        return None

    split = int(len(model_df) * 0.8)
    if split <= 0 or split >= len(model_df):
        return None

    train = model_df.iloc[:split]
    test = model_df.iloc[split:]

    x_train = train.drop(columns=["target"])
    y_train = train["target"]
    x_test = test.drop(columns=["target"])
    y_test = test["target"]

    imputer = SimpleImputer(strategy="median")
    x_train_imp = imputer.fit_transform(x_train)
    x_test_imp = imputer.transform(x_test)

    model = RandomForestRegressor(
        n_estimators=250,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        min_samples_leaf=8,
    )
    model.fit(x_train_imp, y_train)
    predictions = model.predict(x_test_imp)

    perm = permutation_importance(
        model,
        x_test_imp,
        y_test,
        n_repeats=8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    importance = pd.DataFrame(
        {
            "feature": x_train.columns,
            "importance_mean": perm.importances_mean,
            "importance_std": perm.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    metrics = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_r2": float(r2_score(y_test, predictions)),
        "test_mae": float(mean_absolute_error(y_test, predictions)),
    }
    return importance, metrics


def normalize_scores(series):
    if series.empty:
        return series
    series = series.astype(float)
    min_v = series.min()
    max_v = series.max()
    if max_v == min_v:
        return pd.Series(1.0, index=series.index)
    return (series - min_v) / (max_v - min_v)


def merge_summary(screening, mi_df, te_df, rf_df):
    summary = screening[
        [
            "feature",
            "best_lag_steps",
            "best_lag_label",
            "pearson",
            "abs_pearson",
            "spearman",
            "abs_spearman",
            "samples",
        ]
    ].copy()

    if mi_df is not None and not mi_df.empty:
        summary = summary.merge(
            mi_df[["feature", "mutual_information"]],
            on="feature",
            how="left",
        )

    if te_df is not None and not te_df.empty:
        summary = summary.merge(
            te_df[["feature", "transfer_entropy"]],
            on="feature",
            how="left",
        )

    if rf_df is not None and not rf_df.empty:
        rf_compact = rf_df.copy()
        rf_compact["base_feature"] = rf_compact["feature"].str.replace(
            r" \[lag=\d+x5min\]$",
            "",
            regex=True,
        )
        rf_compact = (
            rf_compact.groupby("base_feature", as_index=False)["importance_mean"]
            .max()
            .rename(columns={"base_feature": "feature"})
        )
        summary = summary.merge(rf_compact, on="feature", how="left")

    summary["pearson_score"] = normalize_scores(summary["abs_pearson"].fillna(0))
    summary["spearman_score"] = normalize_scores(summary["abs_spearman"].fillna(0))
    summary["mi_score"] = normalize_scores(summary["mutual_information"].fillna(0))
    summary["te_score"] = normalize_scores(summary["transfer_entropy"].fillna(0))
    summary["rf_score"] = normalize_scores(summary["importance_mean"].fillna(0))
    summary["consensus_score"] = (
        0.25 * summary["pearson_score"]
        + 0.15 * summary["spearman_score"]
        + 0.20 * summary["mi_score"]
        + 0.15 * summary["te_score"]
        + 0.25 * summary["rf_score"]
    )
    summary = summary.sort_values("consensus_score", ascending=False)
    return summary


def plot_top_bar(frame, value_col, title, output_path, top_n=15):
    if frame is None or frame.empty:
        return

    top = frame.head(top_n).iloc[::-1]
    plt.figure(figsize=(12, 7))
    plt.barh(top["feature"], top[value_col])
    plt.title(title)
    plt.xlabel(value_col)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def write_report(sections):
    report_path = OUTPUT_DIR / "report.md"
    lines = [
        "# Reporte de influencias sobre AI-1224A y AI-1224B",
        "",
        "Este reporte se genero de forma automatica a partir del dataset unificado",
        "de 5 minutos con todas las fases. El objetivo es priorizar variables que podrian influir",
        "sobre los medidores de oxigeno originales y sus versiones filtradas con Kalman,",
        "considerando retardos y relaciones no lineales.",
        "",
    ]

    for section in sections:
        lines.extend(section)
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def format_top_lines(summary, n=10):
    lines = []
    for row in summary.head(n).itertuples(index=False):
        lines.append(
            f"- `{row.feature}`: lag={row.best_lag_label}, "
            f"corr={row.pearson:.3f}, spearman={row.spearman:.3f}, "
            f"consenso={row.consensus_score:.3f}"
        )
    return lines


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_combined_dataframe()
    report_sections = []

    overview = [
        "## Alcance del analisis",
        "",
        "- Frecuencia usada: `5min`.",
        f"- Rango temporal observado: `{df.index.min()}` a `{df.index.max()}`.",
        f"- Variables numericas evaluadas: `{len(df.columns)}`.",
        f"- Targets evaluados: `{len(TARGETS)}`.",
        f"- Retardos evaluados: `{len(LAG_STEPS)}` posiciones sobre la grilla de 5 minutos, hasta `{lag_label(max(LAG_STEPS))}`.",
        "- Metodos usados: correlacion de Pearson con rezago, correlacion de Spearman con rezago, informacion mutua, transfer entropy y Random Forest exogeno.",
        "",
    ]
    report_sections.append(overview)

    for target_name in TARGETS:
        print(f"Analizando {target_name}...")
        slug = slugify(target_name.split("|")[-1].strip())

        screening = compute_lag_screening(df, target_name)
        screening.to_csv(OUTPUT_DIR / f"{slug}_lag_screening.csv", index=False)

        mi_df = compute_mutual_information(df, target_name, screening)
        mi_df.to_csv(OUTPUT_DIR / f"{slug}_top_candidates.csv", index=False)

        te_df = compute_transfer_entropy(df, target_name, screening)
        te_df.to_csv(OUTPUT_DIR / f"{slug}_transfer_entropy.csv", index=False)

        model_df = build_model_matrix(df, target_name, screening, mi_df, te_df)
        rf_result = train_random_forest(model_df)
        if rf_result is None:
            rf_df = pd.DataFrame(columns=["feature", "importance_mean", "importance_std"])
            metrics = {}
        else:
            rf_df, metrics = rf_result
        rf_df.to_csv(OUTPUT_DIR / f"{slug}_random_forest_importance.csv", index=False)

        summary = merge_summary(screening, mi_df, te_df, rf_df)
        summary.to_csv(OUTPUT_DIR / f"{slug}_summary.csv", index=False)

        plot_top_bar(
            summary,
            "consensus_score",
            f"Top variables candidatas para {target_name}",
            OUTPUT_DIR / f"{slug}_consensus.png",
        )
        plot_top_bar(
            rf_df,
            "importance_mean",
            f"Importancia Random Forest para {target_name}",
            OUTPUT_DIR / f"{slug}_rf_importance.png",
        )

        section = [
            f"## {target_name}",
            "",
            f"- Muestras no nulas del target: `{int(df[target_name].notna().sum())}`.",
            f"- Features cribadas con rezago: `{len(screening)}`.",
        ]
        if metrics:
            section.extend(
                [
                    f"- Random Forest exogeno, R2 en test: `{metrics['test_r2']:.3f}`.",
                    f"- Random Forest exogeno, MAE en test: `{metrics['test_mae']:.3f}`.",
                ]
            )
        section.extend(
            [
                "",
                "### Top variables candidatas",
                "",
                *format_top_lines(summary, n=12),
                "",
                "### Lectura metodologica",
                "",
                "- `corr` refleja la mejor correlacion lineal encontrada dentro de la grilla de retardos.",
                "- `spearman` agrega una lectura monotona mas robusta frente a no linealidades suaves y outliers.",
                "- El puntaje de consenso combina Pearson, Spearman, informacion mutua, transfer entropy e importancia en Random Forest.",
                "- Un puntaje alto no prueba causalidad fisica por si mismo, pero si prioriza variables para revision de proceso.",
            ]
        )
        report_sections.append(section)

    write_report(report_sections)
    print(f"Reporte generado en {OUTPUT_DIR / 'report.md'}")


if __name__ == "__main__":
    main()

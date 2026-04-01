import numpy as np
import pandas as pd
from pyinform import transfer_entropy
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score


MIN_OVERLAP = 4000
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


def is_derived_column(column):
    lowered = column.lower()
    return lowered.endswith("-kalman") or lowered.endswith("-desviacion")


def base_sensor_name(column):
    sensor = column.split("|")[-1].strip()
    sensor = sensor.removesuffix("-kalman")
    sensor = sensor.removesuffix("-desviacion")
    return sensor


def lag_label(lag_steps):
    minutes = lag_steps * 5
    hours = minutes / 60
    return f"{minutes}min ({hours:.2f}h)"


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
    if not cols:
        return pd.DataFrame()

    sampled = sample_rows(df[[target_name] + cols], SCREENING_SAMPLE_SIZE)
    target = sampled[target_name]
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

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results).sort_values(
        ["abs_pearson", "abs_spearman", "samples"],
        ascending=[False, False, False],
    )


def compute_mutual_information(df, target_name, screening):
    if screening is None or screening.empty:
        return pd.DataFrame()

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

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("mutual_information", ascending=False)


def discretize_series(series, bins=6):
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=bins, labels=False, duplicates="drop").astype(int)


def compute_transfer_entropy(df, target_name, screening):
    if screening is None or screening.empty:
        return pd.DataFrame()

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

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values("transfer_entropy", ascending=False)


def build_model_matrix(df, target_name, screening, mi_df, te_df):
    if screening is None or screening.empty:
        return pd.DataFrame()

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
    return sample_rows(model_df, MODEL_SAMPLE_SIZE)


def train_random_forest(model_df):
    if model_df.empty or model_df.shape[1] <= 1:
        return pd.DataFrame(), {}

    split = int(len(model_df) * 0.8)
    if split <= 0 or split >= len(model_df):
        return pd.DataFrame(), {}

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


def merge_influence_summary(screening, mi_df, te_df, rf_df):
    if screening is None or screening.empty:
        return pd.DataFrame()

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
    return summary.sort_values("consensus_score", ascending=False)


def calcular_influencias_para_variable(df, columna_objetivo):
    if df.empty or columna_objetivo not in df.columns:
        return {
            "summary": pd.DataFrame(),
            "screening": pd.DataFrame(),
            "mi": pd.DataFrame(),
            "rf": pd.DataFrame(),
            "metrics": {},
        }

    screening = compute_lag_screening(df, columna_objetivo)
    mi_df = compute_mutual_information(df, columna_objetivo, screening)
    te_df = compute_transfer_entropy(df, columna_objetivo, screening)
    model_df = build_model_matrix(df, columna_objetivo, screening, mi_df, te_df)
    rf_df, metrics = train_random_forest(model_df)
    summary = merge_influence_summary(screening, mi_df, te_df, rf_df)

    return {
        "summary": summary,
        "screening": screening,
        "mi": mi_df,
        "te": te_df,
        "rf": rf_df,
        "metrics": metrics,
    }

import numpy as np
import pandas as pd
from pyinform import transfer_entropy
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score


MAX_MIN_OVERLAP = 4000
MIN_CONTEXT_OVERLAP = 36
MIN_CONTEXT_OVERLAP_RATIO = 0.5
MAX_RF_BATCH_FEATURES = 24
MIN_RF_BATCH_FEATURES = 4
MODEL_ROWS_PER_FEATURE = 12
SCREENING_SAMPLE_SIZE = 120000
MI_SAMPLE_SIZE = 25000
TE_SAMPLE_SIZE = 12000
MODEL_SAMPLE_SIZE = 220000
RANDOM_STATE = 42


def build_lag_steps():
    lags = set(range(0, 13))
    lags.update(range(15, 144, 3))
    return sorted(lags)


LAG_STEPS = build_lag_steps()


def is_derived_column(column):
    lowered = column.lower()
    return lowered.endswith("-kalman") or lowered.endswith("-prefiltrada")


def base_sensor_name(column):
    sensor = column.split("|")[-1].strip()
    sensor = sensor.removesuffix("-Kalman")
    sensor = sensor.removesuffix("-kalman")
    sensor = sensor.removesuffix("-Prefiltrada")
    sensor = sensor.removesuffix("-prefiltrada")
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


def build_analysis_config(df):
    context_rows = int(len(df.index))
    min_overlap = min(
        MAX_MIN_OVERLAP,
        max(MIN_CONTEXT_OVERLAP, int(context_rows * MIN_CONTEXT_OVERLAP_RATIO)),
    )
    max_lag_steps = max(0, context_rows - min_overlap)
    lag_steps = [lag for lag in LAG_STEPS if lag <= max_lag_steps] or [0]

    if context_rows >= 240:
        te_bins = 6
    elif context_rows >= 120:
        te_bins = 5
    elif context_rows >= 60:
        te_bins = 4
    else:
        te_bins = 3

    rf_batch_features = min(
        MAX_RF_BATCH_FEATURES,
        max(MIN_RF_BATCH_FEATURES, context_rows // MODEL_ROWS_PER_FEATURE),
    )

    return {
        "context_rows": context_rows,
        "min_overlap": min_overlap,
        "lag_steps": lag_steps,
        "te_bins": te_bins,
        "rf_batch_features": rf_batch_features,
    }


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


def chunk_values(values, chunk_size):
    if chunk_size <= 0:
        return
    for start in range(0, len(values), chunk_size):
        yield values[start : start + chunk_size]


def compute_lag_screening(df, target_name, analysis_config):
    cols = candidate_columns(df, target_name)
    if not cols:
        return pd.DataFrame()

    sampled = sample_rows(df[[target_name] + cols], SCREENING_SAMPLE_SIZE)
    target = sampled[target_name]
    results = []

    for column in cols:
        serie = sampled[column]
        best = None

        for lag in analysis_config["lag_steps"]:
            shifted = serie.shift(lag)
            pair = pd.concat(
                [shifted.rename("feature"), target.rename("target")], axis=1
            ).dropna()

            if len(pair) < analysis_config["min_overlap"]:
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


def compute_mutual_information(df, target_name, screening, analysis_config):
    if screening is None or screening.empty:
        return pd.DataFrame()

    target = df[target_name]
    rows = []

    for row in screening.itertuples(index=False):
        shifted = df[row.feature].shift(int(row.best_lag_steps))
        pair = pd.concat(
            [shifted.rename("feature"), target.rename("target")], axis=1
        ).dropna()

        if len(pair) < analysis_config["min_overlap"]:
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
    bins = max(2, min(int(bins), int(series.nunique()), int(len(series))))
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=bins, labels=False, duplicates="drop").astype(int)


def compute_transfer_entropy(df, target_name, screening, analysis_config):
    if screening is None or screening.empty:
        return pd.DataFrame()

    target = df[target_name]
    rows = []

    for row in screening.itertuples(index=False):
        shifted = df[row.feature].shift(int(row.best_lag_steps))
        pair = pd.concat(
            [shifted.rename("feature"), target.rename("target")], axis=1
        ).dropna()

        if len(pair) < analysis_config["min_overlap"]:
            continue

        pair = sample_rows(pair, TE_SAMPLE_SIZE)

        try:
            feature_disc = discretize_series(pair["feature"], bins=analysis_config["te_bins"])
            target_disc = discretize_series(pair["target"], bins=analysis_config["te_bins"])
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


def build_model_matrix(df, target_name, screening, selected_features):
    if screening is None or screening.empty or not selected_features:
        return pd.DataFrame()

    lag_map = {
        row.feature: int(row.best_lag_steps)
        for row in screening.itertuples(index=False)
    }

    model_df = pd.DataFrame(index=df.index)
    for feature in selected_features:
        lag = lag_map.get(feature, 0)
        model_df[f"{feature} [lag={lag}x5min]"] = df[feature].shift(lag)

    model_df["target"] = df[target_name]
    model_df = model_df.dropna(subset=["target"])
    return sample_rows(model_df, MODEL_SAMPLE_SIZE)


def train_random_forest(model_df):
    if model_df.empty or model_df.shape[1] <= 1:
        return pd.DataFrame(), {}

    split = int(len(model_df) * 0.8)
    if split < 20 or split >= len(model_df):   # safer minimum size
        return pd.DataFrame(), {"error": "Dataset too small after split"}

    train = model_df.iloc[:split]
    test = model_df.iloc[split:]

    x_train = train.drop(columns=["target"])
    y_train = train["target"].values
    x_test = test.drop(columns=["target"])
    y_test = test["target"].values

    # === Imputation with proper feature tracking ===
    imputer = SimpleImputer(strategy="median")
    x_train_imp = imputer.fit_transform(x_train)
    x_test_imp = imputer.transform(x_test)

    # Determine which features were actually used (not all-NaN)
    statistics = imputer.statistics_
    if statistics.ndim == 1:
        # Most common case
        valid_mask = ~np.isnan(statistics)
    else:
        valid_mask = ~np.all(np.isnan(statistics), axis=0)

    kept_features = x_train.columns[valid_mask].tolist()

    if len(kept_features) == 0:
        return pd.DataFrame(), {"error": "All features dropped by imputer"}

    # If some features were dropped, warn once
    dropped_count = len(x_train.columns) - len(kept_features)
    if dropped_count > 0:
        print(f"  → Warning: {dropped_count} feature(s) were fully NaN and dropped by imputer "
              f"(e.g. very large lags with insufficient overlap).")

    # Train the model on the imputed data (which has only kept features)
    min_samples_leaf = max(2, min(8, len(train) // 20))
    model = RandomForestRegressor(
        n_estimators=250,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        min_samples_leaf=min_samples_leaf,
    )
    model.fit(x_train_imp, y_train)

    predictions = model.predict(x_test_imp)

    # Permutation importance
    perm = permutation_importance(
        model,
        x_test_imp,
        y_test,
        n_repeats=8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    importance = pd.DataFrame({
        "feature": kept_features,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)

    metrics = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_r2": float(r2_score(y_test, predictions)),
        "test_mae": float(mean_absolute_error(y_test, predictions)),
        "features_used": len(kept_features),
        "features_dropped": dropped_count,
    }

    return importance, metrics


def train_random_forest_batches(df, target_name, screening, mi_df, te_df, analysis_config):
    if screening is None or screening.empty:
        return pd.DataFrame(), {}

    summary_sin_rf = merge_influence_summary(
        screening,
        mi_df,
        te_df,
        pd.DataFrame(),
    )
    if summary_sin_rf.empty:
        return pd.DataFrame(), {}

    feature_order = summary_sin_rf["feature"].tolist()
    rf_frames = []
    batch_metrics = []
    first_error = None
    batch_size = analysis_config["rf_batch_features"]
    total_batches = 0

    for feature_batch in chunk_values(feature_order, batch_size):
        total_batches += 1
        model_df = build_model_matrix(df, target_name, screening, feature_batch)
        rf_batch, metrics = train_random_forest(model_df)

        if metrics.get("error") and first_error is None:
            first_error = metrics["error"]
        if rf_batch is None or rf_batch.empty:
            continue

        rf_frames.append(rf_batch)
        batch_metrics.append(metrics)

    if not rf_frames:
        return pd.DataFrame(), {
            "error": first_error or "Random Forest no pudo entrenarse con suficientes datos.",
            "batches_total": total_batches,
            "batches_trained": 0,
            "features_scored": 0,
        }

    rf_df = pd.concat(rf_frames, ignore_index=True)
    features_scored = (
        rf_df["feature"]
        .str.replace(r" \[lag=\d+x5min\]$", "", regex=True)
        .nunique()
    )

    metrics = {
        "batches_total": total_batches,
        "batches_trained": len(batch_metrics),
        "features_scored": int(features_scored),
        "train_rows_min": int(min(item["train_rows"] for item in batch_metrics)),
        "train_rows_max": int(max(item["train_rows"] for item in batch_metrics)),
        "test_rows_min": int(min(item["test_rows"] for item in batch_metrics)),
        "test_rows_max": int(max(item["test_rows"] for item in batch_metrics)),
        "test_r2_mean": float(np.mean([item["test_r2"] for item in batch_metrics])),
        "test_mae_mean": float(np.mean([item["test_mae"] for item in batch_metrics])),
        "features_used_mean": float(np.mean([item["features_used"] for item in batch_metrics])),
        "features_dropped_mean": float(np.mean([item["features_dropped"] for item in batch_metrics])),
    }
    return rf_df, metrics


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

    for column in ["mutual_information", "transfer_entropy", "importance_mean"]:
        if column not in summary.columns:
            summary[column] = np.nan

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
            "te": pd.DataFrame(),
            "rf": pd.DataFrame(),
            "metrics": {},
        }

    analysis_config = build_analysis_config(df)
    screening = compute_lag_screening(df, columna_objetivo, analysis_config)
    mi_df = compute_mutual_information(df, columna_objetivo, screening, analysis_config)
    te_df = compute_transfer_entropy(df, columna_objetivo, screening, analysis_config)
    rf_df, metrics = train_random_forest_batches(
        df,
        columna_objetivo,
        screening,
        mi_df,
        te_df,
        analysis_config,
    )
    if metrics:
        metrics["context_rows"] = analysis_config["context_rows"]
        metrics["min_overlap"] = analysis_config["min_overlap"]
        metrics["te_bins"] = analysis_config["te_bins"]
        metrics["rf_batch_features"] = analysis_config["rf_batch_features"]
    summary = merge_influence_summary(screening, mi_df, te_df, rf_df)

    return {
        "summary": summary,
        "screening": screening,
        "mi": mi_df,
        "te": te_df,
        "rf": rf_df,
        "metrics": metrics,
    }

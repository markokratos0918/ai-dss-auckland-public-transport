"""Model training for the AI-DSS modeling checkpoint."""

import warnings

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier, XGBRegressor

from ai_dss_modeling.config import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, RANDOM_STATE, TEST_DATE_SHARE
from ai_dss_modeling.metrics import add_metric, classification_metrics, regression_metrics

try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:  # pragma: no cover - optional runtime dependency
    ARIMA = None


def preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=20)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def feature_names(fitted_preprocessor: ColumnTransformer) -> list[str]:
    return list(fitted_preprocessor.get_feature_names_out())


def train_classification(train_df, test_df, rows: list[dict]):
    x_train = train_df[FEATURES]
    x_test = test_df[FEATURES]
    y_train = train_df["actionable_delay_risk"]
    y_test = test_df["actionable_delay_risk"]

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(x_train, y_train)
    classification_metrics(rows, "Most frequent baseline", y_test, baseline.predict(x_test))

    negative = int((y_train == 0).sum())
    positive = int((y_train == 1).sum())
    scale_pos_weight = negative / positive if positive else 1.0

    model = Pipeline(
        [
            ("preprocess", preprocessor()),
            (
                "model",
                XGBClassifier(
                    n_estimators=160,
                    max_depth=5,
                    learning_rate=0.08,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                    n_jobs=4,
                    scale_pos_weight=scale_pos_weight,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    classification_metrics(rows, "XGBoost classifier", y_test, predictions)
    add_metric(rows, "XGBoost classifier", "classification", "actionable_delay_risk", "scale_pos_weight", scale_pos_weight)
    return model, predictions, probabilities


def train_regression(train_df, test_df, rows: list[dict]):
    x_train = train_df[FEATURES]
    x_test = test_df[FEATURES]
    y_train = train_df["delay_minutes"]
    y_test = test_df["delay_minutes"]

    baseline = DummyRegressor(strategy="median")
    baseline.fit(x_train, y_train)
    regression_metrics(rows, "Median baseline", "delay_minutes", y_test, baseline.predict(x_test))

    model = Pipeline(
        [
            ("preprocess", preprocessor()),
            (
                "model",
                XGBRegressor(
                    n_estimators=180,
                    max_depth=5,
                    learning_rate=0.08,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    objective="reg:squarederror",
                    random_state=RANDOM_STATE,
                    n_jobs=4,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    regression_metrics(rows, "XGBoost regressor", "delay_minutes", y_test, predictions)
    return model, predictions


def arima_baseline(df, rows: list[dict]) -> str:
    target = "hourly_avg_delay_minutes"
    if ARIMA is None:
        add_metric(rows, "ARIMA baseline", "regression", target, "status", "not_run", "statsmodels ARIMA unavailable")
        return "ARIMA was not run because statsmodels ARIMA was unavailable."

    hourly = (
        df.set_index("collection_time_utc")
        .sort_index()["delay_minutes"]
        .resample("h")
        .mean()
        .interpolate(limit_direction="both")
        .dropna()
    )
    if len(hourly) < 30:
        add_metric(rows, "ARIMA baseline", "regression", target, "status", "not_run", "too few hourly points")
        return "ARIMA was not run because fewer than 30 hourly aggregate points were available."

    split_index = max(1, int(len(hourly) * (1 - TEST_DATE_SHARE)))
    train = hourly.iloc[:split_index]
    test = hourly.iloc[split_index:]
    if test.empty:
        add_metric(rows, "ARIMA baseline", "regression", target, "status", "not_run", "empty test period")
        return "ARIMA was not run because the hourly test period was empty."

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = ARIMA(train, order=(1, 0, 1)).fit()
            forecast = fitted.forecast(steps=len(test))
        regression_metrics(
            rows,
            "ARIMA(1,0,1) baseline",
            target,
            test,
            forecast,
            "Hourly average delay baseline, not row-level prediction",
        )
        add_metric(rows, "ARIMA(1,0,1) baseline", "regression", target, "train_hours", len(train))
        add_metric(rows, "ARIMA(1,0,1) baseline", "regression", target, "test_hours", len(test))
        return f"ARIMA used {len(train):,} training hours and {len(test):,} test hours on hourly average delay."
    except Exception as error:
        add_metric(rows, "ARIMA baseline", "regression", target, "status", "not_run", str(error))
        return f"ARIMA was attempted but did not complete: {error}"


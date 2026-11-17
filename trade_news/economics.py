"""Release-aware, retrospective export forecast comparison; no invented trade data.

This adapts the idea of a forecast horse race, not BE1340's dynamic factor model.
The pretrained news classifier still requires an independent human evaluation.
"""
import math
import warnings

import pandas as pd


def load_trade(path):
    frame = pd.read_csv(path, dtype=str).fillna("")
    required = {"month", "fob_usd"}
    if not required <= set(frame):
        raise ValueError("Trade CSV requires month and fob_usd; provide explicit national monthly goods-export totals")
    if "destination" in frame:
        frame = frame[frame["destination"] == "World"].copy()
        if frame.empty:
            raise ValueError("Provide explicit World totals; country rows will not be silently summed")
    if frame.empty or frame["month"].duplicated().any():
        raise ValueError("One national total per month is required; empty or duplicate months found")
    if not frame["month"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise ValueError("Use explicit YYYY-MM reference months")
    frame["fob_usd"] = pd.to_numeric(frame["fob_usd"], errors="raise")
    if any(not math.isfinite(x) or x <= 0 for x in frame["fob_usd"]):
        raise ValueError("National FOB must be finite, strictly positive USD values")
    url_valid = frame.get("source_url", pd.Series("", index=frame.index)).str.match(r"https?://")
    workbook_valid = frame.get("source_ref", pd.Series("", index=frame.index)).str.match(r"workbook-sha256:[0-9a-f]{64}#.+![A-Z]+[0-9]+:[A-Z]+[0-9]+$")
    if not (url_valid | workbook_valid).all():
        raise ValueError("Each numerical observation requires a source URL or SHA-256 workbook/cell reference")
    frame.index = pd.PeriodIndex(frame["month"], freq="M")
    for column in ("release_date", "vintage_date"):
        if column not in frame:
            frame[column] = pd.NaT
        else:
            frame[column] = pd.to_datetime(frame[column].replace("", None), format="%Y-%m-%d", errors="raise")
    for period, row in frame.iterrows():
        if pd.notna(row["release_date"]) and row["release_date"].date() < period.end_time.date():
            raise ValueError("A complete monthly total cannot be released before its reference month ends")
        if pd.notna(row["vintage_date"]) and (pd.isna(row["release_date"]) or row["vintage_date"] < row["release_date"]):
            raise ValueError("Vintage dates require a release date and cannot precede it")
    frame = frame.sort_index().reindex(pd.period_range(frame.index.min(), frame.index.max(), freq="M"))
    frame.index.name = "reference_month"
    return frame


def audit_trade(frame):
    observed = frame["fob_usd"].notna()
    return {"observed_months": int(observed.sum()), "first_month": str(frame.index.min()), "last_month": str(frame.index.max()),
        "missing_calendar_months": [str(period) for period in frame.index[~observed]],
        "release_dates_missing": int(frame.loc[observed, "release_date"].isna().sum()),
        "vintage_dates_missing": int(frame.loc[observed, "vintage_date"].isna().sum()),
        "measure": "Nominal national goods exports, FOB USD; not real export volume",
        "note": "No missing values are filled; statistical reference months and release dates remain separate."}


def growth_asof(frame, origin, allow_revised_history=False):
    """Annual log change; mask unavailable values BEFORE deriving growth."""
    origin = pd.Timestamp(origin)
    values = frame["fob_usd"].copy()
    available = frame["release_date"].notna() & (frame["release_date"] <= origin)
    if not allow_revised_history:
        available &= frame["vintage_date"].notna() & (frame["vintage_date"] <= origin)
    values[~available] = float("nan")
    logs = values.map(lambda x: math.log(x) if pd.notna(x) and x > 0 else float("nan"))
    return 100*(logs-logs.shift(12))


def final_growth(frame):
    logs = frame["fob_usd"].map(lambda x: math.log(x) if pd.notna(x) and x > 0 else float("nan"))
    return 100*(logs-logs.shift(12))


def assumed_availability(frame, lag_months):
    """Explicit sensitivity scenario, never a recovered historical release calendar."""
    if lag_months not in {1, 2, 3}:
        raise ValueError("Prespecified assumed release lags are 1, 2 or 3 calendar months")
    result = frame.copy()
    # Original CSV release/vintage columns remain blank and unchanged on disk.
    result["release_date"] = [(p+lag_months).end_time.normalize() for p in result.index]
    return result


def news_features(rows, scores, months, exclude_reporting=False, fixed_domains=None):
    from .bank_method import aggregate
    from .contextual import aggregate_scores
    from .coverage import in_primary_press_frame
    selected = [r for r in rows if r.get("eligible_for_index") and in_primary_press_frame(r)
                and (not fixed_domains or r["publisher_group"] in fixed_domains)
                and (not exclude_reporting or r.get("document_role_proposal") not in {"statistical_reporting_candidate", "mixed_cues"})]
    lexical = {r["month"]: r for r in aggregate(selected, months) if r["activity"] == "All exports"}
    contextual = aggregate_scores(scores, selected, months)
    records = []
    for r in contextual:
        monthly = [row for row in selected if row["month"] == r["month"]]
        count = len(monthly)
        records.append({"month": r["month"], "tone": r["mean_probability_balance"],
            "uncertainty": lexical[r["month"]]["uncertainty_per_1000"], "articles": r["articles"], "sources": r["publishers"],
            "log_articles": math.log1p(count),
            "source_share": sum(row["publisher_group"] == "valoraanalitik.com" for row in monthly)/count if count else None})
    frame = pd.DataFrame(records)
    frame.index = pd.PeriodIndex(frame.pop("month"), freq="M")
    return frame


def make_fold(trade, news, target, minimum_training=36, allow_revised_history=False):
    target = pd.Period(target, freq="M")
    # Predict month t at the end of t-1. Never use news from target month t.
    origin = (target-1).end_time.normalize()
    history = growth_asof(trade, origin, allow_revised_history).loc[:target-1]
    columns = [c for c in ["log_articles", "source_share", "tone", "uncertainty"] if c in news]
    features = news[columns].reindex(pd.period_range(news.index.min(), target, freq="M")).shift(1)
    features = features.loc[:target]
    # Retain a complete trailing feature window; never connect a missing news month.
    complete = features.notna().all(axis=1)
    if not complete.get(target, False):
        return {"status": "skipped", "reason": "No complete lagged news features at forecast origin", "target": str(target)}
    first = target
    while first-1 in complete.index and bool(complete.loc[first-1]):
        first -= 1
    training_index = pd.period_range(first, target-1, freq="M")
    y = history.reindex(training_index)
    if int(y.notna().sum()) < minimum_training:
        return {"status": "skipped", "reason": "Insufficient released annual-growth observations in a complete news window", "target": str(target)}
    x = features.reindex(training_index)
    means, scales = x.mean(), x.std(ddof=0)
    if any(not math.isfinite(v) for v in scales):
        return {"status": "skipped", "reason": "A news regressor has invalid training variance", "target": str(target)}
    constant_columns = list(scales[scales == 0].index)
    x = x.drop(columns=constant_columns)
    means, scales = means.drop(index=constant_columns), scales.drop(index=constant_columns)
    return {"status": "ready", "target": str(target), "origin": str(origin.date()), "y": y,
            "x": (x-means)/scales, "future_x": (features.loc[[target], x.columns]-means)/scales,
            "training_means": means.to_dict(), "training_scales": scales.to_dict(),
            "training_observations": int(y.notna().sum()), "first_training_month": str(first)}


def error_metrics(actual, predicted):
    if not actual:
        return {"n": 0, "mae": None, "rmse": None, "mean_error": None}
    errors = [prediction-observed for observed, prediction in zip(actual, predicted)]
    return {"n": len(errors), "mae": math.fsum(abs(e) for e in errors)/len(errors),
            "rmse": math.sqrt(math.fsum(e*e for e in errors)/len(errors)), "mean_error": math.fsum(errors)/len(errors)}


def compare(trade, news, test_months=12, minimum_training=36, allow_revised_history=False, assumed_release_lag=None):
    """Fixed ARMA(1,1) vs ARMAX(1,1), common origins, expanding estimation.

    No full-sample model-order search, feature normalization or future-data fit.
    Performance is retrospective: web availability and data vintages limit claims.
    """
    if test_months < 12 or minimum_training < 36:
        raise ValueError("The prespecified comparison requires at least 12 test origins and 36 training observations")
    audit = audit_trade(trade)
    if assumed_release_lag is not None:
        if not allow_revised_history:
            raise ValueError("Assumed publication timing requires explicit revised-history permission")
        trade = assumed_availability(trade, assumed_release_lag)
    if (audit["release_dates_missing"] and assumed_release_lag is None) or (audit["vintage_dates_missing"] and not allow_revised_history):
        return {"status": "blocked_missing_release_or_vintage_dates", "trade_audit": audit, "forecasts": [], "metrics": None,
                "note": "Supply release/vintage dates. An explicit revised-history option permits only a retrospective sensitivity analysis, never a real-time claim."}
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    actual = final_growth(trade)
    last = min(trade.index.max(), news.index.max()+1)
    targets = pd.period_range(last-test_months+1, last, freq="M")
    predictions, skipped = [], []
    for target in targets:
        fold = make_fold(trade, news, target, minimum_training, allow_revised_history)
        truth = actual.get(target)
        if fold["status"] != "ready" or pd.isna(truth):
            skipped.append({"target": str(target), "reason": fold.get("reason", "Target unavailable")})
            continue
        current = {key: fold[key] for key in ["target", "origin", "training_observations", "first_training_month", "training_means", "training_scales"]}
        current.update(actual=float(truth), models={})
        succeeded = True
        controls = [c for c in ["log_articles", "source_share"] if c in fold["x"]]
        specifications = [("baseline_arma", []), ("baseline_coverage", controls),
            ("plus_tone", controls+["tone"]), ("plus_tone_uncertainty", controls+["tone", "uncertainty"])]
        for model_name, columns in specifications:
            columns = [c for c in columns if c in fold["x"]]
            try:
                with warnings.catch_warnings(record=True) as notices:
                    fit = SARIMAX(fold["y"], exog=fold["x"][columns] if columns else None,
                        order=(1, 0, 1), trend="c", enforce_stationarity=True, enforce_invertibility=True).fit(disp=False, maxiter=250)
                if not fit.mle_retvals.get("converged"):
                    raise ValueError("Optimizer did not converge")
                estimate = fit.get_forecast(steps=1, exog=fold["future_x"][columns] if columns else None)
                bounds = estimate.conf_int(alpha=.05).iloc[0].tolist()
                residual = fit.resid[fold["y"].notna()].iloc[3:]
                lag = min(12, max(3, len(residual)//5))
                lb = acorr_ljungbox(residual, lags=[lag], model_df=2, return_df=True)
                current["models"][model_name] = {"prediction": float(estimate.predicted_mean.iloc[0]),
                    "interval_95": [float(x) for x in bounds], "aic": float(fit.aic), "bic": float(fit.bic),
                    "ljung_box_lag": lag, "ljung_box_pvalue": float(lb["lb_pvalue"].iloc[0]),
                    "warnings": list(dict.fromkeys(str(w.message) for w in notices))}
            except Exception as error:
                skipped.append({"target": str(target), "model": model_name, "reason": str(error)})
                succeeded = False
                break
        if succeeded:
            current["models"]["growth_persistence"] = {"prediction": float(fold["y"].dropna().iloc[-1]),
                "definition": "Latest annual log-growth observation available at this origin; diagnostic comparator, no fit"}
            current["models"]["seasonal_naive_fob"] = {"prediction": 0.0,
                "definition": "Same nominal FOB as twelve months earlier implies zero annual log growth; diagnostic comparator, no fit"}
            current["training_adf_pvalue"] = float(adfuller(fold["y"].dropna(), maxlag=3, regression="c", autolag="AIC", result_object=False)[1])
            predictions.append(current)
    metrics = {name: error_metrics([r["actual"] for r in predictions], [r["models"][name]["prediction"] for r in predictions])
               for name in ["baseline_arma", "baseline_coverage", "plus_tone", "plus_tone_uncertainty", "growth_persistence", "seasonal_naive_fob"]}
    diagnostics = {name: {"residual_autocorrelation_rejections_at_005": sum(r["models"][name]["ljung_box_pvalue"] < .05 for r in predictions),
                         "evaluated_fits": len(predictions)} for name in ["baseline_arma", "baseline_coverage", "plus_tone", "plus_tone_uncertainty"]}
    return {"status": "retrospective_comparison" if len(predictions) >= 12 else "insufficient_common_successful_origins",
        "measure": "100 * annual log change in nominal national FOB USD; errors in log percentage points",
        "design": "Fixed ARMA(1,1); coverage-controlled ARMAX (log article count and source share); plus lagged tone; plus lagged tone and uncertainty. All news lagged one calendar month; expanding windows; training-only scaling; common successful origins.",
        "assumed_release_lag_months": assumed_release_lag,
        "availability_status": "Assumed end-of-month release timing; current revised history; NOT verified real-time availability" if assumed_release_lag else "Supplied release dates; inspect vintage limitations",
        "revised_history_allowed": allow_revised_history, "trade_audit": audit, "forecasts": predictions, "skipped": skipped, "metrics": metrics,
        "diagnostic_assessment": {"by_model": diagnostics,
            "training_adf_nonrejections_at_005": sum(r["training_adf_pvalue"] >= .05 for r in predictions),
            "interpretation": "Forecasting validity is not established; retain diagnostics and do not treat a small error reduction as validation."},
        "note": "No exact BE1340 dynamic-factor replication, no guaranteed improvement, no causal or real-time claim. Inspect failed folds, stationarity, residuals, sample size and source/reporting sensitivity before interpreting errors."}


def lead_lag(trade, news):
    """Descriptive associations at fixed lags; no optimal-lag or causal claim."""
    growth = final_growth(trade)
    results = []
    for offset in range(-3, 4):
        aligned = pd.Series({period: growth.get(period+offset) for period in news.index}, dtype=float)
        pairs = pd.DataFrame({"tone": news["tone"], "growth": aligned}).dropna()
        value = pairs["tone"].corr(pairs["growth"]) if len(pairs) > 2 else None
        results.append({"export_month_minus_news_month": offset, "n": len(pairs),
                        "pearson_correlation": float(value) if value is not None and math.isfinite(value) else None})
    return {"measure": "corr(tone at t, annual nominal FOB log growth at t+h)", "pairs": results,
            "note": "Negative h refers to earlier export reference periods, positive h to later periods. Descriptive, dependent monthly observations; no causal evidence or selected best lag."}

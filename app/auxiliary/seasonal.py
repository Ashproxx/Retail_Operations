"""Supplemental validation-only anomaly comparison; final-test evidence is untouched."""
from datetime import timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, roc_auc_score
from statsmodels.tsa.seasonal import STL


def compare(dates, values):
    dates, values = list(dates), np.asarray(values, dtype=float)
    if values.ndim != 1 or len(dates) != len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Matching dates and finite nonnegative counts required')
    if not dates or any(b-a != timedelta(days=1) for a,b in zip(dates, dates[1:])):
        raise ValueError('Contiguous daily observations required; never fill gaps with zeros')
    if dates[-1].isoformat() != '2026-05-26':
        raise ValueError('Supplement ends May 26; final-test rows are forbidden')
    train = values[[d.isoformat() <= '2026-03-31' for d in dates]]
    validation = values[[d.isoformat() >= '2026-04-01' for d in dates]]
    if len(train) < 56 or len(validation) != 56 or np.std(train) == 0:
        raise ValueError('At least 56 variable training days and exactly 56 validation days required')
    stl = STL(train, period=7, seasonal=7, robust=True).fit()
    # Fixed extrapolation: repeat the final weekly component with a flat final trend.
    expected = stl.trend[-1] + np.resize(stl.seasonal[-7:], len(validation))
    expected = np.maximum(expected, 0)
    forest = IsolationForest(n_estimators=100, contamination=.05, random_state=42).fit(train[:,None])
    center = np.median(train)
    contaminated = validation.copy()
    indices = np.random.default_rng(42).choice(len(validation), 5, replace=False)
    shifts = np.array([1,-1,1,-1,1])*4*np.std(train)
    contaminated[indices] = np.maximum(contaminated[indices]+shifts, 0)
    labels = np.zeros(len(validation), dtype=int)
    labels[indices] = 1
    scores = {
        'stl_weekly': (np.abs(stl.resid), np.abs(validation-expected), np.abs(contaminated-expected)),
        'isolation_forest': (-forest.score_samples(train[:,None]), -forest.score_samples(validation[:,None]),
                             -forest.score_samples(contaminated[:,None])),
        'median_absolute_deviation': (np.abs(train-center), np.abs(validation-center), np.abs(contaminated-center)),
    }
    results = {}
    for name,(reference,clean,score) in scores.items():
        threshold = float(np.quantile(reference,.95))
        prediction = score > threshold
        results[name] = {'roc_auc': float(roc_auc_score(labels,score)),
            'average_precision': float(average_precision_score(labels,score)),
            'f1': float(f1_score(labels,prediction,zero_division=0)),
            'confusion_labels_0_1': confusion_matrix(labels,prediction,labels=[0,1]).tolist(),
            'threshold': threshold, 'clean_validation_alert_rate': float(np.mean(clean>threshold))}
    return {'status':'MEASURED_VALIDATION_INJECTED_PROXY', 'train_days':len(train),
        'validation_days':len(validation), 'injected_days':len(indices),
        'injected_dates':[dates[len(train)+int(i)].isoformat() for i in indices],
        'results':results, 'limitations':[
            'Supplemental development validation, not a new independent final test or natural anomaly accuracy.',
            'Thresholds use in-sample training scores, so optimistic calibration is possible.',
            'Five large mixed-sign injected changes are an easy proxy; natural anomalies remain unlabelled.',
            'Clean alert rate is not a false-positive rate without reviewed natural anomaly labels.',
            'STL is fitted only on training history; its trend is held flat and final weekly component repeated.',
            'No model selection, promotion, or change to the existing frozen final-test report.']}

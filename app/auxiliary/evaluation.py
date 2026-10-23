"""Fixed auxiliary experiments on local synthetic data, with explicit exclusions."""
from collections import Counter, defaultdict
from datetime import date, timedelta
import math

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, roc_auc_score, silhouette_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans


def day(value):
    return date.fromisoformat(str(value)[:10])


def delivery_orders(rows):
    """One resolved order per store/id; inconsistent line-level labels are rejected."""
    grouped = defaultdict(list)
    for row in rows:
        if row['fulfillment_type'] == 'Home Delivery':
            grouped[row['store_id'], row['order_id']].append(row)
    orders, excluded = [], Counter()
    same = ('sale_date', 'delivery_status', 'promised_delivery_date',
            'actual_delivery_date', 'sales_channel', 'delivery_partner')
    for lines in grouped.values():
        first = lines[0]
        if any(any(row[k] != first[k] for k in same) for row in lines):
            excluded['inconsistent_order_lines'] += 1
            continue
        if first['delivery_status'] != 'Delivered' or not first['actual_delivery_date']:
            excluded['unresolved_or_missing_actual'] += 1
            continue
        try:
            sold, promised, actual = map(day, (first['sale_date'],
                first['promised_delivery_date'], first['actual_delivery_date']))
            if min(promised, actual) < sold:
                raise ValueError('invalid chronology')
            units = sum(float(r['quantity']) for r in lines)
            if not math.isfinite(units) or units <= 0:
                raise ValueError('invalid quantity')
        except (ValueError, TypeError):
            excluded['invalid_dates_or_quantity'] += 1
            continue
        orders.append({'sold': sold, 'resolved': actual,
            'label': int(actual > promised),
            'x': [first['store_id'], first['sales_channel'], first['delivery_partner'],
                  str(sold.weekday()), (promised-sold).days, units]})
    return orders, dict(excluded)


def classification_metrics(labels, probabilities):
    y, p = np.asarray(labels), np.asarray(probabilities)
    if not len(y) or len(y) != len(p) or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Finite probabilities and nonempty matching labels required')
    if not set(y.tolist()) <= {0, 1}:
        raise ValueError('Binary labels required')
    bins = []
    bin_ids = np.minimum((p*10).astype(int), 9)
    for index in range(10):
        mask = bin_ids == index
        if mask.any():
            bins.append({'count': int(mask.sum()), 'mean_probability': float(p[mask].mean()),
                         'observed_rate': float(y[mask].mean())})
    two_classes = len(set(y.tolist())) == 2
    return {'n': len(y), 'positive_rate': float(y.mean()),
        'roc_auc': float(roc_auc_score(y, p)) if two_classes else None,
        'pr_auc_average_precision': float(average_precision_score(y, p)) if two_classes else None,
        'brier': float(brier_score_loss(y, p)),
        'f1_at_fixed_half': float(f1_score(y, p >= .5, zero_division=0)),
        'confusion_labels_0_1': confusion_matrix(y, p >= .5, labels=[0, 1]).tolist(),
        'calibration_bins': bins,
        'ece_10_bins': sum(b['count']*abs(b['mean_probability']-b['observed_rate']) for b in bins)/len(y)}


def delivery_evaluation(rows):
    orders, excluded = delivery_orders(rows)
    train_end, validation_end, test_end = map(day, ('2026-03-31', '2026-08-04', '2026-09-29'))
    train = [r for r in orders if r['sold'] <= train_end and r['resolved'] <= train_end]
    validation = [r for r in orders if train_end < r['sold'] <= validation_end and r['resolved'] <= validation_end]
    test = [r for r in orders if validation_end < r['sold'] <= test_end and r['resolved'] <= test_end]
    excluded['label_unavailable_at_partition_end'] = len(orders)-len(train)-len(validation)-len(test)
    if not train or not validation or not test or len({r['label'] for r in train}) < 2:
        return {'status': 'UNVERIFIED', 'reason': 'insufficient resolved classes/partitions', 'excluded': excluded}
    x, y = [r['x'] for r in train], [r['label'] for r in train]
    def preparation():
        return ColumnTransformer([('categorical', OneHotEncoder(handle_unknown='ignore', sparse_output=False), [0,1,2,3]),
                                  ('numeric', StandardScaler(), [4,5])])
    models = {'logistic': make_pipeline(preparation(), LogisticRegression(C=1, max_iter=1000, random_state=42)),
              'forest': make_pipeline(preparation(), RandomForestClassifier(n_estimators=100, min_samples_leaf=20,
                                                        max_depth=8, random_state=42, n_jobs=1))}
    for model in models.values():
        model.fit(x, y)
    results = {}
    for name, subset in [('validation', validation), ('test', test)]:
        labels = [r['label'] for r in subset]
        results[name] = {'prevalence_baseline': classification_metrics(labels, [np.mean(y)]*len(subset))}
        for model_name, model in models.items():
            results[name][model_name] = classification_metrics(labels, model.predict_proba([r['x'] for r in subset])[:,1])
    return {'status': 'MEASURED_SYNTHETIC', 'train_orders': len(train), 'excluded': excluded,
        'features': ['store', 'channel', 'partner', 'weekday', 'promised_lead_days', 'order_units'],
        'fixed_threshold': .5, 'results': results,
        'limitations': ['Resolved delivered orders only; cancellation/failure risk is not measured.',
            'Snapshot order fields are assumed known at checkout; no revision history validates that assumption.',
            'No validation tuning, refitting or automatic deployment; training ends March 31.']}


def product_segments(rows):
    """Descriptive clusters fit on pre-April records only, never employee data."""
    grouped = defaultdict(list)
    for row in rows:
        if day(row['sale_date']) <= day('2026-03-31'):
            grouped[row['sku_id']].append(row)
    ids, features = [], []
    for sku, values in sorted(grouped.items()):
        days = len({r['sale_date'][:10] for r in values})
        if days < 14:
            continue
        units = sum(float(r['quantity']) for r in values)
        revenue = sum(float(r['net_amount_inr']) for r in values)
        ids.append(sku)
        features.append([math.log1p(units), math.log1p(revenue/units), days,
                         len({r['store_id'] for r in values})])
    if len(ids) < 6:
        return {'status': 'UNVERIFIED', 'reason': 'fewer than six eligible products'}
    x = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(x)
    count = len(set(labels))
    return {'status': 'MEASURED_DESCRIPTIVE', 'eligible_products': len(ids), 'excluded_products': len(grouped)-len(ids),
        'features': ['log_observed_units', 'log_realized_unit_price', 'observed_sale_dates', 'observed_store_count'],
        'silhouette': float(silhouette_score(x, labels)) if 1 < count < len(ids) else None,
        'cluster_sizes': dict(Counter(str(n) for n in labels)),
        'limitations': ['In-sample silhouette is descriptive, not held-out predictive accuracy.',
            'Observed sales and exposure differ; missing dates are not zero sales.',
            'No relevance labels exist for similarity ranking agreement.']}


def anomaly_evaluation(rows):
    """Train on clean history; inject labelled spikes only in a held-out copy."""
    totals = defaultdict(float)
    for r in rows:
        totals[day(r['sale_date'])] += float(r['quantity'])
    dates = sorted(totals)
    if not dates or any(b-a != timedelta(days=1) for a,b in zip(dates, dates[1:])):
        return {'status': 'UNVERIFIED', 'reason': 'daily coverage is incomplete'}
    train = np.array([totals[d] for d in dates if d <= day('2026-03-31')])
    test = np.array([totals[d] for d in dates if day('2026-08-05') <= d <= day('2026-09-29')])
    if len(train) < 56 or len(test) < 28:
        return {'status': 'UNVERIFIED', 'reason': 'insufficient history'}
    rng = np.random.default_rng(42)
    indices = rng.choice(len(test), size=max(1, len(test)//10), replace=False)
    injected = test.copy()
    injected[indices] += 4*np.std(train)
    labels = np.zeros(len(test), dtype=int)
    labels[indices] = 1
    model = IsolationForest(n_estimators=100, contamination=.05, random_state=42).fit(train[:,None])
    center, scale = np.median(train), np.median(np.abs(train-np.median(train)))
    if scale == 0:
        return {'status': 'UNVERIFIED', 'reason': 'zero training MAD'}
    scores = {'isolation_forest': (-model.score_samples(injected[:,None]), -model.score_samples(train[:,None]),
                                   -model.score_samples(test[:,None])),
              'median_absolute_deviation': (np.abs(injected-center)/scale, np.abs(train-center)/scale,
                                            np.abs(test-center)/scale)}
    results = {}
    for name, (score, reference, clean) in scores.items():
        threshold = float(np.quantile(reference, .95))
        pred = score > threshold
        results[name] = {'roc_auc': float(roc_auc_score(labels, score)),
            'average_precision': float(average_precision_score(labels, score)),
            'f1_at_train_95_percentile': float(f1_score(labels, pred, zero_division=0)),
            'confusion_labels_0_1': confusion_matrix(labels, pred, labels=[0,1]).tolist(),
            'clean_holdout_alert_rate': float(np.mean(clean > threshold)), 'threshold': threshold}
    return {'status': 'MEASURED_INJECTED_PROXY', 'test_days': len(test), 'injected_days': len(indices),
        'results': results, 'limitations': ['Only seeded upward spikes are labelled; natural anomalies are unknown.',
            'Clean alert rate is not a false-positive rate without reviewed anomaly labels.',
            'This univariate comparison does not evaluate seasonal STL or multivariate anomaly detection.']}

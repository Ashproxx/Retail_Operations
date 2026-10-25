"""Compare geometric product rankings; agreement is not relevance accuracy."""
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics.pairwise import cosine_distances, euclidean_distances
from sklearn.preprocessing import StandardScaler


def compare_rankings(rows):
    """Input: SKU, units, revenue INR, observed dates, observed stores (training only)."""
    rows = sorted(rows)
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids) or any(not sku for sku in ids):
        raise ValueError('Unique nonempty SKU identifiers required')
    values = np.asarray([r[1:] for r in rows], dtype=float)
    if values.shape != (len(rows), 4) or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Four positive finite observed aggregates required per SKU')
    eligible = values[:, 2] >= 14
    values = values[eligible]
    ids = [sku for sku, keep in zip(ids, eligible) if keep]
    if len(ids) < 7:
        return {'status': 'UNVERIFIED', 'reason': 'At least seven eligible products required'}
    features = np.column_stack((np.log1p(values[:, 0]),
        np.log1p(values[:, 1] / values[:, 0]), values[:, 2:]))
    x = StandardScaler().fit_transform(features)
    # shortcut: zero centered vectors have no cosine direction; omit until richer features exist.
    directional = np.linalg.norm(x, axis=1) > 1e-12
    x = x[directional]
    ids = [sku for sku, keep in zip(ids, directional) if keep]
    if len(ids) < 7:
        return {'status': 'UNVERIFIED', 'reason': 'Insufficient nonzero standardized feature vectors'}
    distances = {'euclidean': euclidean_distances(x), 'cosine': cosine_distances(x)}
    review, correlations, overlaps = [], [], []
    for i, sku in enumerate(ids):
        rankings = {name: sorted((j for j in range(len(ids)) if j != i),
                    key=lambda j: (float(matrix[i, j]), ids[j]))
                    for name, matrix in distances.items()}
        first, second = rankings['euclidean'], rankings['cosine']
        candidates = sorted(set(first[:5]) | set(second[:5]), key=lambda j: ids[j])
        overlaps.append(len(set(first[:5]) & set(second[:5])) / 5)
        others = [j for j in range(len(ids)) if j != i]
        correlations.append(float(spearmanr([first.index(j) for j in others],
                                           [second.index(j) for j in others]).statistic))
        for j in candidates:
            review.append({'query_sku': sku, 'candidate_sku': ids[j],
                'euclidean_rank': first.index(j) + 1, 'cosine_rank': second.index(j) + 1,
                'reviewer': None, 'relevant': None})
    return {'status': 'MEASURED_METHOD_AGREEMENT', 'eligible_products': len(ids),
        'excluded_short_history': int((~eligible).sum()),
        'excluded_zero_direction': int((~directional).sum()),
        'mean_top5_overlap_fraction': float(np.mean(overlaps)),
        'mean_full_ranking_spearman': float(np.mean(correlations)),
        'features': ['log_observed_units', 'log_realized_unit_price', 'observed_sale_dates', 'observed_store_count'],
        'relevance_status': 'UNVERIFIED_NO_HUMAN_LABELS', 'review_queue': review}


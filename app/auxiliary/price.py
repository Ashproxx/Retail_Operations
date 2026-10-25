"""Descriptive price/sales association; never a causal elasticity estimator."""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def price_association(rows):
    """Rows are (ISO day, SKU, observed units, net revenue INR), one per SKU/day."""
    frame = pd.DataFrame(rows, columns=['day', 'sku', 'units', 'revenue'])
    if frame.empty:
        raise ValueError('Observed SKU/day rows required')
    frame['day'] = pd.to_datetime(frame['day'], errors='raise')
    if (frame.day > pd.Timestamp('2026-03-31')).any():
        raise ValueError('Training-only supplement ends March 31')
    if frame[['day', 'sku']].duplicated().any() or frame[['day', 'sku']].isna().any().any():
        raise ValueError('Unique SKU/day rows with SKU identifiers required')
    values = frame[['units', 'revenue']].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Positive finite observed units and revenue required')
    frame['log_units'] = np.log(values[:, 0])
    frame['log_price'] = np.log(values[:, 1] / values[:, 0])
    counts = frame.groupby('sku').size()
    eligible = counts[counts >= 28].index
    excluded = len(counts) - len(eligible)
    frame = frame[frame.sku.isin(eligible)].copy()
    if frame.empty:
        return {'status': 'UNVERIFIED', 'reason': 'No product has 28 observed dates'}
    frame['weekday'] = frame.day.dt.day_of_week
    frame['trend'] = (frame.day - frame.day.min()).dt.days
    frame['week'] = frame.day.map(lambda d: (d.date().toordinal() - 1) // 7)
    weeks = frame.week.nunique()
    if weeks < 12:
        return {'status': 'UNVERIFIED', 'reason': 'Fewer than twelve observed week clusters'}
    model = smf.ols('log_units ~ log_price + C(sku) + C(weekday) + trend', data=frame)
    if np.linalg.matrix_rank(model.exog) < model.exog.shape[1]:
        return {'status': 'UNVERIFIED', 'reason': 'Price association is not identified by this design'}
    fit = model.fit(cov_type='cluster', cov_kwds={'groups': frame.week,
                    'use_correction': True, 'df_correction': True}, use_t=True)
    interval = fit.conf_int(alpha=.05).loc['log_price'].tolist()
    return {'status': 'MEASURED_DESCRIPTIVE_ASSOCIATION',
        'observed_product_days': len(frame), 'products': frame.sku.nunique(),
        'excluded_short_history_products': excluded, 'week_clusters': weeks,
        'first_day': frame.day.min().date().isoformat(),
        'last_day': frame.day.max().date().isoformat(),
        'log_price_coefficient': float(fit.params['log_price']),
        'cluster_week_standard_error': float(fit.bse['log_price']),
        'cluster_week_t_interval_95': interval,
        'interval_degrees_of_freedom': weeks - 1,
        'controls': ['SKU fixed effects', 'weekday fixed effects', 'linear calendar trend'],
        'limitations': [
            'Synthetic training data only; no held-out prediction or real-world accuracy claim.',
            'Realized price is revenue divided by sold units; quantity weighting and mathematical coupling can distort association.',
            'Only positive observed sales days enter; missing days are unknown, never zero-filled.',
            'Stock availability, promotions, changing store exposure and customer selection are unobserved confounders.',
            'Week-cluster intervals allow within-week dependence; across-week dependence and few clusters can invalidate coverage.',
            'This coefficient is not causal demand elasticity and must not drive price recommendations.']}

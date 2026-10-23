"""Calendar-aligned, cutoff-bounded features and authorized source extraction."""
from datetime import date, timedelta
from math import isfinite
from statistics import mean, pstdev
from sqlalchemy import select, func
from app.enterprise.data import Sale
from app.enterprise.retail import filters


def validate_series(days: list[date], values: list[float], *, contiguous: bool = False) -> None:
    if not days or len(days) != len(values) or days != sorted(set(days)):
        raise ValueError('Require nonempty, ordered, unique dates and aligned values')
    if any(not isfinite(v) or v < 0 for v in values):
        raise ValueError('Observed units must be finite and nonnegative')
    if contiguous and any(b-a != timedelta(days=1) for a,b in zip(days,days[1:])):
        raise ValueError('Missing days are unknown, not zero sales')


def at_origin(days: list[date], values: list[float], cutoff: date, target: date) -> dict:
    validate_series(days, values)
    if target <= cutoff:
        raise ValueError('Target must follow cutoff')
    known = {d:v for d,v in zip(days,values) if d <= cutoff}
    result = {'lead':(target-cutoff).days, 'weekday':target.weekday(), 'month':target.month,
              'weekend':int(target.weekday() >= 5)}
    for lag in (1,7,14,28):
        result[f'lag_{lag}'] = known.get(target-timedelta(days=lag))
    for window in (7,14,28):
        observed = [known[cutoff-timedelta(days=i)] for i in range(window) if cutoff-timedelta(days=i) in known]
        result[f'count_{window}'] = len(observed)
        result[f'mean_{window}'] = mean(observed) if len(observed)==window else None
        result[f'std_{window}'] = pstdev(observed) if len(observed)==window else None
    return result


def daily_series(database, ctx, cutoff: date, level: str = 'chain') -> dict:
    dimensions = {'chain':[], 'store':[Sale.store_id], 'store_category':[Sale.store_id,Sale.category],
                  'store_sku':[Sale.store_id,Sale.sku_id]}
    if level not in dimensions:
        raise ValueError('Unknown aggregation level')
    dims = dimensions[level]
    clauses = filters(ctx, {}, period=False) + [Sale.day <= cutoff.isoformat()]
    query = select(*dims, Sale.day, func.sum(Sale.quantity)).where(*clauses).group_by(*dims,Sale.day).order_by(*dims,Sale.day)
    result = {}
    with database.session() as session:
        for row in session.execute(query):
            key = tuple(row[:-2]) or ('chain',)
            days, values = result.setdefault(key, ([],[]))
            days.append(date.fromisoformat(row[-2])); values.append(row[-1])
    return result

"""Scoped observation coverage; absence is not a zero-sales measurement."""
from datetime import date, timedelta
from sqlalchemy import func, select
from app.api.schemas import Role
from app.enterprise.data import Sale
from app.enterprise.retail import filters


def observation_coverage(database, ctx):
    clauses = filters(ctx, {})
    with database.session() as session:
        latest = session.scalar(select(func.max(Sale.day)).where(*clauses))
        if latest is None:
            return {'status': 'no_observations', 'start': None, 'end': None, 'stores': []}
        end = date.fromisoformat(latest)
        start = end - timedelta(days=27)
        stores = (list(session.scalars(select(Sale.store_id).where(*clauses).distinct()))
                  if ctx.role == Role.ADMIN else list(ctx.store_ids))
        rows = session.execute(select(Sale.store_id, Sale.day, func.sum(Sale.quantity))
            .where(*clauses, Sale.day >= start.isoformat(), Sale.day <= latest)
            .group_by(Sale.store_id, Sale.day)).all()
    observed = {(store, day): units for store, day, units in rows}
    dates = [(start + timedelta(days=i)).isoformat() for i in range(28)]
    result = []
    for store in sorted(set(stores)):
        values = [observed.get((store, day)) for day in dates]
        count = sum(value is not None for value in values)
        result.append({'store_id': store, 'observed_days': count, 'unknown_days': 28-count,
                       'dates': dates, 'units': values})
    return {'status': 'observed_snapshot', 'start': start.isoformat(), 'end': latest,
        'stores': result,
        'limitation': 'Dates without recorded transactions are unknown, not zero sales or confirmed closure. '
                      'Coverage does not establish complete imports or inventory availability. '
                      'The window ends at the latest authorized recorded sale, not the current date.'}

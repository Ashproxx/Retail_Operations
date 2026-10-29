"""Seeded resampling of supplied transaction rows, never represented as real sales."""
from datetime import timedelta, date
from copy import deepcopy
import random
from zoneinfo import ZoneInfo
from app.realtime.stream.ingest import Event


def events(rows: list[dict], *, seed: int, start, count: int, step_seconds: float=1):
    if not rows or count<0 or start.tzinfo is None or step_seconds<=0:
        raise ValueError('Provide source rows and a timezone-aware start')
    rng=random.Random(seed)
    for i in range(count):
        row=deepcopy(rng.choice(rows));stamp=(start+timedelta(seconds=i*step_seconds)).astimezone(ZoneInfo('Asia/Kolkata'))
        if not {'sale_date','promised_delivery_date','actual_delivery_date'} <= row.keys():
            raise ValueError('Simulator requires complete imported transaction payloads')
        shift=stamp.date()-date.fromisoformat(str(row['sale_date'])[:10])
        for field in ('promised_delivery_date','actual_delivery_date'):
            if row[field] is not None:row[field]=(date.fromisoformat(str(row[field])[:10])+shift).isoformat()
        row.update(txn_id=f'sim-{seed}-{int(start.timestamp())}-{i}',order_id=f'sim-order-{seed}-{int(start.timestamp())}-{i}',
                   sale_date=stamp.date().isoformat(),sale_time=stamp.time().replace(microsecond=0).isoformat(),day_of_week=stamp.strftime('%A'))
        yield Event(payload=row,synthetic=True)

from datetime import timedelta


def online(rows,now):
    def units(start,end):
        selected=[r for r in rows if start<=r['occurred_at']<=end and r['received_at']<=now]
        return sum(r['quantity'] for r in selected) if selected else None
    return {'units_15min':units(now-timedelta(minutes=15),now),
            'units_1hour':units(now-timedelta(hours=1),now),
            'units_same_hour_last_week':units(now-timedelta(days=7,hours=1),now-timedelta(days=7)),
            'warning':'No events is unknown coverage, not zero sales; event source labels must be retained.'}

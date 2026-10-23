from datetime import datetime


def freshness(latest: datetime | None, now: datetime):
    if latest is None:return {'status':'unavailable','age_hours':None}
    age=(now-latest).total_seconds()/3600
    return {'status':'invalid' if age<0 else 'green' if age<2 else 'amber' if age<6 else 'red','age_hours':age}

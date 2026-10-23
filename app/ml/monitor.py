"""Pure monitoring summaries; no automatic retraining or model promotion."""
from datetime import datetime
from statistics import mean, pstdev


def freshness(latest: datetime | None, now: datetime) -> dict:
    if now.tzinfo is None or latest is not None and latest.tzinfo is None:
        raise ValueError('Timezone-aware timestamps required')
    if latest is None:
        return {'status':'unavailable','age_hours':None}
    hours=(now-latest).total_seconds()/3600
    if hours<0:
        return {'status':'invalid_future_timestamp','age_hours':hours}
    return {'status':'green' if hours<2 else 'amber' if hours<6 else 'red','age_hours':hours}


def drift(reference: list[float], current: list[float]) -> dict:
    if len(reference)<28 or len(current)<7:
        return {'status':'insufficient_data','retraining_review':False}
    change=abs(mean(current)-mean(reference)); scale=pstdev(reference)
    warning=change>3*scale if scale else change>0
    return {'status':'review' if warning else 'stable','mean_shift':change,'reference_std':scale,
            'retraining_review':warning,'method':'heuristic mean shift; not a calibrated drift test'}


def error_monitor(actual: list[float], predicted: list[float], baseline_mae: float) -> dict:
    if len(actual)<7 or len(actual)!=len(predicted) or baseline_mae<0:
        return {'status':'insufficient_data','retraining_review':False}
    mae=mean(abs(a-p) for a,p in zip(actual,predicted))
    return {'mae':mae,'retraining_review':mae>1.2*baseline_mae,'method':'review after seven labels and >20% MAE increase; no automatic training'}

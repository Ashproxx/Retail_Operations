"""Finite-sample split-conformal bands from separate out-of-sample residuals."""
from math import ceil, isfinite


def conformal_radius(residuals: list[float], coverage: float) -> float:
    if not 0 < coverage < 1 or not residuals or any(not isfinite(r) for r in residuals):
        raise ValueError('Require finite calibration residuals and coverage between zero and one')
    rank=ceil((len(residuals)+1)*coverage)
    if rank>len(residuals):
        raise ValueError('Insufficient calibration residuals for a finite interval at this coverage')
    return sorted(abs(r) for r in residuals)[rank-1]


def intervals(predicted: list[float], residuals: list[float], coverage: float) -> list[dict]:
    if not predicted or any(not isfinite(p) or p<0 for p in predicted):
        raise ValueError('Observed-sales predictions must be finite and nonnegative')
    radius=conformal_radius(residuals,coverage)
    return [{'prediction':p,'lower':max(0,p-radius),'upper':p+radius,'nominal_coverage':coverage} for p in predicted]


def interval_metrics(actual: list[float], bands: list[dict]) -> dict:
    if not actual or len(actual)!=len(bands) or any(not isfinite(a) or a<0 for a in actual):
        raise ValueError('Require aligned finite nonnegative observations')
    if any(not isfinite(b['lower']) or not isfinite(b['upper']) or b['lower']>b['upper'] for b in bands):
        raise ValueError('Malformed interval')
    return {'coverage':sum(b['lower']<=a<=b['upper'] for a,b in zip(actual,bands))/len(actual),
            'mean_width':sum(b['upper']-b['lower'] for b in bands)/len(bands),'n':len(actual)}


def pinball(actual: list[float], predicted: list[float], quantile: float) -> float:
    if not actual or len(actual)!=len(predicted) or not 0<quantile<1 or any(not isfinite(x) for x in actual+predicted):
        raise ValueError('Invalid quantile evaluation inputs')
    return sum(max(quantile*(a-p),(quantile-1)*(a-p)) for a,p in zip(actual,predicted))/len(actual)

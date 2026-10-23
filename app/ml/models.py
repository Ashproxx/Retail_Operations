"""Baseline adapters reuse existing numerics; fitted ML adapters belong to M17."""
from datetime import date
from typing import Protocol
from app.conversation.forecast import ApparelRetailForecastProfile, predict
from app.ml.features import validate_series


class Forecaster(Protocol):
    name: str
    def fit(self, days: list[date], values: list[float]) -> 'Forecaster': ...
    def predict(self, targets: list[date]) -> list[float]: ...
    def predict_quantiles(self, targets: list[date], quantiles: list[float]) -> dict: ...


class Baseline:
    def __init__(self, name: str):
        if name not in ApparelRetailForecastProfile().candidates(730):
            raise ValueError('Unknown baseline')
        self.name = name
        self.days: list[date] = []
        self.values: list[float] = []

    def fit(self, days: list[date], values: list[float]) -> 'Baseline':
        validate_series(days, values, contiguous=True)
        if self.name not in ApparelRetailForecastProfile().candidates(len(days)):
            raise ValueError('Insufficient training history for this baseline')
        self.days, self.values = list(days), list(values)
        return self

    def predict(self, targets: list[date]) -> list[float]:
        if not self.days or any(t <= self.days[-1] for t in targets):
            raise ValueError('Fit first and predict strictly after training end')
        return [predict(self.name,self.days,self.values,t) for t in targets]

    def predict_quantiles(self, targets: list[date], quantiles: list[float]) -> dict:
        raise NotImplementedError('Baseline has no calibrated quantiles; use the M17 calibration adapter')

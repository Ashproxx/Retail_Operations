"""Sparse-demand baselines require observed zeros, never absent transaction dates."""
from datetime import date
from app.ml.features import validate_series


class Intermittent:
    def __init__(self, name: str='sba', alpha: float=.1):
        if name not in ('croston','sba','tsb','gamma_poisson') or not 0<alpha<=1:
            raise ValueError('Invalid intermittent model or smoothing parameter')
        self.name=name;self.alpha=alpha;self.cutoff=None;self.level=None;self.posterior=None

    def fit(self, days: list[date], values: list[float]):
        validate_series(days,values,contiguous=True)
        if any(int(v)!=v for v in values):
            raise ValueError('These count-demand models require integer observed units')
        self.cutoff=days[-1];a=self.alpha
        if self.name=='gamma_poisson':
            # Gamma(shape=1, rate=1) prior; Poisson observation exposure is one observed day.
            self.posterior={'shape':1+sum(values),'rate':1+len(values)}
            self.level=self.posterior['shape']/self.posterior['rate'];return self
        first=next((i for i,v in enumerate(values) if v>0),None)
        if first is None:self.level=0.;return self
        size=float(values[first]);gap=float(first+1);probability=1/gap;elapsed=1
        for value in values[first+1:]:
            if self.name=='tsb':probability+=a*((1 if value>0 else 0)-probability)
            if value>0:
                size+=a*(value-size)
                gap+=a*(elapsed-gap)
                elapsed=1
            else:elapsed+=1
        self.level=size*probability if self.name=='tsb' else size/gap*(1-a/2 if self.name=='sba' else 1)
        return self

    def predict(self, targets: list[date]) -> list[float]:
        if self.cutoff is None or any(t<=self.cutoff for t in targets):
            raise ValueError('Fit first and predict only future dates')
        return [self.level for _ in targets]

    def predict_quantiles(self, targets: list[date], quantiles: list[float]) -> dict:
        raise NotImplementedError('Use separately calibrated intervals; no invented quantiles')

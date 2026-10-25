"""One shared boosting estimator over explicitly supplied observed series."""
from datetime import timedelta
from math import isfinite

from app.ml.features import validate_series
from app.ml.forecasting import features


class PooledBoosting:
    def fit(self, series):
        from sklearn.ensemble import HistGradientBoostingRegressor
        if len(series) < 2:
            raise ValueError('At least two observed series required for pooling')
        self.keys = sorted(series)
        self.history = {}
        origins, x, y = set(), [], []
        for key in self.keys:
            days, values = series[key]
            validate_series(days, values, contiguous=True)
            if len(days) != 56:
                raise ValueError('Exactly 56 observed training days per series required')
            origins.add(days[-1])
            history = dict(zip(days, values))
            self.history[key] = history
            for day in days[28:]:
                x.append(features(history, day) + [int(key == other) for other in self.keys])
                y.append(history[day])
        if len(origins) != 1 or sum(y) <= 0:
            raise ValueError('Common origin and positive pooled target sum required')
        self.origin = origins.pop()
        self.model = HistGradientBoostingRegressor(loss='poisson', max_iter=100,
            max_leaf_nodes=15, min_samples_leaf=10, early_stopping=False, random_state=42).fit(x, y)
        return self

    def predict(self, key, targets):
        if not hasattr(self, 'model') or key not in self.history or not targets:
            raise ValueError('Fit first and select a known series with future targets')
        if min(targets) <= self.origin or (max(targets)-self.origin).days > 120:
            raise ValueError('Future targets within 120 days required')
        history = dict(self.history[key])
        identity = [int(key == other) for other in self.keys]
        for lead in range(1, (max(targets)-self.origin).days+1):
            day = self.origin + timedelta(days=lead)
            value = max(0., float(self.model.predict([features(history, day)+identity])[0]))
            if not isfinite(value):
                raise ValueError('Nonfinite pooled forecast; retain baseline')
            history[day] = value
        return [history[day] for day in targets]

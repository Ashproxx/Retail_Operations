"""Optional statistical and tabular adapters with strictly past-only recursive features."""
from datetime import timedelta
from math import sin, cos, pi, isfinite
from statistics import mean, pstdev
import warnings
from app.ml.features import validate_series

FEATURES=['weekday_sin','weekday_cos','month_sin','month_cos','lag_1','lag_7','lag_14','lag_28','mean_7','mean_28','std_7']


def calendar(day):
    return [sin(2*pi*day.weekday()/7),cos(2*pi*day.weekday()/7),sin(2*pi*day.month/12),cos(2*pi*day.month/12)]


def features(history,day):
    recent=[history[day-timedelta(days=i)] for i in range(1,29)]
    return calendar(day)+[recent[i-1] for i in (1,7,14,28)]+[mean(recent[:7]),mean(recent),pstdev(recent[:7])]


class ForecastModel:
    def __init__(self,name,*,seed=42,quantile=None):
        if name not in ('ets','sarima','sarimax_calendar','ridge','lasso','hist_gradient','hist_quantile','random_forest','extra_trees'):
            raise ValueError('Unknown forecasting family')
        if name=='hist_quantile' and (quantile is None or not 0<quantile<1):
            raise ValueError('Quantile model needs a probability between zero and one')
        self.name=name;self.seed=seed;self.quantile=quantile;self.model=None;self.fit_warnings=[]

    def fit(self,days,values):
        validate_series(days,values,contiguous=True)
        if len(days)<56:raise ValueError('Require 56 contiguous observed training days')
        self.days=list(days);self.values=list(values);self.history=dict(zip(days,values))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            if self.name=='ets':
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                self.model=ExponentialSmoothing(values,trend='add',damped_trend=True,seasonal='add',seasonal_periods=7,initialization_method='estimated').fit(optimized=True)
            elif self.name in ('sarima','sarimax_calendar'):
                from statsmodels.tsa.statespace.sarimax import SARIMAX
                exog=[calendar(d) for d in days] if self.name=='sarimax_calendar' else None
                self.model=SARIMAX(values,exog=exog,order=(1,0,0),seasonal_order=(1,0,0,7),trend='c',enforce_stationarity=True).fit(disp=False,maxiter=100)
                if not self.model.mle_retvals.get('converged',False):
                    raise ValueError('Statistical optimizer did not converge; retain baseline fallback')
            else:
                from sklearn.pipeline import make_pipeline
                from sklearn.preprocessing import StandardScaler
                from sklearn.linear_model import Ridge,Lasso
                from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor,ExtraTreesRegressor
                if self.name=='ridge':estimator=make_pipeline(StandardScaler(),Ridge(alpha=10))
                elif self.name=='lasso':estimator=make_pipeline(StandardScaler(),Lasso(alpha=.1,max_iter=5000))
                elif self.name in ('random_forest','extra_trees'):
                    cls=RandomForestRegressor if self.name=='random_forest' else ExtraTreesRegressor
                    estimator=cls(n_estimators=100,min_samples_leaf=5,random_state=self.seed,n_jobs=1)
                else:
                    estimator=HistGradientBoostingRegressor(loss='quantile' if self.name=='hist_quantile' else 'poisson',
                        quantile=self.quantile,max_iter=100,max_leaf_nodes=15,min_samples_leaf=10,early_stopping=False,random_state=self.seed)
                if sum(values[28:])==0 and self.name=='hist_gradient':
                    raise ValueError('Poisson boosting requires positive training target sum')
                self.model=estimator.fit([features(self.history,d) for d in days[28:]],values[28:])
            self.fit_warnings=sorted({type(w.message).__name__ for w in caught})
        return self

    def predict(self,targets):
        if self.model is None or not targets or any(t<=self.days[-1] for t in targets):
            raise ValueError('Fit first and predict future dates only')
        steps=(max(targets)-self.days[-1]).days
        if steps>120:raise ValueError('Prediction lead exceeds 120 days')
        dates=[self.days[-1]+timedelta(days=i) for i in range(1,steps+1)]
        if self.name in ('ets','sarima','sarimax_calendar'):
            kwargs={'exog':[calendar(d) for d in dates]} if self.name=='sarimax_calendar' else {}
            predicted=self.model.forecast(steps,**kwargs)
            result={d:max(0,float(p)) for d,p in zip(dates,predicted)}
        else:
            history=dict(self.history);result={}
            for d in dates:
                value=max(0,float(self.model.predict([features(history,d)])[0]))
                history[d]=value;result[d]=value
        if any(not isfinite(v) for v in result.values()):raise ValueError('Nonfinite forecast')
        return [result[d] for d in targets]

    def predict_quantiles(self,targets,quantiles):
        if self.name=='hist_quantile' and quantiles==[self.quantile]:return {self.quantile:self.predict(targets)}
        raise NotImplementedError('Fit quantile adapters separately or use held-out conformal residuals')

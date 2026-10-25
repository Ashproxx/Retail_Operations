"""Seeded validation-only permutation importance for tabular predictors."""
from statistics import mean
import random


def permutation_importance(predict, rows: list[dict], actual: list[float], *, seed: int=42, repeats: int=5) -> dict:
    if not rows or len(rows)!=len(actual) or repeats<1:
        raise ValueError('Require labelled rows and positive repeats')
    def error(data):
        predicted=predict(data)
        if len(predicted)!=len(actual):
            raise ValueError('Prediction length mismatch')
        return mean(abs(a-p) for a,p in zip(actual,predicted))
    baseline=error(rows); rng=random.Random(seed); result={}
    for feature in rows[0]:
        scores=[]
        for _ in range(repeats):
            values=[row[feature] for row in rows]; rng.shuffle(values)
            changed=[{**row,feature:value} for row,value in zip(rows,values)]
            scores.append(error(changed)-baseline)
        result[feature]=mean(scores)
    return {'baseline_mae':baseline,'increase_in_mae':result,'warning':'Predictive association, not causal importance; correlated features can mask each other.'}

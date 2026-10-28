from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import math
import random
from pydantic import BaseModel, ConfigDict, Field, model_validator

TZ=ZoneInfo('Asia/Kolkata')
UTC=timezone.utc


class CalendarEvent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name: str
    start: date
    end: date
    region: str='Navi Mumbai'
    provenance: str='manually supplied demo assumption'
    categories: dict[str,float]
    lead_days: int=Field(0,ge=0,le=30)
    decay_days: int=Field(0,ge=0,le=30)

    @model_validator(mode='after')
    def valid(self):
        if self.end<self.start or any(not math.isfinite(x) or not 0.1<=x<=4 for x in self.categories.values()):
            raise ValueError('Invalid dated event')
        return self


class Config(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: str='seasonal-v1'
    scenario: str=Field('local-demo',pattern=r'^[a-z0-9-]{1,40}$')
    seed: int=42
    start_date: date|None=None
    max_stores: int=Field(4,ge=1,le=20)
    products_per_store: int=Field(6,ge=1,le=100)
    opening_units: int=Field(30,ge=1,le=10000)
    reorder_at: int=Field(12,ge=0,le=1000)
    delivery_units: int=Field(50,ge=1,le=10000)
    lead_days: int=Field(2,ge=1,le=30)
    weekday: list[float]=Field(default_factory=lambda:[.85,.9,.9,1,1.1,1.4,1.25])
    monthly: dict[str,list[float]]=Field(default_factory=dict)
    events: list[CalendarEvent]=Field(default_factory=list)
    discount_bps: int=Field(500,ge=0,le=5000)
    promotion_factor: float=Field(1,ge=.5,le=3,allow_inf_nan=False)
    annual_trend: float=Field(.02,ge=-.2,le=.2,allow_inf_nan=False)
    dispersion: float=Field(4,ge=.1,le=100,allow_inf_nan=False)
    max_multiplier: float=Field(4,ge=1,le=10,allow_inf_nan=False)
    max_slot_units: int=Field(20,ge=1,le=100)

    @model_validator(mode='after')
    def weights(self):
        for weights,n in [(self.weekday,7)]+[(v,12) for v in self.monthly.values()]:
            if len(weights)!=n or any(not math.isfinite(x) or not .1<=x<=4 for x in weights):
                raise ValueError('Weights must be bounded, positive and complete')
        return self


def load(path=None):
    return Config.model_validate_json(Path(path or Path(__file__).with_name('seasonal.json')).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def rng(config,*parts):
    return random.Random(int(digest([config.seed,config.version,config.scenario,*parts]),16))


def factors(config,day,category):
    event_factor=1.0; names=[]
    for event in config.events:
        weight=event.categories.get(category,1)
        if event.start<=day<=event.end:
            event_factor*=weight;names.append(event.name)
        elif event.start-timedelta(days=event.lead_days)<=day<event.start:
            event_factor*=1+(weight-1)*(1-(event.start-day).days/(event.lead_days+1));names.append(event.name+' lead-in')
        elif event.end<day<=event.end+timedelta(days=event.decay_days):
            event_factor*=1+(weight-1)*(1-(day-event.end).days/(event.decay_days+1));names.append(event.name+' decay')
    month=config.monthly.get(category,[1]*12)[day.month-1]
    trend=max(.8,min(1.2,1+config.annual_trend*(day-(config.start_date or day)).days/365.25))
    return {'month':month,'weekday':config.weekday[day.weekday()],'event':event_factor,
            'promotion':config.promotion_factor,'trend':trend,'events':names,
            'combined':min(config.max_multiplier,month*config.weekday[day.weekday()]*event_factor*config.promotion_factor*trend)}


def sample(config,mean,randomizer):
    # Gamma-Poisson variation; the per-slot cap bounds demo volume, not historical observations.
    rate=min(50,randomizer.gammavariate(config.dispersion,mean/config.dispersion)) if mean>0 else 0
    product=1.0; count=0; threshold=math.exp(-rate)
    while product>threshold:
        product*=randomizer.random();count+=1
    return min(config.max_slot_units,max(0,count-1))


def instant(day,hour):
    return datetime.combine(day,datetime.min.time(),TZ).replace(hour=hour).astimezone(UTC)


def next_slot(slot):
    local=slot.astimezone(TZ)
    return instant(local.date(),local.hour+1) if local.hour<19 else instant(local.date()+timedelta(days=1),10)

import asyncio
from datetime import datetime, timezone
from urllib.parse import urlsplit
import httpx
from pydantic import BaseModel, ConfigDict, Field


class Hourly(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    time: list[datetime]
    temperature_2m: list[float | None]
    precipitation: list[float | None]
    weather_code: list[int | None]


class OpenMeteo:
    def __init__(self, settings, *, transport=None):
        self.settings=settings;self.transport=transport;self.cache={};self.last_attempt={};self.last_status='not_requested'

    async def fetch(self, *, start=None, end=None, now=None):
        now=now or datetime.now(timezone.utc)
        if not self.settings.weather_enabled:
            return {'status':'disabled','rows':[]}
        url='https://archive-api.open-meteo.com/v1/archive' if start else self.settings.weather_url
        parsed=urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname not in self.settings.weather_allowed_hosts or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.query or parsed.fragment:
            raise ValueError('Weather destination is not allowed')
        params={'latitude':self.settings.weather_lat,'longitude':self.settings.weather_lon,
                'hourly':'temperature_2m,precipitation,weather_code','timezone':'UTC'}
        if start:
            if not end or end<start:
                raise ValueError('Invalid historical interval')
            params.update(start_date=start.isoformat(),end_date=end.isoformat(),models='era5')
        else:
            params.update(forecast_days=2,past_days=1)
        key=(url,str(start),str(end));previous=self.cache.get(key)
        if previous and (now-previous['fetched_at']).total_seconds()<3600:
            return {**previous,'status':'cached'}
        if key in self.last_attempt and (now-self.last_attempt[key]).total_seconds()<60:
            return {**previous,'status':'stale_fallback'} if previous else {'status':'unavailable','rows':[]}
        self.last_attempt[key]=now
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15,follow_redirects=False,transport=self.transport) as client:
                    response=await client.get(url,params=params);response.raise_for_status()
                hourly=Hourly.model_validate(response.json()['hourly'])
                size=len(hourly.time)
                if not size or size>9000 or any(len(getattr(hourly,k))!=size for k in ['temperature_2m','precipitation','weather_code']):
                    raise ValueError('Malformed weather array lengths')
                if len(set(hourly.time))!=size:
                    raise ValueError('Duplicate hourly timestamps')
                rows=[{'observed_at':stamp.replace(tzinfo=timezone.utc).isoformat(),
                       'temperature_2m':hourly.temperature_2m[i],'precipitation':hourly.precipitation[i],
                       'weather_code':hourly.weather_code[i]} for i,stamp in enumerate(hourly.time)]
                result={'status':'fresh','fetched_at':now,'rows':rows,'source':'open-meteo-era5' if start else 'open-meteo-forecast',
                        'synthetic':False,'attribution':'Weather data by Open-Meteo.com; CC BY 4.0',
                        'licence':'https://creativecommons.org/licenses/by/4.0/'}
                self.cache[key]=result;self.last_status='fresh';return result
            except (httpx.HTTPError,ValueError,KeyError):
                if attempt<2:await asyncio.sleep(.1*2**attempt)
        self.last_status='failed'
        return {**previous,'status':'stale_fallback'} if previous else {'status':'unavailable','rows':[]}

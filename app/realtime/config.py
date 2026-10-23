from typing import Literal
from pydantic import Field, SecretStr
from app.core.config import Settings


class RealtimeSettings(Settings):
    stream_mode: Literal['off','simulator','webhook'] = 'off'
    stream_speed: float = Field(default=1,ge=1,le=1000)
    stream_seed: int = 42
    stream_hmac_key: SecretStr | None = None
    weather_enabled: bool = False
    weather_url: str = 'https://api.open-meteo.com/v1/forecast'
    weather_lat: float = Field(default=19.03,ge=-90,le=90)
    weather_lon: float = Field(default=73.03,ge=-180,le=180)
    weather_allowed_hosts: list[str] = ['api.open-meteo.com','archive-api.open-meteo.com']

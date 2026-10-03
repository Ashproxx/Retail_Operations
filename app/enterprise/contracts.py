from typing import Literal
from pydantic import Field
from app.api.schemas import Contract


class WorkspaceTurn(Contract):
    session_id: str=Field(min_length=1,max_length=100)
    message: str=Field(default='',max_length=2000)
    action: Literal['select','latest','period','location','sales','inventory','forecast','competition','delivery','chart','group','reset','search','overview','profile']|None=None
    value: str|None=Field(default=None,max_length=256)

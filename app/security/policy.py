"""Deny-by-default authorization using trusted, authenticated context."""
import hashlib,hmac
from datetime import datetime,timezone
from typing import Annotated,Callable
from pydantic import Field,AwareDatetime
from app.api.schemas import Contract,RequestContext,Role
from app.core.exceptions import RetailOpsError

class AccessDenied(RetailOpsError):
    code='access_denied'
    status_code=403

class AuthenticationFailed(RetailOpsError):
    code='authentication_failed'
    status_code=401

ALL_ACTIONS=frozenset({'inventory.read','forecast.read','analytics.read','pricing.recommend','orders.read','supply.read','support.read','returns.read','audit.read'})
PERMISSIONS={
    Role.ADMIN:ALL_ACTIONS,
    Role.STORE_MANAGER:ALL_ACTIONS-{'audit.read'},
    Role.INVENTORY_MANAGER:frozenset({'inventory.read','forecast.read','supply.read'}),
    Role.PRICING_ANALYST:frozenset({'pricing.recommend','forecast.read','analytics.read'}),
    Role.SUPPORT_AGENT:frozenset({'orders.read','support.read','returns.read'}),
    Role.ANALYST:frozenset({'analytics.read','forecast.read'}),
}

class Grant(Contract):
    token_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    principal_id:str=Field(min_length=1)
    role:Role
    expires_at:AwareDatetime|None=None
    store_ids:list[Annotated[str,Field(min_length=1)]]=Field(default_factory=list)

class TokenAuthenticator:
    """Opaque random bearer tokens provisioned outside git; not password hashing."""
    def __init__(self,grants:list[Grant]):
        if len({g.token_sha256 for g in grants})!=len(grants):raise ValueError('Duplicate token grant')
        self._grants=tuple(g.model_copy(deep=True) for g in grants)

    def authenticate(self,token:str,session_id:str)->RequestContext:
        if not 32<=len(token)<=4096:raise AuthenticationFailed('Invalid authentication')
        digest=hashlib.sha256(token.encode()).hexdigest()
        for grant in self._grants:
            if hmac.compare_digest(digest,grant.token_sha256):
                if grant.expires_at is not None and datetime.now(timezone.utc)>=grant.expires_at:
                    raise AuthenticationFailed('Invalid authentication')
                return RequestContext(session_id=session_id,principal_id=grant.principal_id,
                                      role=grant.role,store_ids=grant.store_ids.copy())
        raise AuthenticationFailed('Invalid authentication')


def authorize(context:RequestContext,action:str,store_id:str|None=None)->None:
    if action not in PERMISSIONS.get(context.role,frozenset()):raise AccessDenied('Action is not permitted')
    if context.role!=Role.ADMIN and (store_id is None or store_id not in context.store_ids):
        raise AccessDenied('Resource is outside trusted scope')

class ToolRegistry:
    def __init__(self):self._tools={}
    def register(self,name:str,action:str,handler:Callable)->None:
        if not name or name in self._tools or action not in ALL_ACTIONS:raise ValueError('Invalid tool registration')
        self._tools[name]=(action,handler)
    def invoke(self,name:str,context:RequestContext,store_id:str,arguments:dict):
        if name not in self._tools:raise AccessDenied('Unknown tool')
        action,handler=self._tools[name]
        authorize(context,action,store_id)
        if {'context','store_id'}&arguments.keys():raise AccessDenied('Reserved context arguments')
        return handler(context=context,store_id=store_id,**arguments)

from pydantic import SecretStr,model_validator
from pydantic_settings import BaseSettings,SettingsConfigDict

class SecuritySettings(BaseSettings):
    model_config=SettingsConfigDict(env_prefix='RETAILOPS_SECURITY_',extra='ignore')
    integrity_key:SecretStr|None=None
    @model_validator(mode='after')
    def key_length(self):
        if self.integrity_key is not None and len(self.integrity_key.get_secret_value().encode())<32:
            raise ValueError('Integrity key must be at least 32 bytes')
        return self
    def require_key(self)->bytes:
        if self.integrity_key is None:raise ValueError('Integrity key is not configured')
        return self.integrity_key.get_secret_value().encode()

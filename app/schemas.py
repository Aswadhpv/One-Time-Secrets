from pydantic import BaseModel, Field
from typing import Optional

class SecretCreate(BaseModel):
    secret: str
    passphrase: Optional[str] = None
    ttl_seconds: Optional[int] = Field(
        default=300,
        description="Lifetime in seconds; minimum is 300 seconds (5 minutes)"
    )

class SecretResponse(BaseModel):
    secret_key: str

class GetSecretResponse(BaseModel):
    secret: str

class DeleteResponse(BaseModel):
    status: str

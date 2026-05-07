from pydantic import BaseModel
from typing import List

class Permission(BaseModel):
    role: str
    resource: str
    actions: List[str]

class AuthSchema(BaseModel):
    auth_type: str = "JWT"
    roles: List[str]
    permissions: List[Permission]
    session_expiry_hours: int = 24

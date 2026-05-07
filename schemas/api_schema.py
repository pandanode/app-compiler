from pydantic import BaseModel
from typing import List

class APIField(BaseModel):
    name: str
    type: str
    required: bool = True

class Endpoint(BaseModel):
    path: str
    method: str
    auth_required: bool
    roles_allowed: List[str]
    request_fields: List[APIField]
    response_fields: List[APIField]

class APISchema(BaseModel):
    base_url: str = "/api"
    endpoints: List[Endpoint]

from pydantic import BaseModel, Field
from typing import List

class Entity(BaseModel):
    name: str = Field(..., description="Entity name e.g. User, Product")
    fields: List[str] = Field(..., description="List of field names")

class IntentOutput(BaseModel):
    app_name: str
    description: str
    entities: List[Entity]
    roles: List[str]
    features: List[str]
    has_payments: bool
    has_auth: bool
    is_vague: bool = False
    clarification_needed: str = ""
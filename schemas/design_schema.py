from pydantic import BaseModel
from typing import List

class Relationship(BaseModel):
    from_entity: str
    to_entity: str
    type: str

class Flow(BaseModel):
    name: str
    steps: List[str]

class DesignOutput(BaseModel):
    entities: List[str]
    relationships: List[Relationship]
    user_flows: List[Flow]
    premium_features: List[str]
    public_routes: List[str]
    protected_routes: List[str]

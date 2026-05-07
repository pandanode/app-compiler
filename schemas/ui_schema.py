from pydantic import BaseModel
from typing import List, Optional

class UIComponent(BaseModel):
    type: str
    label: str
    api_endpoint: Optional[str] = None

class Page(BaseModel):
    name: str
    route: str
    auth_required: bool
    roles_allowed: List[str]
    components: List[UIComponent]

class UISchema(BaseModel):
    pages: List[Page]

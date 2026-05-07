from pydantic import BaseModel
from typing import List, Optional

class Column(BaseModel):
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None

class Table(BaseModel):
    name: str
    columns: List[Column]

class DBSchema(BaseModel):
    tables: List[Table]

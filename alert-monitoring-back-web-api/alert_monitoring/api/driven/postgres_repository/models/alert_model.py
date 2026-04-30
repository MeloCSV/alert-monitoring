from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
import uuid

class AlertDB(SQLModel, table=True):
    __tablename__ = "alerts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    source_tool: str
    severity: str
    condition: str
    environments: List[str] = Field(default=[], sa_column=Column(JSON))
    microservice: Optional[str] = None
    solution: Optional[str] = None
    notification_channel: Optional[str] = None
    confidence_level: float
from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class AlertApiDB(SQLModel, table=True):
    __tablename__ = "alert_api"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    api: str = Field(index=True)
    microservice: str
    severity: Optional[str] = Field(default=None)
    notification_channel: Optional[str] = Field(default=None)
    environments: List[str] = Field(default=[], sa_column=Column(JSON))
